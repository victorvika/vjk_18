import type { TickerRow } from '../lib/feed';
import { fmtPct, fmtPrice } from '../lib/feed';

export default function TickerTape({ rows, onSelect }: { rows: TickerRow[]; onSelect: (s: string) => void }) {
  const doubled = [...rows, ...rows];
  return (
    <div className="ticker" aria-label="Market ticker tape">
      <div className="ticker-track">
        {doubled.map((r, i) => (
          <button key={`${r.symbol}-${i}`} type="button" className="ticker-item" onClick={() => onSelect(r.symbol)}>
            <b>{r.symbol}</b>
            <span>{fmtPrice(r.last)}</span>
            <span className={r.changePct >= 0 ? 'up' : 'down'}>{fmtPct(r.changePct)}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
