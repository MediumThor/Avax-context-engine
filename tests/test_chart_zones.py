"""Validated zones are drawn as shaded ranges on the Lightweight Charts pane."""

from pathlib import Path


def test_market_chart_attaches_zone_bands():
    chart = Path("apps/web/src/components/MarketChart.tsx").read_text(encoding="utf-8")
    primitive = Path("apps/web/src/components/ChartZoneBands.ts").read_text(encoding="utf-8")
    app = Path("apps/web/src/App.tsx").read_text(encoding="utf-8")
    assert "ZoneBandPrimitive" in chart
    assert "attachPrimitive" in chart
    assert "zones={overlayZones}" in app
    assert "Does not invent future width" in primitive
    assert "rgba(255,89,100,0.22)" in primitive
    assert "autoscaleInfo" in primitive
    assert "knownUnix" in primitive
    assert "timeEnd" in primitive
    assert app.index("<h2>Thesis</h2>") < app.index("<h2>Forecast · next 10</h2>")


def test_zone_band_starts_at_known_at_not_before_series():
    primitive = Path("apps/web/src/components/ChartZoneBands.ts").read_text(encoding="utf-8")
    assert "Math.max(this.timeStart, known ?? this.timeStart)" in primitive
    assert "t1 = this.timeEnd" in primitive
