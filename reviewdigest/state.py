"""Dedup + rating-snapshot state, persisted as JSON inside the repo.

Layout of state/state.json:
{
  "version": 1,
  "last_run": "2026-07-10T12:00:00+00:00",
  "seen": {"<app_id>:<country>": ["<review_id>", ...]},      # newest first, capped
  "ratings": {"<app_id>:<country>": [{"date", "average_rating", "rating_count"}, ...]}
}
"""

from __future__ import annotations

import json
import os

SEEN_CAP = 1000  # per app:country; ~50 weeks of a very active storefront
RATING_HISTORY_CAP = 104  # two years of weekly snapshots


def key(app_id: str, country: str) -> str:
    return f"{app_id}:{country}"


def load(path: str) -> dict:
    if not os.path.exists(path):
        return {"version": 1, "last_run": None, "seen": {}, "ratings": {}}
    with open(path, encoding="utf-8") as f:
        state = json.load(f)
    state.setdefault("seen", {})
    state.setdefault("ratings", {})
    return state


def save(state: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
        f.write("\n")


def seen_ids(state: dict, app_id: str, country: str) -> set[str]:
    return set(state["seen"].get(key(app_id, country), []))


def mark_seen(state: dict, app_id: str, country: str, new_ids: list[str]) -> None:
    k = key(app_id, country)
    existing = state["seen"].get(k, [])
    state["seen"][k] = (list(new_ids) + existing)[:SEEN_CAP]


def previous_rating(state: dict, app_id: str, country: str) -> dict | None:
    history = state["ratings"].get(key(app_id, country), [])
    return history[-1] if history else None


def add_rating_snapshot(
    state: dict, app_id: str, country: str, date: str, average_rating, rating_count
) -> None:
    if average_rating is None and rating_count is None:
        return
    k = key(app_id, country)
    history = state["ratings"].setdefault(k, [])
    if history and history[-1].get("date") == date:
        history[-1] = {"date": date, "average_rating": average_rating, "rating_count": rating_count}
    else:
        history.append(
            {"date": date, "average_rating": average_rating, "rating_count": rating_count}
        )
    del history[:-RATING_HISTORY_CAP]
