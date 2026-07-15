"""Load and validate reviewdigest.yaml."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import yaml

from . import storefronts

DEFAULT_CONFIG_PATH = "reviewdigest.yaml"

SUPPORTED_PROVIDERS = ("anthropic", "openai")


@dataclass
class AppConfig:
    id: str
    name: str | None = None  # optional; resolved via iTunes lookup when missing


@dataclass
class LLMConfig:
    provider: str = "anthropic"
    model: str = "claude-opus-4-8"
    base_url: str | None = None  # OpenAI-compatible endpoint override
    max_tokens: int = 4000

    def api_key(self) -> str | None:
        generic = os.environ.get("REVIEWDIGEST_LLM_API_KEY")
        if generic:
            return generic
        if self.provider == "anthropic":
            return os.environ.get("ANTHROPIC_API_KEY")
        return os.environ.get("OPENAI_API_KEY")


@dataclass
class OutputConfig:
    type: str = "github-issue"  # github-issue | file | stdout
    path: str = "digests"  # directory for type=file
    labels: list[str] = field(default_factory=lambda: ["review-digest"])


@dataclass
class Config:
    apps: list[AppConfig]
    countries: list[str]
    language: str = "English"
    lookback_days: int = 8
    max_pages_per_storefront: int = 5
    request_delay_seconds: float = 1.0
    llm: LLMConfig = field(default_factory=LLMConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    state_path: str = "state/state.json"


class ConfigError(Exception):
    pass


def _parse_apps(raw) -> list[AppConfig]:
    if not raw:
        raise ConfigError(
            "No apps configured. Add at least one app id to `apps:` in reviewdigest.yaml.\n"
            "Find your app id in its App Store URL: https://apps.apple.com/us/app/<slug>/id<THIS NUMBER>"
        )
    apps = []
    for entry in raw:
        if isinstance(entry, dict):
            app_id = entry.get("id")
            name = entry.get("name")
        else:
            app_id, name = entry, None
        raw = app_id if app_id is not None else entry
        app_id = str(app_id).strip().lstrip("id") if app_id is not None else ""
        if not app_id.isdigit():
            raise ConfigError(
                f"App id {str(raw)!r} is not a numeric App Store id. "
                "Edit `apps:` in reviewdigest.yaml — the id is the number in your App Store URL: "
                "https://apps.apple.com/us/app/<slug>/id<NUMBER>"
            )
        apps.append(AppConfig(id=app_id, name=name))
    return apps


def load(path: str = DEFAULT_CONFIG_PATH) -> Config:
    if not os.path.exists(path):
        raise ConfigError(
            f"Config file {path!r} not found. Copy reviewdigest.yaml from the template repo root."
        )
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    apps = _parse_apps(raw.get("apps"))
    try:
        countries = storefronts.expand(raw.get("countries", ["us"]))
    except ValueError as e:
        raise ConfigError(str(e)) from e

    llm_raw = raw.get("llm") or {}
    llm = LLMConfig(
        provider=str(llm_raw.get("provider", "anthropic")).lower(),
        model=str(llm_raw.get("model", "claude-opus-4-8")),
        base_url=llm_raw.get("base_url"),
        max_tokens=int(llm_raw.get("max_tokens", 4000)),
    )
    if llm.provider not in SUPPORTED_PROVIDERS:
        raise ConfigError(
            f"Unsupported llm.provider {llm.provider!r}. Supported: {', '.join(SUPPORTED_PROVIDERS)} "
            "(openai works for any OpenAI-compatible endpoint via llm.base_url)."
        )

    out_raw = raw.get("output") or {}
    output = OutputConfig(
        type=str(out_raw.get("type", "github-issue")),
        path=str(out_raw.get("path", "digests")),
        labels=list(out_raw.get("labels", ["review-digest"])),
    )
    if output.type not in ("github-issue", "file", "stdout"):
        raise ConfigError(
            f"Unsupported output.type {output.type!r}. Supported: github-issue, file, stdout."
        )

    return Config(
        apps=apps,
        countries=countries,
        language=str(raw.get("language", "English")),
        lookback_days=int(raw.get("lookback_days", 8)),
        max_pages_per_storefront=int(raw.get("max_pages_per_storefront", 5)),
        request_delay_seconds=float(raw.get("request_delay_seconds", 1.0)),
        llm=llm,
        output=output,
        state_path=str(raw.get("state_path", "state/state.json")),
    )
