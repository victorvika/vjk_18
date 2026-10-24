import { useRef, useState } from 'react';
import sampleRaw from '../data/xauusd-sample.json';
import { inferBarSeconds, parseMarketFile, resample } from '../lib/import';
import type { ParseResult } from '../lib/import';
import type { Dataset } from '../lib/store';

type Props = {
  open: boolean;
  onClose: () => void;
  onLoaded: (dataset: Dataset) => void;
  onError: (message: string) => void;
};

export default function DataImport({ open, onClose, onLoaded, onError }: Props) {
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<ParseResult | null>(null);
  const [name, setName] = useState('XAUUSD');
  const [buckets, setBuckets] = useState(0);
  const fileRef = useRef<HTMLInputElement | null>(null);

  if (!open) return null;

  const reset = () => {
    setPreview(null);
    setBusy(false);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleFile = async (file: File) => {
    setBusy(true);
    try {
      const text = await file.text();
      const parsed = parseMarketFile(file.name, text);
      setPreview(parsed);
      setBuckets(inferBarSeconds(parsed.candles));
    } catch (err) {
      onError((err as Error).message);
      setPreview(null);
    } finally {
      setBusy(false);
    }
  };

  // The sample ships inside the bundle, so this works offline and from file://.
  const loadSample = () => {
    try {
      const parsed = parseMarketFile('xauusd-sample.json', JSON.stringify(sampleRaw));
      setPreview(parsed);
      setBuckets(inferBarSeconds(parsed.candles));
    } catch (err) {
      onError((err as Error).message);
    }
  };

  const commit = () => {
    if (!preview) return;
    const target = buckets > 0 ? resample(preview.candles, buckets) : preview.candles;
    const id = `ds_${Date.now().toString(36)}`;
    onLoaded({
      id,
      name: name.trim() || 'XAUUSD',
      symbol: 'XAUUSD',
      barSeconds: buckets,
      importedAt: Date.now(),
      candles: target,
      source: 'import',
    });
    reset();
    onClose();
  };

  const span = preview
    ? `${new Date(preview.candles[0].time * 1000).toISOString().slice(0, 10)} → ${new Date(
        preview.candles.at(-1)!.time * 1000,
      )
        .toISOString()
        .slice(0, 10)}`
    : '';

  return (
    <div className="sheet-backdrop" role="dialog" aria-modal="true" aria-label="Import price data" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <header className="sheet-head">
          <h2>Import XAUUSD data</h2>
          <button type="button" className="ghost" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </header>

        <p className="sheet-copy">
          Load your own history from MetaTrader, TradingView, Dukascopy or any CSV. Everything stays on this
          device — nothing is uploaded anywhere.
        </p>

        <label className="field">
          <span>Label</span>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="XAUUSD H1" />
        </label>

        <div className="drop">
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.txt,.json,text/csv,application/json"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void handleFile(f);
            }}
            aria-label="Choose price file"
          />
          <span>CSV or JSON · MT5, TradingView, Dukascopy exports</span>
        </div>

        <button type="button" className="ghost wide" onClick={loadSample} disabled={busy}>
          {busy ? 'Reading…' : 'Load bundled 1-hour XAUUSD sample (Oct–Dec 2025)'}
        </button>

        {preview && (
          <div className="preview">
            <dl>
              <div>
                <dt>Bars</dt>
                <dd>{preview.candles.length.toLocaleString()}</dd>
              </div>
              <div>
                <dt>Range</dt>
                <dd>{span}</dd>
              </div>
              <div>
                <dt>Bar size</dt>
                <dd>{buckets >= 3600 ? `${buckets / 3600}h` : buckets >= 60 ? `${buckets / 60}m` : `${buckets}s`}</dd>
              </div>
            </dl>
            <label className="field">
              <span>Merge into</span>
              <select value={buckets} onChange={(e) => setBuckets(Number(e.target.value))}>
                <option value={0}>Keep original</option>
                <option value={300}>5 minutes</option>
                <option value={900}>15 minutes</option>
                <option value={1800}>30 minutes</option>
                <option value={3600}>1 hour</option>
                <option value={14400}>4 hours</option>
                <option value={86400}>1 day</option>
              </select>
            </label>
            {preview.warnings.length > 0 && (
              <ul className="warnings">
                {preview.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            )}
            <button type="button" className="primary wide" onClick={commit}>
              Use this data
            </button>
          </div>
        )}

        <details className="help">
          <summary>Which columns are recognised?</summary>
          <p>
            Delimiters comma, semicolon, tab and pipe are detected automatically. Headers may be{' '}
            <code>date,time,open,high,low,close,volume</code> (any case), MetaTrader&apos;s{' '}
            <code>&lt;DATE&gt; &lt;TIME&gt; &lt;OPEN&gt; &lt;HIGH&gt; &lt;LOW&gt; &lt;CLOSE&gt; &lt;TICKVOL&gt;</code>, or
            no header at all (date,open,high,low,close,volume). Timestamps may be unix seconds/millis,
            <code>2025-10-20 04:05:00</code>, <code>2025.10.20 04:05</code> or <code>20/10/2025 04:05</code>.
          </p>
        </details>
      </div>
    </div>
  );
}
