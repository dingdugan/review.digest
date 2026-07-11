from reviewdigest import state as state_mod


def test_roundtrip(tmp_path):
    path = str(tmp_path / "state.json")
    state = state_mod.load(path)
    state_mod.mark_seen(state, "42", "us", ["a", "b"])
    state_mod.add_rating_snapshot(state, "42", "us", "2026-07-10", 4.5, 100)
    state_mod.save(state, path)

    loaded = state_mod.load(path)
    assert state_mod.seen_ids(loaded, "42", "us") == {"a", "b"}
    assert state_mod.previous_rating(loaded, "42", "us")["average_rating"] == 4.5


def test_mark_seen_prepends_and_caps():
    state = state_mod.load("/nonexistent")
    state_mod.mark_seen(state, "42", "us", [str(i) for i in range(state_mod.SEEN_CAP)])
    state_mod.mark_seen(state, "42", "us", ["new"])
    ids = state["seen"]["42:us"]
    assert ids[0] == "new"
    assert len(ids) == state_mod.SEEN_CAP


def test_snapshot_same_day_replaces():
    state = state_mod.load("/nonexistent")
    state_mod.add_rating_snapshot(state, "42", "us", "2026-07-10", 4.0, 10)
    state_mod.add_rating_snapshot(state, "42", "us", "2026-07-10", 4.2, 12)
    history = state["ratings"]["42:us"]
    assert len(history) == 1
    assert history[0]["average_rating"] == 4.2


def test_seen_isolated_per_country():
    state = state_mod.load("/nonexistent")
    state_mod.mark_seen(state, "42", "us", ["a"])
    assert state_mod.seen_ids(state, "42", "jp") == set()
