import type { TickerRow } from '../lib/feed';
import { fmtPct, fmtPrice } from '../lib/feed';

type Props = {
  rows: TickerRow[];
  active: string;
  onSelect: (symbol: string) => void;
};

function Spark({ values }: { values: number[] }) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const w = 62;
  const h = 20;
  const pts = values
    .map((v, i) => `${(i / (values.length - 1)) * w},${h - ((v - min) / span) * (h - 2) - 1}`)
    .join(' ');
  const up = values[values.length - 1] >= values[0];
  return (
    <svg className="spark" width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
      <polyline points={pts} fill="none" stroke={up ? '#26a69a' : '#ef5350'} strokeWidth="1.2" />
    </svg>
  );
}

export default function Watchlist({ rows, active, onSelect }: Props) {
  return (
    <aside className="watchlist" aria-label="Watchlist">
      <div className="watch-head">
        <span>Watchlist</span>
        <span className="muted">{rows.length} symbols</span>
      </div>
      <div className="watch-cols">
        <span>Symbol</span>
        <span>Last</span>
        <span>Chg%</span>
      </div>
      <ul className="watch-rows">
        {rows.map((r) => {
          const up = r.changePct >= 0;
          return (
            <li key={r.symbol}>
              <button
                type="button"
                className={`watch-row ${r.symbol === active ? 'active' : ''}`}
                onClick={() => onSelect(r.symbol)}
                aria-current={r.symbol === active}
              >
                <span className="watch-sym">
                  <b>{r.symbol}</b>
                  <small>{r.name}</small>
                </span>
                <span className="watch-price">
                  <b>{fmtPrice(r.last)}</b>
                  <Spark values={r.spark} />
                </span>
                <span className={`watch-chg ${up ? 'up' : 'down'}`}>{fmtPct(r.changePct)}</span>
              </button>
            </li>
          );
        })}
      </ul>
      <p className="disclaimer">
        Price data is procedurally generated for interface demonstration. Not real quotes, not investment
        advice.
      </p>
    </aside>
  );
}
