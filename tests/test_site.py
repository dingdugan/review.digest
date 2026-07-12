import json
import os

from reviewdigest import site

DIGEST_MD = """<!-- 📱 Review Digest Jul 4 – Jul 12, 2026 · MyApp · 3 new reviews -->

# 📱 Review Digest · Jul 4 – Jul 12, 2026

## MyApp

**3 new reviews** across 2 storefronts · average 2.3★

### 🚨 Negative themes
**Crashes on launch** (2, US/DE)
> "It crashes" [US]
"""


def _setup(tmp_path, with_digest=True, ratings=None):
    digests = tmp_path / "digests"
    digests.mkdir()
    if with_digest:
        (digests / "digest-2026-07-12.md").write_text(DIGEST_MD, encoding="utf-8")
    state_file = tmp_path / "state" / "state.json"
    state_file.parent.mkdir()
    state_file.write_text(json.dumps({
        "version": 1, "seen": {},
        "ratings": ratings or {},
    }), encoding="utf-8")
    return str(digests), str(state_file), str(tmp_path / "_site")


def test_build_renders_digest_pages_and_index(tmp_path):
    digests, state_path, out = _setup(tmp_path, ratings={
        "42:us": [
            {"date": "2026-07-05", "average_rating": 4.5, "rating_count": 100},
            {"date": "2026-07-12", "average_rating": 4.6, "rating_count": 110},
        ],
    })
    site.build(digests, state_path, out, site_src="/nonexistent", config_path="/nonexistent")

    index = open(os.path.join(out, "index.html"), encoding="utf-8").read()
    assert "digest-2026-07-12.html" in index
    assert "3 new reviews" in index
    assert "<polyline" in index  # trend chart rendered

    page = open(os.path.join(out, "digest-2026-07-12.html"), encoding="utf-8").read()
    assert "Crashes on launch" in page
    assert "<blockquote>" in page


def test_build_empty_state_renders_empty_message(tmp_path):
    digests, state_path, out = _setup(tmp_path, with_digest=False)
    site.build(digests, state_path, out, site_src="/nonexistent", config_path="/nonexistent")
    index = open(os.path.join(out, "index.html"), encoding="utf-8").read()
    assert "No digests yet" in index


def test_trend_svg_needs_two_points():
    assert site.render_trend_svg({"us": [
        {"date": "2026-07-12", "average_rating": 4.5, "rating_count": 10},
    ]}) == ""
    svg = site.render_trend_svg({"us": [
        {"date": "2026-07-05", "average_rating": 4.5, "rating_count": 10},
        {"date": "2026-07-12", "average_rating": 4.7, "rating_count": 12},
    ]})
    assert "<polyline" in svg and "US 4.70" in svg


def test_trend_svg_caps_series_by_rating_count():
    histories = {
        f"c{i}": [
            {"date": "2026-07-05", "average_rating": 4.0, "rating_count": i},
            {"date": "2026-07-12", "average_rating": 4.1, "rating_count": i},
        ]
        for i in range(10)
    }
    svg = site.render_trend_svg(histories)
    assert svg.count("<polyline") == site.TREND_COUNTRIES


def test_build_copies_site_assets(tmp_path):
    digests, state_path, out = _setup(tmp_path, with_digest=False)
    src = tmp_path / "sitesrc"
    src.mkdir()
    (src / "setup.html").write_text("<html>wizard</html>", encoding="utf-8")
    site.build(digests, state_path, out, site_src=str(src), config_path="/nonexistent")
    assert os.path.exists(os.path.join(out, "setup.html"))
