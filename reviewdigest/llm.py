"""Minimal LLM client — raw REST, no SDK dependencies.

Supports:
- provider: anthropic  -> POST https://api.anthropic.com/v1/messages
- provider: openai     -> POST {base_url}/chat/completions (any OpenAI-compatible endpoint)

API keys come from environment variables only (repo secrets in CI):
REVIEWDIGEST_LLM_API_KEY overrides; otherwise ANTHROPIC_API_KEY / OPENAI_API_KEY.
"""

from __future__ import annotations

import logging
import time

import requests

from .config import LLMConfig

log = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_DEFAULT_BASE = "https://api.openai.com/v1"


class LLMError(Exception):
    pass


def complete(cfg: LLMConfig, system: str, user: str) -> str:
    api_key = cfg.api_key()
    if not api_key:
        env_name = "ANTHROPIC_API_KEY" if cfg.provider == "anthropic" else "OPENAI_API_KEY"
        raise LLMError(
            f"No API key found for provider {cfg.provider!r}. "
            f"Set the {env_name} repo secret (Settings → Secrets and variables → Actions), "
            "or run with --no-llm for a raw digest without AI analysis."
        )
    if cfg.provider == "anthropic":
        return _anthropic(cfg, api_key, system, user)
    return _openai(cfg, api_key, system, user)


def _post_with_retry(url: str, headers: dict, body: dict) -> dict:
    backoff = 5.0
    last_err = ""
    for attempt in range(4):
        if attempt:
            time.sleep(backoff)
            backoff *= 2
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=300)
        except requests.RequestException as e:
            last_err = str(e)
            log.warning("LLM request error, retrying: %s", e)
            continue
        if resp.status_code == 200:
            return resp.json()
        last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
        if resp.status_code in (429, 500, 502, 503, 504, 529):
            log.warning("LLM %s, backing off %.0fs", last_err, backoff)
            continue
        break
    raise LLMError(f"LLM request to {url} failed: {last_err}")


def _anthropic(cfg: LLMConfig, api_key: str, system: str, user: str) -> str:
    data = _post_with_retry(
        ANTHROPIC_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        body={
            "model": cfg.model,
            "max_tokens": cfg.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
    )
    try:
        return "".join(
            block["text"] for block in data["content"] if block.get("type") == "text"
        ).strip()
    except (KeyError, TypeError) as e:
        raise LLMError(f"Unexpected Anthropic response shape: {str(data)[:300]}") from e


def _openai(cfg: LLMConfig, api_key: str, system: str, user: str) -> str:
    base = (cfg.base_url or OPENAI_DEFAULT_BASE).rstrip("/")
    data = _post_with_retry(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        body={
            "model": cfg.model,
            "max_tokens": cfg.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
    )
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as e:
        raise LLMError(f"Unexpected OpenAI response shape: {str(data)[:300]}") from e
