"""Build the LLM analysis for one app's new reviews.

This is where the product lives: the prompt turns a pile of multi-language
reviews into an operator-grade weekly briefing. Keep it honest — counts must
come from the data, quotes must be real, empty sections must say so.
"""

from __future__ import annotations

from .config import LLMConfig
from .fetch import Review
from . import llm

# Keep the LLM input bounded. Negative and recent reviews carry the signal;
# a week with more than this many reviews gets sampled (noted in the digest).
MAX_REVIEWS_FOR_LLM = 300

SYSTEM_PROMPT = """\
You are a seasoned App Store review analyst writing the weekly review briefing \
for an indie developer. You are direct, specific, and honest — never inflate or \
invent. The developer will act on what you write: fix bugs, reply to users, \
plan features. Write tight, information-dense markdown. No filler, no preamble.\
"""

USER_PROMPT_TEMPLATE = """\
App: {app_name}
New reviews this period: {total} (from {n_countries} storefront(s)){sampling_note}
Write the analysis in: {language}

Each review below is formatted as:
[COUNTRY ★RATING DATE] Title | Body

<reviews>
{reviews_block}
</reviews>

Write these markdown sections, in this order, using `###` headings exactly as given:

### 🚨 Negative themes
Cluster complaints from 1–3★ reviews into named themes, most damaging first. For each theme: \
**bold theme name** (count, affected storefronts) — one-line summary, then one representative \
quote as a blockquote (translated into {language} if needed, with original country tag). \
Max 5 themes. If none: "None this week."

### 🐛 Crashes & bugs
Concrete crash/bug reports: what breaks, on what device/OS/app version when mentioned. \
Bullet list with counts. If none: "None this week."

### 💡 Feature requests
Requested features/changes, grouped and counted, most requested first. If none: "None this week."

### 💬 Worth replying
Up to 5 reviews where a developer reply would matter most (recoverable angry users, \
detailed bug reporters, thoughtful suggestions). For each: quote (translated), country + rating, \
and a one-line suggested reply angle. If none: "None this week."

### 🌟 Bright spots
2–3 sentences on what users love this period, with one short quote. If overwhelmingly \
negative, say so plainly.

Rules:
- Every count must be derived from the reviews above. Never invent reviews, quotes, or numbers.
- Translate all quoted text into {language}; keep the [country] tag so origin stays visible.
- Total length under 700 words. Cut praise before cutting problems.\
"""


def _format_review(r: Review) -> str:
    title = r.title.replace("\n", " ").strip()
    text = r.text.replace("\n", " ").strip()
    if len(text) > 600:
        text = text[:600] + "…"
    return f"[{r.country.upper()} ★{r.rating} {r.date.date().isoformat()}] {title} | {text}"


def select_for_llm(reviews: list[Review]) -> tuple[list[Review], bool]:
    """Cap LLM input; keep all negatives first, then most recent of the rest."""
    if len(reviews) <= MAX_REVIEWS_FOR_LLM:
        return reviews, False
    negatives = [r for r in reviews if r.rating <= 3]
    positives = [r for r in reviews if r.rating > 3]
    negatives.sort(key=lambda r: r.date, reverse=True)
    positives.sort(key=lambda r: r.date, reverse=True)
    selected = (negatives + positives)[:MAX_REVIEWS_FOR_LLM]
    return selected, True


def analyze(
    llm_cfg: LLMConfig, app_name: str, reviews: list[Review], language: str
) -> str:
    """Return the LLM-written analysis body (markdown) for one app."""
    selected, sampled = select_for_llm(reviews)
    countries = {r.country for r in reviews}
    sampling_note = (
        f" — showing {len(selected)} (all negative reviews + most recent others)"
        if sampled
        else ""
    )
    reviews_block = "\n".join(_format_review(r) for r in selected)
    user = USER_PROMPT_TEMPLATE.format(
        app_name=app_name,
        total=len(reviews),
        n_countries=len(countries),
        sampling_note=sampling_note,
        language=language,
        reviews_block=reviews_block,
    )
    return llm.complete(llm_cfg, SYSTEM_PROMPT, user)
