from datetime import datetime, timedelta, timezone
from unittest import mock

from reviewdigest import fetch


def _item(rid: str, date: str, rating: int = 3, review: str = "body", title: str = "t"):
    return {
        "id": rid,
        "type": "user-reviews",
        "attributes": {
            "date": date,
            "rating": rating,
            "review": review,
            "title": title,
            "userName": "user",
            "isEdited": False,
        },
    }


def _page(items, next_url="/next"):
    return {"data": items, "next": next_url}


NOW = datetime(2026, 7, 10, tzinfo=timezone.utc)
SINCE = NOW - timedelta(days=8)


def test_parse_review_fields():
    r = fetch._parse_review(_item("1", "2026-07-09T10:00:00Z", rating=1), "42", "us")
    assert r.id == "1"
    assert r.rating == 1
    assert r.country == "us"
    assert r.date == datetime(2026, 7, 9, 10, tzinfo=timezone.utc)


def test_parse_review_missing_date_returns_none():
    assert fetch._parse_review({"id": "1", "attributes": {}}, "42", "us") is None


def test_fetch_stops_at_older_review():
    pages = [
        _page([_item("1", "2026-07-09T00:00:00Z"), _item("2", "2026-06-01T00:00:00Z")]),
    ]
    with mock.patch.object(fetch, "_request_json", side_effect=pages) as m:
        got = fetch.fetch_new_reviews(mock.Mock(), "42", "us", SINCE, set(), delay=0)
    assert [r.id for r in got] == ["1"]
    assert m.call_count == 1  # stopped without fetching page 2


def test_fetch_skips_seen_ids():
    pages = [_page([_item("1", "2026-07-09T00:00:00Z"), _item("2", "2026-07-08T00:00:00Z")], next_url=None)]
    with mock.patch.object(fetch, "_request_json", side_effect=pages):
        got = fetch.fetch_new_reviews(mock.Mock(), "42", "us", SINCE, {"1"}, delay=0)
    assert [r.id for r in got] == ["2"]


def test_fetch_paginates_until_max_pages():
    page = _page([_item(str(i), "2026-07-09T00:00:00Z") for i in range(20)])
    with mock.patch.object(fetch, "_request_json", return_value=page) as m:
        fetch.fetch_new_reviews(mock.Mock(), "42", "us", SINCE, set(), max_pages=3, delay=0)
    assert m.call_count == 3


def test_fetch_stops_on_empty_page():
    with mock.patch.object(fetch, "_request_json", return_value={"data": [], "next": None}) as m:
        got = fetch.fetch_new_reviews(mock.Mock(), "42", "us", SINCE, set(), delay=0)
    assert got == []
    assert m.call_count == 1
