import { TIMEFRAMES, type Timeframe } from '../lib/market';

type Props = {
  timeframe: Timeframe;
  onTimeframe: (tf: Timeframe) => void;
  overlays: Set<string>;
  onToggleOverlay: (id: string) => void;
  onOpenPalette: () => void;
};

const INDICATORS: { id: string; label: string }[] = [
  { id: 'ema20', label: 'EMA 20' },
  { id: 'ema50', label: 'EMA 50' },
  { id: 'sma200', label: 'SMA 200' },
  { id: 'vwap', label: 'VWAP' },
  { id: 'volume', label: 'Volume' },
];

export default function Toolbar({ timeframe, onTimeframe, overlays, onToggleOverlay, onOpenPalette }: Props) {
  return (
    <nav className="toolbar" aria-label="Chart toolbar">
      <div className="tf-group" role="group" aria-label="Timeframe">
        {TIMEFRAMES.map((tf) => (
          <button
            key={tf.id}
            type="button"
            className={tf.id === timeframe ? 'on' : ''}
            onClick={() => onTimeframe(tf.id)}
            aria-pressed={tf.id === timeframe}
          >
            {tf.label}
          </button>
        ))}
      </div>
      <span className="divider" />
      <div className="ind-group" role="group" aria-label="Indicators">
        {INDICATORS.map((ind) => (
          <button
            key={ind.id}
            type="button"
            className={overlays.has(ind.id) ? 'on' : ''}
            onClick={() => onToggleOverlay(ind.id)}
            aria-pressed={overlays.has(ind.id)}
          >
            {ind.label}
          </button>
        ))}
      </div>
      <span className="divider" />
      <button type="button" className="ghost" onClick={onOpenPalette}>
        Search <kbd>⌘K</kbd>
      </button>
    </nav>
  );
}
