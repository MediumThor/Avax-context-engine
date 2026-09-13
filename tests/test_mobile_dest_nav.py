"""Five dests share Market/Replay/Accuracy/Health/More URLs on phone and desktop."""

from pathlib import Path


def test_five_destinations_are_named_and_routed():
    dests = Path("apps/web/src/nav/destinations.ts").read_text(encoding="utf-8")
    nav_tsx = Path("apps/web/src/nav/DestNav.tsx").read_text(encoding="utf-8")
    css = Path("apps/web/src/styles.css").read_text(encoding="utf-8")
    app = Path("apps/web/src/App.tsx").read_text(encoding="utf-8")
    wiki = Path("wiki/Navigation-Directive.md").read_text(encoding="utf-8")
    assert "DEST_IDS = ['market', 'replay', 'accuracy', 'health', 'more']" in dests
    assert "return `/market/${route.symbol}`" in dests
    assert "return `/replay/${route.symbol}`" in dests
    assert "return '/accuracy'" in dests
    assert "return '/health'" in dests
    assert "return '/more'" in dests
    assert "aria-label=\"Primary destinations\"" in nav_tsx
    assert ".destBtn{" in css and "min-height:44px" in css
    assert "DestNav" in app
    assert "Market" in wiki and "Replay" in wiki and "Accuracy" in wiki
    assert "Health" in wiki and "More" in wiki


def test_invalid_dest_and_as_of_plus_are_canonical():
    dests = Path("apps/web/src/nav/destinations.ts").read_text(encoding="utf-8")
    assert "return { dest: 'market', symbol: DEFAULT_SYMBOL, asOf: null, panel: 'context' }" in dests
    assert "raw.replace(/\\+/g, '%2B')" in dests
    assert "encodeURIComponent(route.asOf)" in dests
