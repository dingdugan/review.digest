"""Fetch App Store reviews via the apps.apple.com first-party web API.

Endpoint (verified 2026-07-10, see docs/research-data-layer.md):
    https://apps.apple.com/api/apps/v1/catalog/{country}/apps/{id}/reviews
        ?platform=web&sort=recent&limit=20&offset=N

No auth required, but a browser User-Agent and >=1s spacing between
requests are needed to avoid 429s. The legacy iTunes customer-reviews RSS
feed is dead (returns empty feeds as of 2026-07).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)
REVIEWS_URL = "https://apps.apple.com/api/apps/v1/catalog/{country}/apps/{app_id}/reviews"
LOOKUP_URL = "https://itunes.apple.com/lookup"
PAGE_SIZE = 20  # server-side maximum; larger values return an empty list


class FetchError(Exception):
    pass


@dataclass
class Review:
    id: str
    app_id: str
    country: str
    date: datetime
    rating: int
    title: str
    text: str
    author: str
    edited: bool = False
    has_developer_response: bool = False


def _request_json(session: requests.Session, url: str, params: dict, delay: float) -> dict:
    """GET with retry/backoff on 429 and 5xx. Sleeps `delay` before each request."""
    backoff = 2.0
    last_status = None
    for attempt in range(5):
        time.sleep(delay if attempt == 0 else backoff)
        try:
            resp = session.get(url, params=params, timeout=30)
        except requests.RequestException as e:
            log.warning("request error (%s), retrying: %s", url, e)
            backoff *= 2
            continue
        last_status = resp.status_code
        if resp.status_code == 200:
            try:
                return resp.json()
            except ValueError as e:
                raise FetchError(f"Non-JSON response from {url}: {resp.text[:200]}") from e
        if resp.status_code in (429, 500, 502, 503, 504):
            log.warning("HTTP %s from %s, backing off %.0fs", resp.status_code, url, backoff)
            backoff *= 2
            continue
        raise FetchError(f"HTTP {resp.status_code} from {url}: {resp.text[:200]}")
    raise FetchError(f"Giving up on {url} after 5 attempts (last status: {last_status})")


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return session


def _parse_review(item: dict, app_id: str, country: str) -> Review | None:
    attrs = item.get("attributes") or {}
    raw_date = attrs.get("date")
    if not item.get("id") or not raw_date:
        return None
    try:
        date = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
    except ValueError:
        return None
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return Review(
        id=str(item["id"]),
        app_id=app_id,
        country=country,
        date=date,
        rating=int(attrs.get("rating") or 0),
        title=str(attrs.get("title") or "").strip(),
        text=str(attrs.get("review") or "").strip(),
        author=str(attrs.get("userName") or "").strip(),
        edited=bool(attrs.get("isEdited")),
        has_developer_response=bool(attrs.get("developerResponse")),
    )


def fetch_new_reviews(
    session: requests.Session,
    app_id: str,
    country: str,
    since: datetime,
    seen_ids: set[str],
    max_pages: int = 5,
    delay: float = 1.0,
) -> list[Review]:
    """Fetch reviews for one app in one storefront, newest first.

    Stops at the first review older than `since` (the feed is date-sorted),
    when a page comes back empty, or after `max_pages` pages.
    Reviews whose ids are in `seen_ids` are skipped.
    """
    url = REVIEWS_URL.format(country=country, app_id=app_id)
    collected: list[Review] = []
    for page in range(max_pages):
        params = {
            "platform": "web",
            "sort": "recent",
            "limit": PAGE_SIZE,
            "offset": page * PAGE_SIZE,
            "l": "en-US",
        }
        data = _request_json(session, url, params, delay)
        items = data.get("data") or []
        if not items:
            break
        hit_older = False
        for item in items:
            review = _parse_review(item, app_id, country)
            if review is None:
                continue
            if review.date < since:
                hit_older = True
                break
            if review.id in seen_ids:
                continue
            collected.append(review)
        if hit_older or not data.get("next"):
            break
    return collected


def lookup_app(session: requests.Session, app_id: str, country: str, delay: float = 1.0) -> dict | None:
    """Official iTunes lookup: current name / average rating / rating count for one storefront."""
    data = _request_json(session, LOOKUP_URL, {"id": app_id, "country": country}, delay)
    results = data.get("results") or []
    if not results:
        return None
    r = results[0]
    return {
        "name": r.get("trackName"),
        "average_rating": r.get("averageUserRating"),
        "rating_count": r.get("userRatingCount"),
        "current_version": r.get("version"),
    }
