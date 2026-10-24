import type { OrderBook as Book } from '../lib/feed';
import { fmtCompact, fmtPrice } from '../lib/feed';

export default function OrderBook({ book }: { book: Book }) {
  const maxTotal = Math.max(book.bids.at(-1)?.total ?? 1, book.asks.at(-1)?.total ?? 1);
  return (
    <section className="panel depth" aria-label="Order book (synthetic)">
      <header className="panel-head">
        <h2>Order book</h2>
        <span className="muted">synthetic</span>
      </header>
      <div className="depth-cols">
        <span>Price</span>
        <span>Size</span>
        <span>Total</span>
      </div>
      <div className="depth-side asks">
        {[...book.asks].reverse().map((lvl) => (
          <div className="depth-row" key={`a${lvl.price}`}>
            <i style={{ width: `${(lvl.total / maxTotal) * 100}%` }} />
            <span className="px down">{fmtPrice(lvl.price, book.mid)}</span>
            <span>{lvl.size}</span>
            <span className="muted">{fmtCompact(lvl.total)}</span>
          </div>
        ))}
      </div>
      <div className="depth-mid">
        <span>{fmtPrice(book.mid)}</span>
        <small>spread {book.spread.toFixed(4)}</small>
      </div>
      <div className="depth-side bids">
        {book.bids.map((lvl) => (
          <div className="depth-row" key={`b${lvl.price}`}>
            <i style={{ width: `${(lvl.total / maxTotal) * 100}%` }} />
            <span className="px up">{fmtPrice(lvl.price, book.mid)}</span>
            <span>{lvl.size}</span>
            <span className="muted">{fmtCompact(lvl.total)}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
