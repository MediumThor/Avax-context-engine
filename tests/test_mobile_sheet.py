"""Phone workspace keeps the chart visible and tabs Context/Forecast/Thesis/Journal."""

from pathlib import Path


def test_mobile_sheet_keeps_chart_and_tabs():
    css = Path("apps/web/src/styles.css").read_text(encoding="utf-8")
    app = Path("apps/web/src/App.tsx").read_text(encoding="utf-8")
    nav = Path("wiki/Navigation-Directive.md").read_text(encoding="utf-8")
    assert "@media(max-width:900px)" in css
    assert "grid-template-rows:minmax(0,1fr) auto" in css
    assert "max-height:42dvh" in css
    assert ".sheetTab{flex:1 1 0;min-height:44px;min-width:44px" in css
    assert '.rail[data-active-sheet="thesis"]>[data-sheet="thesis"]{display:block}' in css
    assert ".sheetTabs,.regimeStrip{display:none}" in css
    dests = Path("apps/web/src/nav/destinations.ts").read_text(encoding="utf-8")
    assert "role=\"tablist\"" in app
    assert "panel" in app
    assert "SHEET_PANELS = ['context', 'forecast', 'thesis', 'journal']" in dests
    assert app.count("<h2>Thesis</h2>") == 1
    assert app.index("<h2>Thesis</h2>") < app.index("<h2>Forecast · next 10</h2>")
    assert "panel=<context|forecast|thesis|journal>" in nav


def test_invalid_panel_query_falls_back_to_context():
    dests = Path("apps/web/src/nav/destinations.ts").read_text(encoding="utf-8")
    assert "export function readPanel" in dests
    assert "SHEET_PANELS as readonly string[]).includes(raw ?? '')" in dests
    assert "(raw as SheetPanel) : 'context'" in dests
