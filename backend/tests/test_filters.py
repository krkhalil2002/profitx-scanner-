from filters import DEFAULT_FILTERS, compute_metrics, passes

GOOD = {"open": 10.5, "prev_close": 10.0, "volume": 1_000_000, "avg_volume": 400_000, "float": 20_000_000}


def test_passes_when_all_filters_met():
    ok, m = passes(GOOD)
    assert ok
    assert round(m["gap_pct"], 2) == 5.0
    assert round(m["rvol"], 2) == 2.5


def test_fails_on_each_filter():
    assert not passes({**GOOD, "open": 10.3})[0]            # gap 3%
    assert not passes({**GOOD, "volume": 400_000})[0]        # low volume
    assert not passes({**GOOD, "avg_volume": 900_000})[0]    # rvol ~1.1
    assert not passes({**GOOD, "float": 80_000_000})[0]      # float too big


def test_threshold_is_exclusive():
    d = {**GOOD, "open": 10.4}  # exactly 4.0% gap
    assert not passes(d)[0]


def test_bad_data_is_skipped_not_crashed():
    assert passes({**GOOD, "prev_close": 0})[0] is False
    assert passes({**GOOD, "float": None})[0] is False
    assert passes({"symbol": "X"})[0] is False
    assert compute_metrics({**GOOD, "avg_volume": 0})["rvol"] == 0.0


def test_custom_filters_override_defaults():
    cfg = {**DEFAULT_FILTERS, "min_gap_pct": 6.0}
    assert not passes(GOOD, cfg)[0]
