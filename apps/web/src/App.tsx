import { useEffect, useState } from 'react'
import { MarketChart } from './components/MarketChart'
import { AgentKillSwitch } from './components/AgentKillSwitch'
import { fetchKillSwitch, type KillSwitchState } from './api/killSwitch'
import './styles.css'

const demo = Array.from({ length: 80 }, (_, i) => {
  const base = 7.65 - i * 0.004 + Math.sin(i / 4) * 0.03
  return { time: 1789286400 + i * 300, open: base + 0.01, high: base + 0.03, low: base - 0.03, close: base }
})
const regimes: Array<[string, string]> = [
  ['1D', 'bearish'],
  ['4H', 'bearish'],
  ['1H', 'bearish'],
  ['15m', 'transition_up'],
  ['5m', 'neutral'],
]

export default function App() {
  const [kill, setKill] = useState<KillSwitchState | null>(null)
  const [killError, setKillError] = useState<string | null>(null)

  useEffect(() => {
    fetchKillSwitch()
      .then(setKill)
      .catch((err: unknown) => setKillError(err instanceof Error ? err.message : 'kill switch unreachable'))
  }, [])

  const severed = Boolean(kill?.engaged)

  return (
    <main className={`shell ${severed ? 'severed' : ''}`}>
      <header className="topbar">
        <div>
          <span className="eyebrow">AVAX / USDT · main</span>
          <h1>Context Engine</h1>
        </div>
        <div className={`health ${severed ? 'severedHealth' : ''}`}>
          <span className="dot" />
          {severed ? 'AGENTS SEVERED · READ ONLY' : 'DATA LIVE · READ ONLY'}
        </div>
      </header>
      {severed && (
        <div className="banner" role="status">
          Recursive Learning Harness agents are severed. Market context and journaled forecasts remain; no agent may continue until reset.
        </div>
      )}
      <AgentKillSwitch state={kill} error={killError} onChange={setKill} />
      <section className="workspace">
        <div className="chartPanel">
          <div className="chartHeader">
            <strong>$7.26</strong>
            <span className="negative">−2.4%</span>
            <span>5m</span>
          </div>
          <MarketChart candles={demo} className="chart" />
        </div>
        <aside className="rail">
          <section className="card">
            <h2>Regime stack</h2>
            {regimes.map(([tf, r]) => (
              <div className="row" key={tf}>
                <span>{tf}</span>
                <b className={r}>{r}</b>
              </div>
            ))}
          </section>
          <section className="card">
            <h2>Forecast · next 10</h2>
            <p className="muted">
              {severed ? 'Harness degraded. Forecast numbers stay journaled; no new loop will run.' : 'Waiting for journaled model output.'}
            </p>
            <div className="forecastPlaceholder" />
          </section>
          <section className="card">
            <h2>Thesis ledger</h2>
            <div className="thesis bear">
              <b>Bear continuation</b>
              <p>Active until higher-timeframe reclaim.</p>
            </div>
            <div className="thesis bull">
              <b>Bull reversal</b>
              <p>Unconfirmed.</p>
            </div>
          </section>
          <section className="card">
            <h2>Agent wave</h2>
            <p className="muted">
              {severed
                ? `Severed: ${(kill?.severed_task_ids ?? []).join(', ') || 'all launched tasks'}.`
                : 'Prototype writes land on main. Use the kill switch to halt every recursive agent.'}
            </p>
          </section>
        </aside>
      </section>
    </main>
  )
}
