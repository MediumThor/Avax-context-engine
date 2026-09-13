"""Desktop workspace keeps the chart pane while the rail scrolls."""

from pathlib import Path


def test_desktop_workspace_keeps_chart_visible():
    css = Path("apps/web/src/styles.css").read_text(encoding="utf-8")
    assert "@media(min-width:901px)" in css
    assert "html,body{height:100%;overflow:hidden}" in css
    assert ".chart{flex:1 1 auto;height:auto;min-height:280px;background:#0a0d12}" in css
    assert ".rail{overflow-y:auto;min-height:0}" in css
    assert "grid-template-columns:minmax(0,1fr) 340px" in css
