import { useCallback, useEffect, useMemo, useState } from 'react';
import ChartPanel from './components/ChartPanel';
import CommandPalette, { type Command } from './components/CommandPalette';
import OrderBook from './components/OrderBook';
import StatsBar from './components/StatsBar';
import Tape from './components/Tape';
import TickerTape from './components/TickerTape';
import Toolbar from './components/Toolbar';
import Watchlist from './components/Watchlist';
import { buildOrderBook, buildTape, buildTicker, summarize } from './lib/feed';
import { INSTRUMENTS, TIMEFRAMES, generateCandles, instrumentBySymbol, type Timeframe } from './lib/market';
import { buildOverlays } from './lib/studies';

const STORAGE = 'chartdesk:v1';

type Persisted = { symbol: string; timeframe: Timeframe; overlays: string[] };

function loadState(): Persisted {
  try {
    const raw = localStorage.getItem(STORAGE);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<Persisted>;
      const symbol = INSTRUMENTS.some((i) => i.symbol === parsed.symbol) ? parsed.symbol! : 'NIFTY 50';
      const timeframe = TIMEFRAMES.some((t) => t.id === parsed.timeframe) ? parsed.timeframe! : '5m';
      const overlays = Array.isArray(parsed.overlays) ? parsed.overlays : ['ema20', 'ema50', 'volume'];
      return { symbol, timeframe, overlays };
    }
  } catch {
    /* storage can be unavailable or hold junk — fall through to defaults */
  }
  return { symbol: 'NIFTY 50', timeframe: '5m', overlays: ['ema20', 'ema50', 'volume'] };
}

export default function App() {
  const initial = useMemo(loadState, []);
  const [symbol, setSymbol] = useState(initial.symbol);
  const [timeframe, setTimeframe] = useState<Timeframe>(initial.timeframe);
  const [overlays, setOverlays] = useState<Set<string>>(() => new Set(initial.overlays));
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [seedSalt, setSeedSalt] = useState(0);

  const inst = instrumentBySymbol(symbol);
  const candles = useMemo(() => generateCandles(inst, timeframe), [inst, timeframe]);
  const studyRows = useMemo(() => buildOverlays(candles, overlays), [candles, overlays]);
  const book = useMemo(() => buildOrderBook(inst, candles.at(-1)?.close ?? inst.basePrice, 12, seedSalt), [inst, candles, seedSalt]);
  const tape = useMemo(() => buildTape(inst, candles.at(-1)?.close ?? inst.basePrice, 26, seedSalt), [inst, candles, seedSalt]);
  const summary = useMemo(() => summarize(candles), [candles]);

  const tickers = useMemo(
    () => INSTRUMENTS.map((i) => buildTicker(generateCandles(i, '15m', 120), i)),
    [],
  );

  useEffect(() => {
    const payload: Persisted = { symbol, timeframe, overlays: [...overlays] };
    try {
      localStorage.setItem(STORAGE, JSON.stringify(payload));
    } catch {
      /* private mode — state simply won't persist */
    }
  }, [symbol, timeframe, overlays]);

  // the simulator refreshes the book and tape on a slow, gentle cadence
  useEffect(() => {
    const id = window.setInterval(() => setSeedSalt((s) => s + 1), 4000);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
      if (e.key === '/' && !(e.target instanceof HTMLInputElement)) {
        e.preventDefault();
        setPaletteOpen(true);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const toggleOverlay = useCallback((id: string) => {
    setOverlays((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const commands: Command[] = useMemo(
    () => [
      ...INSTRUMENTS.map((i) => ({
        id: `sym:${i.symbol}`,
        label: `Open ${i.symbol}`,
        hint: i.name,
        run: () => setSymbol(i.symbol),
      })),
      ...TIMEFRAMES.map((tf) => ({
        id: `tf:${tf.id}`,
        label: `Timeframe ${tf.label}`,
        hint: `${tf.minutes} min bars`,
        run: () => setTimeframe(tf.id),
      })),
      ...[
        { id: 'ema20', label: 'Toggle EMA 20' },
        { id: 'ema50', label: 'Toggle EMA 50' },
        { id: 'sma200', label: 'Toggle SMA 200' },
        { id: 'vwap', label: 'Toggle VWAP' },
        { id: 'volume', label: 'Toggle volume' },
      ].map((o) => ({ id: `ind:${o.id}`, label: o.label, hint: 'indicator', run: () => toggleOverlay(o.id) })),
    ],
    [toggleOverlay],
  );

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path d="M3 17l5-6 4 3 4-7 5 4" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M3 21h18" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
            </svg>
          </span>
          <span className="brand-text">
            Chart<b>Deck</b>
          </span>
          <span className="env-pill">simulator</span>
        </div>
        <div className="top-actions">
          <button type="button" className="ghost" onClick={() => setPaletteOpen(true)} aria-label="Open command palette">
            ⌘K
          </button>
          <span className="clock-chip">{new Date().toISOString().slice(11, 19)} UTC</span>
        </div>
      </header>

      <TickerTape rows={tickers} onSelect={setSymbol} />

      <main className="layout">
        <Watchlist rows={tickers} active={symbol} onSelect={setSymbol} />
        <section className="center">
          <StatsBar inst={inst} summary={summary} />
          <Toolbar
            timeframe={timeframe}
            onTimeframe={setTimeframe}
            overlays={overlays}
            onToggleOverlay={toggleOverlay}
            onOpenPalette={() => setPaletteOpen(true)}
          />
          <ChartPanel
            candles={candles}
            overlays={studyRows}
            showVolume={overlays.has('volume')}
            symbol={symbol}
            loading={false}
          />
        </section>
        <div className="right-rail">
          <OrderBook book={book} />
          <Tape prints={tape} mid={book.mid} />
        </div>
      </main>

      <footer className="foot">
        <span>ChartDeck · original demo terminal</span>
        <span>
          Charts by <b>Lightweight Charts™</b> (Apache-2.0, TradingView) · data is procedurally generated
        </span>
      </footer>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} commands={commands} />
    </div>
  );
}
