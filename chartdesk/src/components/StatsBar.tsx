import type { Instrument } from '../lib/market';
import type { summarize } from '../lib/feed';
import { fmtCompact, fmtPct, fmtPrice } from '../lib/feed';

type Summary = NonNullable<ReturnType<typeof summarize>>;

export default function StatsBar({
  inst,
  summary,
  source,
}: {
  inst: Instrument;
  summary: Summary | null;
  source: string;
}) {
  if (!summary) return null;
  const up = summary.changePct >= 0;
  return (
    <section className="stats" aria-label="Symbol statistics">
      <div className="stat-hero">
        <div className="stat-name">
          <h1>{inst.symbol}</h1>
          <p>
            {inst.name} · {inst.exchange} · {inst.currency}
          </p>
          <span className={`source-chip ${source.startsWith('imported') ? 'live' : ''}`}>{source}</span>
        </div>
        <div className={`stat-last ${up ? 'up' : 'down'}`}>
          <b>{fmtPrice(summary.last)}</b>
          <span>
            {summary.change >= 0 ? '+' : ''}
            {fmtPrice(summary.change)} ({fmtPct(summary.changePct)})
          </span>
        </div>
      </div>
      <dl className="stat-grid">
        <div>
          <dt>Session open</dt>
          <dd>{fmtPrice(summary.open)}</dd>
        </div>
        <div>
          <dt>Session high</dt>
          <dd>{fmtPrice(summary.high)}</dd>
        </div>
        <div>
          <dt>Session low</dt>
          <dd>{fmtPrice(summary.low)}</dd>
        </div>
        <div>
          <dt>Volume</dt>
          <dd>{fmtCompact(summary.volume)}</dd>
        </div>
        <div>
          <dt>Bars</dt>
          <dd>{summary.barCount}</dd>
        </div>
        <div>
          <dt>Range</dt>
          <dd>
            {summary.high > 0 ? (((summary.high - summary.low) / summary.high) * 100).toFixed(2) : '0.00'}%
          </dd>
        </div>
      </dl>
    </section>
  );
}
