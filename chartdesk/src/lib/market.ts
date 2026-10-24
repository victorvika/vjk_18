import { gaussian, hashString, mulberry32 } from './rng';

export type Instrument = {
  symbol: string;
  name: string;
  exchange: string;
  currency: string;
  /** volatility per bar, as a fraction of price */
  volatility: number;
  /** annualised drift-ish bias used by the generator */
  trend: number;
  basePrice: number;
  /** trading session in minutes, used to build synthetic timestamps */
  session: { openMinute: number; closeMinute: number };
};

export type Candle = {
  time: number; // unix seconds (UTC)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type Timeframe = '1m' | '5m' | '15m' | '1h' | '1D';

export const TIMEFRAMES: { id: Timeframe; label: string; minutes: number }[] = [
  { id: '1m', label: '1m', minutes: 1 },
  { id: '5m', label: '5m', minutes: 5 },
  { id: '15m', label: '15m', minutes: 15 },
  { id: '1h', label: '1H', minutes: 60 },
  { id: '1D', label: '1D', minutes: 1440 },
];

export const INSTRUMENTS: Instrument[] = [
  { symbol: 'XAUUSD', name: 'Gold Spot / US Dollar', exchange: 'OANDA', currency: 'USD', volatility: 0.0016, trend: 0.00008, basePrice: 4285.4, session: { openMinute: 0, closeMinute: 1440 } },
  { symbol: 'NIFTY 50', name: 'Nifty 50 Index', exchange: 'NSE', currency: 'INR', volatility: 0.0016, trend: 0.00012, basePrice: 24187.4, session: { openMinute: 555, closeMinute: 930 } },
  { symbol: 'BANKNIFTY', name: 'Nifty Bank Index', exchange: 'NSE', currency: 'INR', volatility: 0.0024, trend: 0.00009, basePrice: 52140.75, session: { openMinute: 555, closeMinute: 930 } },
  { symbol: 'RELIANCE', name: 'Reliance Industries', exchange: 'NSE', currency: 'INR', volatility: 0.0021, trend: 0.00005, basePrice: 2934.6, session: { openMinute: 555, closeMinute: 930 } },
  { symbol: 'INFY', name: 'Infosys Ltd', exchange: 'NSE', currency: 'INR', volatility: 0.0019, trend: -0.00003, basePrice: 1782.35, session: { openMinute: 555, closeMinute: 930 } },
  { symbol: 'TCS', name: 'Tata Consultancy Services', exchange: 'NSE', currency: 'INR', volatility: 0.0017, trend: 0.00002, basePrice: 4126.9, session: { openMinute: 555, closeMinute: 930 } },
  { symbol: 'HDFCBANK', name: 'HDFC Bank Ltd', exchange: 'NSE', currency: 'INR', volatility: 0.002, trend: 0.00004, basePrice: 1690.15, session: { openMinute: 555, closeMinute: 930 } },
  { symbol: 'BTCUSDT', name: 'Bitcoin / Tether', exchange: 'BINANCE', currency: 'USDT', volatility: 0.0062, trend: 0.0002, basePrice: 67412.5, session: { openMinute: 0, closeMinute: 1440 } },
  { symbol: 'ETHUSDT', name: 'Ether / Tether', exchange: 'BINANCE', currency: 'USDT', volatility: 0.0075, trend: 0.00015, basePrice: 3287.9, session: { openMinute: 0, closeMinute: 1440 } },
  { symbol: 'EURUSD', name: 'Euro / US Dollar', exchange: 'OANDA', currency: 'USD', volatility: 0.0006, trend: -0.00001, basePrice: 1.0864, session: { openMinute: 0, closeMinute: 1440 } },
  { symbol: 'AAPL', name: 'Apple Inc', exchange: 'NASDAQ', currency: 'USD', volatility: 0.0018, trend: 0.00007, basePrice: 231.42, session: { openMinute: 810, closeMinute: 1200 } },
  { symbol: 'NVDA', name: 'NVIDIA Corp', exchange: 'NASDAQ', currency: 'USD', volatility: 0.0033, trend: 0.00018, basePrice: 138.07, session: { openMinute: 810, closeMinute: 1200 } },
];

export const instrumentBySymbol = (symbol: string): Instrument =>
  INSTRUMENTS.find((i) => i.symbol === symbol) ?? INSTRUMENTS[0];

/** Build the bar timestamps going backwards from `end`, honouring the session window. */
function sessionGrid(inst: Instrument, timeframeMinutes: number, bars: number, end: Date): number[] {
  const minutes = timeframeMinutes;
  const times: number[] = [];
  const cursor = new Date(Date.UTC(end.getUTCFullYear(), end.getUTCMonth(), end.getUTCDate()));
  let guard = 0;
  while (times.length < bars && guard++ < 20000) {
    const dayStart = Date.UTC(cursor.getUTCFullYear(), cursor.getUTCMonth(), cursor.getUTCDate());
    const day = cursor.getUTCDay();
    const isWeekend = day === 0 || day === 6;
    const open = inst.session.openMinute;
    const close = inst.session.closeMinute;
    if (!isWeekend || inst.session.closeMinute - inst.session.openMinute === 1440) {
      const slots: number[] = [];
      for (let m = open; m + minutes <= close; m += minutes) slots.push(m);
      for (let i = slots.length - 1; i >= 0; i--) {
        const t = dayStart + slots[i] * 60000;
        if (t <= end.getTime()) times.push(Math.floor(t / 1000));
      }
    }
    cursor.setUTCDate(cursor.getUTCDate() - 1);
  }
  // a day can overshoot the requested bar count; keep the most recent window
  return times.reverse().slice(-bars);
}

/**
 * Procedural OHLCV generator: a mean-reverting random walk with volatility
 * clustering and occasional impulse moves, so charts look like markets
 * without reproducing anybody's market data.
 */
export function generateCandles(inst: Instrument, timeframe: Timeframe, bars = 420, end = new Date()): Candle[] {
  const tf = TIMEFRAMES.find((t) => t.id === timeframe) ?? TIMEFRAMES[0];
  const tfScale = Math.sqrt(tf.minutes / 5);
  const rand = mulberry32(hashString(`${inst.symbol}:${timeframe}`));
  const times = sessionGrid(inst, tf.minutes, bars, end);

  const out: Candle[] = [];
  let price = inst.basePrice;
  let vol = inst.volatility * tfScale;
  let momentum = 0;

  for (let i = 0; i < times.length; i++) {
    // volatility clustering: vol drifts and mean-reverts
    vol += (inst.volatility * tfScale - vol) * 0.08 + Math.abs(gaussian(rand)) * inst.volatility * tfScale * 0.05;
    vol = Math.min(vol, inst.volatility * tfScale * 3.4);

    momentum = momentum * 0.86 + gaussian(rand) * 0.14;
    const shock = rand() < 0.035 ? gaussian(rand) * vol * 5.5 : 0;
    const drift = inst.trend * tf.minutes + momentum * vol * 0.55;
    const open = price;
    const ret = drift + gaussian(rand) * vol + shock;
    const close = Math.max(open * (1 + ret), 0.0001);
    const wick = Math.abs(gaussian(rand)) * vol * 0.9 + vol * 0.35;
    const high = Math.max(open, close) * (1 + wick * (0.4 + rand() * 0.9));
    const low = Math.min(open, close) * (1 - wick * (0.4 + rand() * 0.9));
    const range = Math.max((high - low) / close, 1e-6);
    const volume = Math.round((900 + rand() * 2600) * (1 + range * 220) * (tf.minutes >= 1440 ? 6 : 1));

    out.push({ time: times[i], open, high, low, close, volume });
    price = close;
  }
  return out;
}

export function aggregate(candles: Candle[], bucketMinutes: number, sourceMinutes: number): Candle[] {
  if (bucketMinutes === sourceMinutes) return candles;
  const factor = Math.max(1, Math.round(bucketMinutes / sourceMinutes));
  const out: Candle[] = [];
  for (let i = 0; i < candles.length; i += factor) {
    const group = candles.slice(i, i + factor);
    if (!group.length) continue;
    out.push({
      time: group[0].time,
      open: group[0].open,
      high: Math.max(...group.map((c) => c.high)),
      low: Math.min(...group.map((c) => c.low)),
      close: group[group.length - 1].close,
      volume: group.reduce((a, c) => a + c.volume, 0),
    });
  }
  return out;
}
