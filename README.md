# 📱 reviewdigest

**Your App Store reviews, read for you. Every Monday, as a GitHub Issue.**

Fork this template, fill in your app id, add your own LLM API key — and every week an AI reads your app's newest reviews across every country's App Store, clusters them into *complaint themes, crashes, feature requests, and reviews worth replying to*, translates them into your language, and delivers the briefing as a GitHub Issue.

**Zero servers. Zero database. Zero subscription.** Runs entirely on GitHub Actions in your own repo, with your own API key. Commercial tools charge ~$199/month for this; here the only cost is your LLM usage (typically a few cents to ~$1 per week).

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What a digest looks like

Real output (from a run against TikTok's public reviews, 237 new reviews across 3 storefronts):

> **237 new reviews** across 3 storefronts · average 2.5★
>
> ### 🚨 Negative themes
>
> **Unjustified bans, strikes & age restrictions** (~30, US/GB/DE) — Automated moderation banning users who claim no wrongdoing; opaque, bot-driven appeals that repeat the same reply.
> > "Automated moderation warned me for no reason (I posted the German national flag) and this led to a full account ban; my appeal was also rejected." [DE]
>
> ### 🐛 Crashes & bugs
>
> - **Black screen / logo hang on launch, then crash** (~20, US/GB/DE) — Started after a recent update. Heavily concentrated on iPhone 7 / 7 Plus and iPads on iOS 15.8 / 15.8.8 …
>
> ### 💬 Worth replying
>
> - "Black screen on launch since the update, iPhone 6s iOS 15.8.8... I need this for back to school." [US ★5] — *Acknowledge the iOS 15.8.x/older-device crash; give timeline or workaround.*

Every section is grounded in the actual reviews — counts are derived from the data, quotes are real (translated, with the origin storefront tagged), and empty sections say "None this week."

Plus a **free dashboard** on GitHub Pages — rating trends per storefront and every past digest as a web page:

![Dashboard](.github/assets/dashboard.png)

---

## Get your first digest in ~8 minutes

You need: a GitHub account, an app on the App Store (yours or anyone's), and an LLM API key.

### 1. Copy this template — 30 seconds

Click **Use this template → Create a new repository** (top right). Private is fine. You get an independent copy that you fully own — not a fork.

### 2. Fill in your app — 2 minutes

Edit `reviewdigest.yaml` in your new repo (the pencil icon on github.com works — no need to clone):

```yaml
apps:
  - id: 1234567890        # ← the number from your App Store URL:
                          #   https://apps.apple.com/us/app/<name>/id1234567890
countries: [us, gb, de, jp]   # or `major` (top 20) or `all` (~170)
language: English             # digest language — review quotes get translated into it
```

**Prefer clicking to typing?** Use the [setup wizard](https://dingdugan.github.io/review.digest/setup.html) — search your app by name, tick storefronts, copy the generated file:

![Setup wizard](.github/assets/setup-wizard.png)

### 3. Add your own API key — 2 minutes

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

- Name: `ANTHROPIC_API_KEY`, value: your key from [console.anthropic.com](https://console.anthropic.com)
- Or `OPENAI_API_KEY` with `llm.provider: openai` in the config — any OpenAI-compatible endpoint works via `llm.base_url`

The key lives encrypted in *your* repo; usage bills to *your* account. **No key? It still works** — you get the stats plus a raw review listing instead of the AI analysis.

### 4. Run it — 3 minutes of waiting

**Actions tab → Review digest → Run workflow.** A couple of minutes later your first digest appears under **Issues**, labeled `review-digest`.

### 5. (Optional) Turn on the dashboard — 30 seconds

**Settings → Pages → Source: "GitHub Actions".** From the next run on, `https://<you>.github.io/<repo>/` serves your rating-trend charts and digest archive. Skipping this is fine — the weekly Issue is unaffected.

### Done — now do nothing

Every Monday 08:00 UTC (edit the cron in [.github/workflows/digest.yml](.github/workflows/digest.yml) to taste), a new Issue arrives. Read it in 5 minutes, know what your users are angry about, what crashed, and who deserves a reply. Discuss in the Issue, link fixes, @ your team.

---

## Configuration reference

All options live in [reviewdigest.yaml](reviewdigest.yaml), documented inline. Highlights:

| Key | Default | Notes |
|---|---|---|
| `apps` | — | one or more App Store app ids; names auto-resolve |
| `countries` | `[us]` | storefront codes, `major` (top 20), or `all` (~170) |
| `language` | `English` | digest output language; quotes translated |
| `lookback_days` | `8` | window scanned per run (overlap is deduped) |
| `llm.provider` | `anthropic` | `anthropic` or `openai` (any compatible endpoint via `base_url`) |
| `llm.model` | `claude-opus-4-8` | `claude-sonnet-5` is the budget option |
| `output.type` | `github-issue` | or `file` / `stdout` |

## Run locally

```bash
pip install -r requirements.txt
python -m reviewdigest --dry-run            # full digest to stdout (needs LLM key in env)
python -m reviewdigest --dry-run --no-llm   # free: stats + raw review listing
python -m reviewdigest.site                 # build the dashboard into _site/
```

Flags: `--force` (digest even with 0 new reviews), `--config path`, `--output stdout|file|github-issue`, `-v`.

## How it works

1. **Fetch** — reviews come from Apple's first-party App Store web API (the same one apps.apple.com uses), newest-first, per storefront. No Apple credentials needed. Store ratings come from the official iTunes lookup API.
2. **Dedup** — seen review ids live in [state/](state/) and get committed back by the workflow. A review is never reported twice. No database.
3. **Analyze** — new reviews go to the LLM with a prompt tuned for operator-grade honesty: counts from the data, real quotes only, no invented numbers.
4. **Deliver** — one Issue per digest; a markdown copy lands in [digests/](digests/), which feeds the Pages dashboard. Weeks with zero new reviews are skipped.

## FAQ & caveats

**Is this official?** The review endpoint is Apple's own web API but undocumented. If Apple changes it, the fetch layer is isolated in [reviewdigest/fetch.py](reviewdigest/fetch.py) and easy to swap (App Store Connect API is the documented fallback for your own apps).

**How many reviews can it see?** Up to `max_pages_per_storefront × 20` per storefront per run (default 100). Very high-volume apps should raise it or run more often.

**Android?** iOS only for now. Google Play's API requires developer verification and a service account — PRs welcome.

**Can I watch competitors?** Yes — any public app id works. Reading what users complain about in competing apps is a feature list waiting to happen.

**Privacy?** Everything runs in your repo with your keys. Review text goes to your chosen LLM provider and nowhere else.

## Contributing

Email/Telegram/Slack outputs, Google Play, trend improvements — see [CONTRIBUTING.md](CONTRIBUTING.md). The output layer is a single function; the fetch layer is one file.

## License

[MIT](LICENSE)
