import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import {
  buildHref,
  destRoute,
  hrefNeedsCanonicalize,
  parseLocation,
  readPanel,
  readTf,
} from './destinations.ts'

const defaultMarket = {
  dest: 'market' as const,
  symbol: 'AVAXUSDT',
  asOf: null,
  panel: 'context' as const,
  tf: '5m' as const,
}

describe('parseLocation', () => {
  it('canonicalizes / to market AVAXUSDT', () => {
    assert.deepEqual(parseLocation('/', ''), defaultMarket)
  })

  it('reads /market/:symbol and panel', () => {
    const route = parseLocation('/market/AVAXUSDT', '?panel=journal')
    assert.equal(route.dest, 'market')
    assert.equal(route.symbol, 'AVAXUSDT')
    assert.equal(route.panel, 'journal')
    assert.equal(route.asOf, null)
    assert.equal(route.tf, '5m')
  })

  it('reads chart timeframe and rejects unknown tf', () => {
    assert.equal(parseLocation('/market/AVAXUSDT', '?tf=4h').tf, '4h')
    assert.equal(parseLocation('/market/AVAXUSDT', '?tf=1w').tf, '1w')
    assert.equal(readTf('nope'), '5m')
    assert.equal(parseLocation('/market/AVAXUSDT', '?tf=2h').tf, '5m')
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

  it('maps accuracy, health, more, secondary dests, and /system', () => {
    assert.equal(parseLocation('/accuracy', '').dest, 'accuracy')
    assert.equal(parseLocation('/health', '').dest, 'health')
    assert.equal(parseLocation('/more', '').dest, 'more')
    assert.equal(parseLocation('/system', '').dest, 'more')
    assert.equal(parseLocation('/benchmarks', '').dest, 'benchmarks')
    assert.equal(parseLocation('/models', '').dest, 'models')
  })

  it('falls unknown dests and symbols back to market AVAXUSDT', () => {
    assert.deepEqual(parseLocation('/not-a-dest', ''), defaultMarket)
    assert.equal(parseLocation('/market/nope!', '').symbol, 'AVAXUSDT')
  })

  it('invalid panel falls back to context', () => {
    assert.equal(readPanel('nope'), 'context')
    assert.equal(parseLocation('/market/AVAXUSDT', '?panel=zones').panel, 'context')
  })
})

describe('buildHref', () => {
  it('builds shareable dest URLs', () => {
    assert.equal(buildHref({ ...defaultMarket }), '/market/AVAXUSDT')
    assert.equal(
      buildHref({ dest: 'market', symbol: 'AVAXUSDT', asOf: null, panel: 'forecast', tf: '5m' }),
      '/market/AVAXUSDT?panel=forecast',
    )
    assert.equal(
      buildHref({ dest: 'market', symbol: 'AVAXUSDT', asOf: null, panel: 'context', tf: '4h' }),
      '/market/AVAXUSDT?tf=4h',
    )
    assert.equal(
      buildHref({
        dest: 'replay',
        symbol: 'AVAXUSDT',
        asOf: '2026-08-29T16:00:00+00:00',
        panel: 'thesis',
        tf: '15m',
      }),
      '/replay/AVAXUSDT?as_of=2026-08-29T16%3A00%3A00%2B00%3A00&panel=thesis&tf=15m',
    )
    assert.equal(
      buildHref({ dest: 'accuracy', symbol: 'AVAXUSDT', asOf: null, panel: 'context', tf: '5m' }),
      '/accuracy',
    )
    assert.equal(
      buildHref({ dest: 'benchmarks', symbol: 'AVAXUSDT', asOf: null, panel: 'context', tf: '5m' }),
      '/benchmarks',
    )
    assert.equal(
      buildHref({ dest: 'models', symbol: 'AVAXUSDT', asOf: null, panel: 'context', tf: '5m' }),
      '/models',
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
    assert.equal(hrefNeedsCanonicalize('/benchmarks', ''), null)
    assert.equal(hrefNeedsCanonicalize('/models', ''), null)
  })
})

describe('destRoute', () => {
  const current = parseLocation('/market/AVAXUSDT', '?panel=journal&tf=1h')

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
    assert.equal(next.tf, '1h')
  })

  it('secondary dests stay out of the five-item phone nav', () => {
    assert.equal(destRoute('benchmarks', current, null).dest, 'benchmarks')
    assert.equal(destRoute('models', current, null).dest, 'models')
    assert.equal(destRoute('more', current, null).dest, 'more')
  })
})
