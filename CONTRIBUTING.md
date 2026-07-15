# Contributing

Thanks for helping make review monitoring free for indie developers.

## Dev setup

```bash
git clone https://github.com/dingdugan/review.digest
cd review.digest
pip install -r requirements.txt
python -m pytest tests/ -q          # 32 tests, should be green
python -m reviewdigest --dry-run --no-llm   # smoke test against real App Store data
```

No SDKs, no build step: Python 3.11+, `requests`, `PyYAML`, `Markdown`.

## Where things live

| Area | File | Notes |
|---|---|---|
| Review fetching | `reviewdigest/fetch.py` | Apple web API client — pagination, backoff, dedup window |
| Config & validation | `reviewdigest/config.py` | everything in `reviewdigest.yaml` |
| Dedup / rating history | `reviewdigest/state.py` | JSON in `state/`, committed back by the workflow |
| LLM calls | `reviewdigest/llm.py` | raw REST, Anthropic + OpenAI-compatible |
| The analysis prompt | `reviewdigest/digest.py` | the product's taste lives here |
| Digest markdown | `reviewdigest/render.py` | stats header + sections |
| Orchestration / delivery | `reviewdigest/main.py` | CLI + GitHub Issue creation |
| Dashboard site | `reviewdigest/site.py` + `site/` | static HTML, inline SVG charts, no JS frameworks |

## Most-wanted contributions

- **New outputs**: email, Telegram, Slack — add a branch in `main.py`'s delivery step (keep zero-server: use webhooks/SMTP via secrets)
- **Google Play support**: a second fetch backend; needs the official Android Publisher API (service account)
- **Prompt improvements**: better clustering, better "worth replying" picks — test against real apps with `--dry-run`
- **More digest languages tested**: the prompt translates quotes; report issues with specific languages

## Ground rules

- Zero-server stays zero-server: no databases, no hosted components, state lives in the repo
- No SDK dependencies for LLM calls — raw REST keeps forks auditable
- Secrets only via environment variables / repo secrets, never in code or config
- Every PR: `python -m pytest tests/ -q` green, and add tests for new behavior
- Honest output is a feature: the LLM prompt must never invent counts or quotes

## Releasing (maintainers)

The repo is the product — merging to `main` ships it to every future "Use this template" click. Template hygiene matters: never commit real app configs, digests, or state to `main`.
