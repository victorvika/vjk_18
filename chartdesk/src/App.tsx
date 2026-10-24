import { useCallback, useEffect, useMemo, useState } from 'react';
import ChartPanel from './components/ChartPanel';
import CommandPalette, { type Command } from './components/CommandPalette';
import DataImport from './components/DataImport';
import OrderBook from './components/OrderBook';
import StatsBar from './components/StatsBar';
import Tape from './components/Tape';
import TickerTape from './components/TickerTape';
import Toolbar from './components/Toolbar';
import Watchlist from './components/Watchlist';
import { buildOrderBook, buildTape, buildTicker, summarize } from './lib/feed';
import { INSTRUMENTS, TIMEFRAMES, generateCandles, instrumentBySymbol, type Candle, type Timeframe } from './lib/market';
import { registerServiceWorker } from './lib/pwa';
import { resample } from './lib/import';
import { saveDataset, type Dataset } from './lib/store';
import { buildOverlays } from './lib/studies';

const STORAGE = 'chartdesk:v2';
type View = 'chart' | 'book' | 'tape' | 'list';

type Persisted = { symbol: string; timeframe: Timeframe; overlays: string[] };

function loadState(): Persisted {
  try {
    const raw = localStorage.getItem(STORAGE) ?? localStorage.getItem('chartdesk:v1');
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<Persisted>;
      const symbol = INSTRUMENTS.some((i) => i.symbol === parsed.symbol) ? parsed.symbol! : 'XAUUSD';
      const timeframe = TIMEFRAMES.some((t) => t.id === parsed.timeframe) ? parsed.timeframe! : '1h';
      const overlays = Array.isArray(parsed.overlays) ? parsed.overlays : ['ema20', 'ema50', 'volume'];
      return { symbol, timeframe, overlays };
    }
  } catch {
    /* storage can be unavailable or hold junk — fall through to defaults */
  }
  return { symbol: 'XAUUSD', timeframe: '1h', overlays: ['ema20', 'ema50', 'volume'] };
}

const TF_SECONDS: Record<Timeframe, number> = { '1m': 60, '5m': 300, '15m': 900, '1h': 3600, '1D': 86400 };

export default function App() {
  const initial = useMemo(loadState, []);
  const [symbol, setSymbol] = useState(initial.symbol);
  const [timeframe, setTimeframe] = useState<Timeframe>(initial.timeframe);
  const [overlays, setOverlays] = useState<Set<string>>(() => new Set(initial.overlays));
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [view, setView] = useState<View>('chart');

  const inst = instrumentBySymbol(symbol);

  useEffect(() => {
    registerServiceWorker();
  }, []);

  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(null), 5200);
    return () => window.clearTimeout(id);
  }, [toast]);

  const candles: Candle[] = useMemo(() => {
    if (dataset) {
      const target = TF_SECONDS[timeframe];
      return dataset.barSeconds > 0 && target > dataset.barSeconds
        ? resample(dataset.candles, target)
        : dataset.candles;
    }
    return generateCandles(inst, timeframe);
  }, [dataset, inst, timeframe]);

  const studyRows = useMemo(() => buildOverlays(candles, overlays), [candles, overlays]);
  const last = candles.at(-1)?.close ?? inst.basePrice;
  const book = useMemo(() => buildOrderBook(inst, last, 12, 0), [inst, last]);
  const tape = useMemo(() => buildTape(inst, last, 22, 0), [inst, last]);
  const summary = useMemo(() => summarize(candles), [candles]);

  const tickers = useMemo(() => INSTRUMENTS.map((i) => buildTicker(generateCandles(i, '15m', 120), i)), []);

  useEffect(() => {
    const payload: Persisted = { symbol, timeframe, overlays: [...overlays] };
    try {
      localStorage.setItem(STORAGE, JSON.stringify(payload));
    } catch {
      /* private mode — state simply won't persist */
    }
  }, [symbol, timeframe, overlays]);

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
      if (e.key === 'i' && !(e.target instanceof HTMLInputElement)) setImportOpen(true);
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

  const onDataset = useCallback(async (ds: Dataset) => {
    setDataset(ds);
    setSymbol('XAUUSD');
    try {
      await saveDataset(ds);
      setToast(`Loaded ${ds.candles.length.toLocaleString()} bars from your file.`);
    } catch {
      setToast(`Loaded ${ds.candles.length.toLocaleString()} bars (kept in memory; device storage refused the save).`);
    }
  }, []);

  const sourceLabel = dataset
    ? `imported · ${dataset.candles.length.toLocaleString()} bars`
    : 'synthetic demo data';

  const commands: Command[] = useMemo(
    () => [
      { id: 'import', label: 'Import XAUUSD data…', hint: 'CSV / JSON', run: () => setImportOpen(true) },
      ...(dataset
        ? [
            {
              id: 'clear',
              label: 'Remove imported data (back to synthetic)',
              hint: 'reset',
              run: () => {
                setDataset(null);
                setToast('Imported data cleared.');
              },
            },
          ]
        : []),
      ...TIMEFRAMES.map((tf) => ({
        id: `tf:${tf.id}`,
        label: `Timeframe ${tf.label}`,
        hint: `${tf.minutes} min bars`,
        run: () => setTimeframe(tf.id),
      })),
      ...INSTRUMENTS.map((i) => ({
        id: `sym:${i.symbol}`,
        label: `Open ${i.symbol}`,
        hint: i.name,
        run: () => setSymbol(i.symbol),
      })),
      ...[
        { id: 'ema20', label: 'Toggle EMA 20' },
        { id: 'ema50', label: 'Toggle EMA 50' },
        { id: 'sma200', label: 'Toggle SMA 200' },
        { id: 'vwap', label: 'Toggle VWAP' },
        { id: 'volume', label: 'Toggle volume' },
      ].map((o) => ({ id: `ind:${o.id}`, label: o.label, hint: 'indicator', run: () => toggleOverlay(o.id) })),
    ],
    [dataset, toggleOverlay],
  );

  return (
    <div className="app" data-view={view}>
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
          <span className={`env-pill ${dataset ? 'live' : ''}`}>{dataset ? 'your data' : 'demo'}</span>
        </div>
        <div className="top-actions">
          <button type="button" className="ghost import-btn" onClick={() => setImportOpen(true)}>
            Import
          </button>
          <button type="button" className="ghost palette-btn" onClick={() => setPaletteOpen(true)} aria-label="Open command palette">
            ⌘K
          </button>
        </div>
      </header>

      <TickerTape rows={tickers} onSelect={setSymbol} />

      <main className="layout">
        <section className="center" data-pane="chart">
          <StatsBar inst={inst} summary={summary} source={sourceLabel} />
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

        <aside className="watch-pane" data-pane="list">
          <Watchlist rows={tickers} active={symbol} onSelect={setSymbol} />
        </aside>

        <div className="right-rail">
          <div data-pane="book" className="pane-box">
            <OrderBook book={book} />
          </div>
          <div data-pane="tape" className="pane-box">
            <Tape prints={tape} mid={book.mid} />
          </div>
        </div>
      </main>

      <nav className="mobile-tabs" aria-label="Sections">
        {(
          [
            ['chart', 'Chart'],
            ['book', 'Depth'],
            ['tape', 'Tape'],
            ['list', 'Symbols'],
          ] as [View, string][]
        ).map(([id, label]) => (
          <button key={id} type="button" className={view === id ? 'on' : ''} aria-pressed={view === id} onClick={() => setView(id)}>
            {label}
          </button>
        ))}
      </nav>

      <footer className="foot">
        <span>ChartDeck · runs entirely on this device</span>
        <span>
          Charts by <b>Lightweight Charts™</b> (Apache-2.0, TradingView) ·{' '}
          {dataset ? 'your imported history' : 'procedurally generated demo data'}
        </span>
      </footer>

      {toast && (
        <div className="toast" role="status">
          {toast}
          <button type="button" onClick={() => setToast(null)} aria-label="Dismiss">
            ✕
          </button>
        </div>
      )}

      <DataImport
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onLoaded={(ds) => void onDataset(ds)}
        onError={(m) => setToast(m)}
      />
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} commands={commands} />
    </div>
  );
}
