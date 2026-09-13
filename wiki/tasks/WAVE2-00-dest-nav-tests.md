# WAVE2-00 — Dest-nav tests for TF + secondary dests

## Scope

`parseLocation` / `buildHref` gained `tf` (PR 64) and `/benchmarks` `/models` (PR 66). The dest unit file still asserted the pre-TF shape, so `npm --workspace apps/web test` failed locally. CI web only ran `web:build`, so the drift was invisible.

## Files

- `apps/web/src/nav/destinations.test.ts`
- `package.json` (`web:test`)
- `.github/workflows/ci.yml`
- `wiki/Navigation-Directive.md`

## Finish criteria

- Dest tests include `tf` and secondary dests
- CI web job runs `npm run web:test` before `web:build`
- Phone nav stays five dests
