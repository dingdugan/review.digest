from datetime import datetime, timezone
from unittest import mock

from reviewdigest import digest
from reviewdigest.config import LLMConfig
from reviewdigest.fetch import Review


def _review(rid, rating, days_offset=0, country="us", text="body"):
    return Review(
        id=rid, app_id="42", country=country,
        date=datetime(2026, 7, 1 + days_offset, tzinfo=timezone.utc),
        rating=rating, title="t", text=text, author="u",
    )


def test_analyze_prompt_contains_reviews_and_honest_counts():
    reviews = [_review("1", 1, text="it crashes"), _review("2", 5, country="jp")]
    with mock.patch.object(digest.llm, "complete", return_value="### 🚨 ...") as m:
        out = digest.analyze(LLMConfig(), "MyApp", reviews, "English")
    assert out == "### 🚨 ..."
    system, user = m.call_args[0][1], m.call_args[0][2]
    assert "MyApp" in user
    assert "New reviews this period: 2" in user
    assert "2 storefront(s)" in user
    assert "it crashes" in user
    assert "[JP ★5" in user
    assert "never inflate or" in system.lower() or "invent" in system.lower()


def test_select_for_llm_keeps_all_when_under_cap():
    reviews = [_review(str(i), 5) for i in range(10)]
    selected, sampled = digest.select_for_llm(reviews)
    assert len(selected) == 10 and not sampled


def test_select_for_llm_prioritizes_negatives_when_over_cap():
    negatives = [_review(f"n{i}", 1) for i in range(200)]
    positives = [_review(f"p{i}", 5) for i in range(200)]
    selected, sampled = digest.select_for_llm(positives + negatives)
    assert sampled
    assert len(selected) == digest.MAX_REVIEWS_FOR_LLM
    assert all(r.rating == 1 for r in selected[:200])  # every negative retained


def test_long_review_text_truncated_in_prompt():
    r = _review("1", 3, text="x" * 2000)
    line = digest._format_review(r)
    assert len(line) < 700 and line.endswith("…")
