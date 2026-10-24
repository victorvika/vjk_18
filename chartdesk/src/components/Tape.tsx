import type { TapePrint } from '../lib/feed';
import { clock, fmtPrice } from '../lib/feed';

export default function Tape({ prints, mid }: { prints: TapePrint[]; mid: number }) {
  return (
    <section className="panel tape" aria-label="Time and sales (synthetic)">
      <header className="panel-head">
        <h2>Time &amp; sales</h2>
        <span className="muted">live sim</span>
      </header>
      <div className="tape-cols">
        <span>Time</span>
        <span>Price</span>
        <span>Size</span>
      </div>
      <div className="tape-rows">
        {prints.map((p) => (
          <div className="tape-row" key={p.id}>
            <span className="muted">{clock(p.time)}</span>
            <span className={p.side === 'buy' ? 'up' : 'down'}>{fmtPrice(p.price, mid)}</span>
            <span>{p.size}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
