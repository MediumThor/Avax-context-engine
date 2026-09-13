import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import {
  buildHref,
  destRoute,
  hrefNeedsCanonicalize,
  parseLocation,
  readPanel,
} from './destinations.ts'

describe('parseLocation', () => {
  it('canonicalizes / to market AVAXUSDT', () => {
    assert.deepEqual(parseLocation('/', ''), {
      dest: 'market',
      symbol: 'AVAXUSDT',
      asOf: null,
      panel: 'context',
    })
  })

  it('reads /market/:symbol and panel', () => {
    const route = parseLocation('/market/AVAXUSDT', '?panel=journal')
    assert.equal(route.dest, 'market')
    assert.equal(route.symbol, 'AVAXUSDT')
    assert.equal(route.panel, 'journal')
    assert.equal(route.asOf, null)
  })

  it('promotes market + as_of to the replay dest', () => {
    const route = parseLocation('/market/AVAXUSDT', '?as_of=2026-08-29T16:00:00+00:00')
    assert.equal(route.dest, 'replay')
    assert.equal(route.asOf, '2026-08-29T16:00:00+00:00')
    const encoded = parseLocation('/replay/AVAXUSDT', '?as_of=2026-08-29T16%3A00%3A00%2B00%3A00')
    assert.equal(encoded.asOf, '2026-08-29T16:00:00+00:00')
  })

  it('reads /replay/:symbol', () => {
    const route = parseLocation('/replay/AVAXUSDT', '')
    assert.equal(route.dest, 'replay')
    assert.equal(route.symbol, 'AVAXUSDT')
    assert.equal(route.asOf, null)
  })

  it('maps accuracy, health, more, and /system', () => {
    assert.equal(parseLocation('/accuracy', '').dest, 'accuracy')
    assert.equal(parseLocation('/health', '').dest, 'health')
    assert.equal(parseLocation('/more', '').dest, 'more')
    assert.equal(parseLocation('/system', '').dest, 'more')
  })

  it('falls unknown dests and symbols back to market AVAXUSDT', () => {
    assert.deepEqual(parseLocation('/not-a-dest', ''), {
      dest: 'market',
      symbol: 'AVAXUSDT',
      asOf: null,
      panel: 'context',
    })
    assert.equal(parseLocation('/market/nope!', '').symbol, 'AVAXUSDT')
  })

  it('invalid panel falls back to context', () => {
    assert.equal(readPanel('nope'), 'context')
    assert.equal(parseLocation('/market/AVAXUSDT', '?panel=zones').panel, 'context')
  })
})

describe('buildHref', () => {
  it('builds shareable dest URLs', () => {
    assert.equal(
      buildHref({ dest: 'market', symbol: 'AVAXUSDT', asOf: null, panel: 'context' }),
      '/market/AVAXUSDT',
    )
    assert.equal(
      buildHref({ dest: 'market', symbol: 'AVAXUSDT', asOf: null, panel: 'forecast' }),
      '/market/AVAXUSDT?panel=forecast',
    )
    assert.equal(
      buildHref({
        dest: 'replay',
        symbol: 'AVAXUSDT',
        asOf: '2026-08-29T16:00:00+00:00',
        panel: 'thesis',
      }),
      '/replay/AVAXUSDT?as_of=2026-08-29T16%3A00%3A00%2B00%3A00&panel=thesis',
    )
    assert.equal(
      buildHref({ dest: 'accuracy', symbol: 'AVAXUSDT', asOf: null, panel: 'context' }),
      '/accuracy',
    )
  })

  it('rewrites / and market+as_of to canonical dests', () => {
    assert.equal(hrefNeedsCanonicalize('/', ''), '/market/AVAXUSDT')
    assert.equal(hrefNeedsCanonicalize('/market/AVAXUSDT', ''), null)
    assert.equal(
      hrefNeedsCanonicalize('/market/AVAXUSDT', '?as_of=2026-08-29T16:00:00+00:00'),
      '/replay/AVAXUSDT?as_of=2026-08-29T16%3A00%3A00%2B00%3A00',
    )
    assert.equal(hrefNeedsCanonicalize('/system', ''), '/more')
    assert.equal(hrefNeedsCanonicalize('/bogus', ''), '/market/AVAXUSDT')
  })
})

describe('destRoute', () => {
  const current = parseLocation('/market/AVAXUSDT', '?panel=journal')

  it('Market dest clears replay as_of', () => {
    const fromReplay = parseLocation('/replay/AVAXUSDT', '?as_of=2026-08-29T16:00:00+00:00&panel=journal')
    const next = destRoute('market', fromReplay, null)
    assert.equal(next.dest, 'market')
    assert.equal(next.asOf, null)
    assert.equal(next.panel, 'journal')
  })

  it('Replay dest uses the hint when as_of is empty', () => {
    const next = destRoute('replay', current, '2026-08-29T15:55:00+00:00')
    assert.equal(next.dest, 'replay')
    assert.equal(next.asOf, '2026-08-29T15:55:00+00:00')
  })
})
