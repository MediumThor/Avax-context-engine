# WAVE2-00 — Mobile five-destination nav

**Agent:** 00 Watcher (lane 17)
**Branch:** `cursor/mobile-dest-nav-8771`
**Status:** implemented — PR 59

## Scope

Phone bottom nav (≤900px) has **five destinations**: Market, Replay, Accuracy, Health, More. Same dest names and URLs on desktop (sidebar). Market keeps the existing Context / Forecast / Thesis / Journal sheet.

## Files

- `apps/web/src/nav/destinations.ts` — dest ids, path builders, parse
- `apps/web/src/nav/DestNav.tsx` — five dests
- `apps/web/src/views/HealthView.tsx` — `/health` + `/api/v1/system`
- `apps/web/src/views/AccuracyView.tsx` — AccuracyPanel as primary
- `apps/web/src/views/MoreView.tsx` — ops / constitution reminders
- `apps/web/src/App.tsx` — pathname + popstate
- `apps/web/src/index.css` — dest nav styles
- `apps/web/src/nav/destinations.test.ts`
- `wiki/Navigation-Directive.md`

## Assumptions

- No react-router. `history.pushState` + `popstate`.
- `/` canonicalizes to `/market/AVAXUSDT`.
- Unknown dest → market.
- Replay dest uses `replay_hint_as_of` when `?as_of=` is empty.
- Market dest clears replay (`as_of`).
- No fabricated ECE/accuracy on Health/More.

## Tests

- dest parse/build unit tests
- `npm test`, `npm run build`
- 390px + desktop browser

## Finish

Five dests work; deep links `?as_of=` / `?panel=` survive; execution stays off.
