# reviewdigest

**Weekly App Store review digests, delivered as GitHub Issues. Zero servers, zero cost*, open source.**

Every Monday, this repo fetches your app's newest App Store reviews across every storefront you care about, has an LLM cluster them into *complaint themes, crashes, feature requests, and reviews worth replying to* — translated into your language — and opens a GitHub Issue with the result.

> *\*Except LLM API usage — a typical weekly digest costs a few cents to ~$1 depending on review volume and model.*

```
📱 Review Digest · Jul 3 – Jul 10, 2026 · MyApp · 47 new reviews

## MyApp
47 new reviews across 12 storefronts · average 3.2★
5★ ███████░░░░░░░░░░░░░ 18
1★ ██████░░░░░░░░░░░░░░ 14
...

### 🚨 Negative themes
**Sync stopped working after 2.4.0** (9 reviews, US/DE/JP) — users report ...
> "Since the update my notes vanish between devices" [DE]

### 💬 Worth replying
> "I'd pay double if export worked — currently forced to screenshot" [GB ★2]
> Suggested angle: export ships in 2.5, offer beta access ...
```

Commercial tools like AppFollow or Appfigures do this for ~$199/month. If you're an indie developer, forking a repo is free.

## Get your first digest in 5 minutes

1. **Use this template** → create your own repo (private is fine).
2. **Edit `reviewdigest.yaml`** — set your app id (the number after `id` in your App Store URL) and the storefronts you want:
   ```yaml
   apps:
     - id: 1234567890
   countries: [us, gb, de, jp]   # or `major` (top 20), or `all`
   language: English             # digest language; reviews get translated into it
   ```
3. **Add your LLM key** — repo *Settings → Secrets and variables → Actions → New repository secret*:
   - `ANTHROPIC_API_KEY` (default), or `OPENAI_API_KEY` with `llm.provider: openai`
   - Any OpenAI-compatible endpoint works via `llm.base_url`
4. **Run it** — *Actions → Review digest → Run workflow*. Your first digest appears as an issue a couple of minutes later.

From then on it runs every Monday 08:00 UTC (edit the cron in [.github/workflows/digest.yml](.github/workflows/digest.yml)).

## How it works

- **Fetch** — reviews come from Apple's first-party App Store web API (the same one apps.apple.com uses), sorted newest-first, per storefront. No Apple credentials needed. Store ratings come from the official iTunes lookup API.
- **Dedup** — seen review ids are kept in [state/state.json](state/state.json) and committed back by the workflow, so a review is never reported twice. No database.
- **Analyze** — new reviews go to the LLM with a prompt tuned for operator-grade honesty: counts must come from the data, quotes must be real, empty sections say "None this week."
- **Deliver** — one GitHub Issue per digest, labeled `review-digest`. Weeks with zero new reviews are skipped.

No LLM key? It still works — you get the stats block plus a raw listing of new reviews grouped by rating (`--no-llm` mode).

## Run locally

```bash
pip install -r requirements.txt
python -m reviewdigest --dry-run            # full digest to stdout (needs LLM key in env)
python -m reviewdigest --dry-run --no-llm   # no key needed: stats + raw review listing
python -m reviewdigest --output file        # writes digests/digest-YYYY-MM-DD.md
```

Useful flags: `--force` (produce a digest even with 0 new reviews), `--config path`, `-v`.

## Configuration reference

See the comments in [reviewdigest.yaml](reviewdigest.yaml) — every option is documented there. Highlights:

| Key | Default | Notes |
|---|---|---|
| `apps` | — | one or more App Store app ids; names auto-resolve |
| `countries` | `[us]` | list of storefront codes, `major` (top 20), or `all` (~170) |
| `language` | `English` | digest output language; quotes translated |
| `lookback_days` | `8` | window scanned per run (overlap is deduped) |
| `llm.provider` | `anthropic` | `anthropic` or `openai` (any OpenAI-compatible endpoint via `base_url`) |
| `llm.model` | `claude-opus-4-8` | `claude-sonnet-5` is the budget option |
| `output.type` | `github-issue` | or `file` / `stdout` |

## Caveats

- The review endpoint is Apple's own web API but not officially documented; if Apple changes it, the fetch layer is isolated in [reviewdigest/fetch.py](reviewdigest/fetch.py) and easy to swap (App Store Connect API is the documented fallback for your own apps).
- Reviews per storefront per run are capped at `max_pages_per_storefront × 20` (default 100). Very high-volume apps should raise it or run more often.
- iOS only for now. Google Play is out of scope for V1 (its API requires developer verification and a service account).

## Contributing

Email/Telegram/Slack outputs, Google Play support, and trend charts are welcome as PRs — the output layer is a single function in [reviewdigest/main.py](reviewdigest/main.py).

## License

MIT
