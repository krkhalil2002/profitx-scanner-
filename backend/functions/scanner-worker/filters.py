"""Deterministic scan rules. Pure functions: no AWS calls, trivially testable."""

DEFAULT_FILTERS = {
    "min_gap_pct": 4.0,        # gap up of more than 4%
    "min_volume": 500_000,     # more than 500k shares traded
    "min_rvol": 2.0,           # more than 2x average volume
    "max_float": 50_000_000,   # fewer than 50M shares in the float
}


def compute_metrics(d):
    """Return {"gap_pct", "rvol"} or None if the data is unusable."""
    open_, prev, vol, avg = d.get("open"), d.get("prev_close"), d.get("volume"), d.get("avg_volume")
    if open_ is None or vol is None or not prev or prev <= 0:
        return None
    # round to avoid float noise (10.4 vs 10.0 is 4.000000000000004%, not exactly 4%)
    gap_pct = round((open_ - prev) / prev * 100, 6)
    rvol = round(vol / avg, 6) if avg and avg > 0 else 0.0
    return {"gap_pct": gap_pct, "rvol": rvol}


def passes(d, cfg=None):
    """Return (matched: bool, metrics: dict | None). A symbol must pass ALL filters."""
    cfg = cfg or DEFAULT_FILTERS
    metrics = compute_metrics(d)
    if metrics is None or d.get("float") is None:
        return False, metrics
    ok = (
        metrics["gap_pct"] > cfg["min_gap_pct"]
        and d["volume"] > cfg["min_volume"]
        and metrics["rvol"] > cfg["min_rvol"]
        and d["float"] < cfg["max_float"]
    )
    return ok, metrics
