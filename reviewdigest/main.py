"""Orchestrate a digest run: fetch → dedup → analyze → render → deliver."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

from . import digest, fetch, render, state as state_mod
from .config import Config, ConfigError, load as load_config
from .llm import LLMError

log = logging.getLogger("reviewdigest")

GITHUB_API = "https://api.github.com"
ISSUE_BODY_LIMIT = 65000  # GitHub caps issue bodies at 65536 chars


def run(cfg: Config, *, dry_run: bool, no_llm: bool, force: bool, output_override: str | None) -> int:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=cfg.lookback_days)
    session = fetch.make_session()
    state = state_mod.load(cfg.state_path)
    today_str = now.date().isoformat()

    use_llm = not no_llm and cfg.llm.api_key() is not None
    if not use_llm and not no_llm:
        log.warning("No LLM API key found — falling back to raw review listing (no AI analysis).")

    app_sections: list[str] = []
    app_names: list[str] = []
    all_new: list[fetch.Review] = []
    warnings: list[str] = []

    for app in cfg.apps:
        reviews: list[fetch.Review] = []
        store_ratings: dict[str, dict] = {}
        previous_ratings: dict[str, dict] = {}
        for country in cfg.countries:
            seen = state_mod.seen_ids(state, app.id, country)
            try:
                new = fetch.fetch_new_reviews(
                    session,
                    app.id,
                    country,
                    since,
                    seen,
                    max_pages=cfg.max_pages_per_storefront,
                    delay=cfg.request_delay_seconds,
                )
            except fetch.FetchError as e:
                log.error("fetch failed for app %s [%s]: %s", app.id, country, e)
                warnings.append(f"⚠️ Could not fetch {country.upper()} reviews for app {app.id}.")
                continue
            log.info("app %s [%s]: %d new review(s)", app.id, country, len(new))
            reviews.extend(new)

            prev = state_mod.previous_rating(state, app.id, country)
            if prev:
                previous_ratings[country] = prev
            try:
                info = fetch.lookup_app(session, app.id, country, delay=cfg.request_delay_seconds)
            except fetch.FetchError as e:
                log.warning("lookup failed for app %s [%s]: %s", app.id, country, e)
                info = None
            if info:
                store_ratings[country] = info
                state_mod.add_rating_snapshot(
                    state, app.id, country, today_str,
                    info.get("average_rating"), info.get("rating_count"),
                )
                if not app.name and info.get("name"):
                    app.name = info["name"]

        app_name = app.name or f"App {app.id}"
        app_names.append(app_name)
        all_new.extend(reviews)

        section = render.render_app_stats(app_name, reviews, store_ratings, previous_ratings)
        if reviews:
            if use_llm:
                try:
                    section += "\n" + digest.analyze(cfg.llm, app_name, reviews, cfg.language) + "\n"
                except LLMError as e:
                    log.error("LLM analysis failed for %s: %s", app_name, e)
                    warnings.append(f"⚠️ AI analysis failed for {app_name}; raw reviews listed instead.")
                    section += "\n" + render.render_raw_reviews(reviews) + "\n"
            else:
                section += "\n" + render.render_raw_reviews(reviews) + "\n"
        app_sections.append(section)

        for country in cfg.countries:
            ids = [r.id for r in reviews if r.country == country]
            if ids:
                state_mod.mark_seen(state, app.id, country, ids)

    total_new = len(all_new)
    if total_new == 0 and not force:
        log.info("No new reviews for any app — skipping digest (use --force to post anyway).")
        if not dry_run:
            state["last_run"] = now.isoformat()
            state_mod.save(state, cfg.state_path)
        return 0

    body = render.render_digest(
        since.date(), now.date(), app_sections, footer_note=" ".join(warnings)
    )
    title = render.issue_title(since.date(), now.date(), total_new, app_names)

    output_type = output_override or cfg.output.type
    if dry_run and output_type == "github-issue":
        output_type = "stdout"

    if output_type == "stdout":
        print(f"\n{'=' * 60}\n{title}\n{'=' * 60}\n")
        print(body)
    elif output_type == "file":
        os.makedirs(cfg.output.path, exist_ok=True)
        out_path = os.path.join(cfg.output.path, f"digest-{now.date().isoformat()}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"<!-- {title} -->\n\n{body}\n")
        log.info("digest written to %s", out_path)
        print(out_path)
    elif output_type == "github-issue":
        url = create_github_issue(title, body, cfg.output.labels)
        log.info("issue created: %s", url)
        print(url)

    if not dry_run:
        state["last_run"] = now.isoformat()
        state_mod.save(state, cfg.state_path)
    return 0


def create_github_issue(title: str, body: str, labels: list[str]) -> str:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        raise SystemExit(
            "output.type is github-issue but GITHUB_TOKEN / GITHUB_REPOSITORY are not set. "
            "Inside GitHub Actions these are provided automatically; locally use "
            "--dry-run or output.type: file."
        )
    if len(body) > ISSUE_BODY_LIMIT:
        body = body[:ISSUE_BODY_LIMIT] + "\n\n*…truncated (GitHub issue size limit).*"
    resp = requests.post(
        f"{GITHUB_API}/repos/{repo}/issues",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"title": title, "body": body, "labels": labels},
        timeout=30,
    )
    if resp.status_code != 201:
        raise SystemExit(f"Failed to create GitHub issue (HTTP {resp.status_code}): {resp.text[:300]}")
    return resp.json()["html_url"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reviewdigest",
        description="Weekly App Store review digests as GitHub Issues.",
    )
    parser.add_argument("--config", default="reviewdigest.yaml", help="path to config file")
    parser.add_argument("--dry-run", action="store_true",
                        help="print digest to stdout; don't save state or create issues")
    parser.add_argument("--no-llm", action="store_true",
                        help="skip AI analysis; list raw reviews instead")
    parser.add_argument("--force", action="store_true",
                        help="produce a digest even when there are no new reviews")
    parser.add_argument("--output", choices=["stdout", "file", "github-issue"],
                        help="override output.type from config")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        cfg = load_config(args.config)
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 2

    return run(
        cfg,
        dry_run=args.dry_run,
        no_llm=args.no_llm,
        force=args.force,
        output_override=args.output,
    )


if __name__ == "__main__":
    sys.exit(main())
