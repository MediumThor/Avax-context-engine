"""Desktop workspace keeps the chart pane while the rail scrolls."""

from pathlib import Path


def test_desktop_workspace_keeps_chart_visible():
    css = Path("apps/web/src/styles.css").read_text(encoding="utf-8")
    app = Path("apps/web/src/App.tsx").read_text(encoding="utf-8")
    assert "@media(min-width:901px)" in css
    assert "html,body{height:100%;overflow:hidden;overscroll-behavior:none}" in css
    assert "height:calc(100dvh - 96px)" in css
    assert "grid-template-rows:minmax(0,1fr)" in css
    assert ".workspace>.chartPanel,.workspace>.rail{min-height:0;max-height:100%}" in css
    assert ".chart{flex:1 1 auto;height:auto;min-height:280px;background:#0a0d12}" in css
    assert "overscroll-behavior:contain" in css
    assert ".rail>*{flex:0 0 auto}" in css
    assert "grid-template-columns:minmax(0,1fr) 340px" in css
    assert app.index("<h2>Thesis</h2>") < app.index("<h2>Forecast · next 10</h2>")
    assert app.count("<h2>Thesis</h2>") == 1
