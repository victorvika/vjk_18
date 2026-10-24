import type { Candle } from './market';

export type Point = { time: number; value: number };

export function sma(candles: Candle[], period: number): Point[] {
  const out: Point[] = [];
  let sum = 0;
  for (let i = 0; i < candles.length; i++) {
    sum += candles[i].close;
    if (i >= period) sum -= candles[i - period].close;
    if (i >= period - 1) out.push({ time: candles[i].time, value: sum / period });
  }
  return out;
}

export function ema(candles: Candle[], period: number): Point[] {
  const k = 2 / (period + 1);
  const out: Point[] = [];
  let prev = 0;
  for (let i = 0; i < candles.length; i++) {
    const close = candles[i].close;
    prev = i === 0 ? close : close * k + prev * (1 - k);
    if (i >= period - 1) out.push({ time: candles[i].time, value: prev });
  }
  return out;
}

/** Rolling Bollinger bands: SMA midline plus `mult` population standard deviations. */
export function bollinger(candles: Candle[], period = 20, mult = 2) {
  const mid = sma(candles, period);
  const upper: Point[] = [];
  const lower: Point[] = [];
  for (let i = period - 1; i < candles.length; i++) {
    const window = candles.slice(i - period + 1, i + 1).map((c) => c.close);
    const mean = window.reduce((a, v) => a + v, 0) / window.length;
    const variance = window.reduce((a, v) => a + (v - mean) ** 2, 0) / window.length;
    const offset = Math.sqrt(variance) * mult;
    upper.push({ time: candles[i].time, value: mean + offset });
    lower.push({ time: candles[i].time, value: Math.max(mean - offset, 0) });
  }
  return { mid, upper, lower };
}

export function rsi(candles: Candle[], period = 14): Point[] {
  const out: Point[] = [];
  let gain = 0;
  let loss = 0;
  for (let i = 1; i < candles.length; i++) {
    const diff = candles[i].close - candles[i - 1].close;
    const up = Math.max(diff, 0);
    const down = Math.max(-diff, 0);
    if (i <= period) {
      gain += up / period;
      loss += down / period;
      if (i === period) {
        const rs = loss === 0 ? 100 : gain / loss;
        out.push({ time: candles[i].time, value: 100 - 100 / (1 + rs) });
      }
      continue;
    }
    gain = (gain * (period - 1) + up) / period;
    loss = (loss * (period - 1) + down) / period;
    const rs = loss === 0 ? 100 : gain / loss;
    out.push({ time: candles[i].time, value: 100 - 100 / (1 + rs) });
  }
  return out;
}

export function macd(candles: Candle[], fast = 12, slow = 26, signalPeriod = 9) {
  const fastE = ema(candles, fast);
  const slowE = ema(candles, slow);
  const slowByTime = new Map(slowE.map((p) => [p.time, p.value]));
  const macdLine: Point[] = [];
  for (const p of fastE) {
    const s = slowByTime.get(p.time);
    if (s !== undefined) macdLine.push({ time: p.time, value: p.value - s });
  }
  const k = 2 / (signalPeriod + 1);
  let prev = 0;
  const signal: Point[] = [];
  for (let i = 0; i < macdLine.length; i++) {
    prev = i === 0 ? macdLine[i].value : macdLine[i].value * k + prev * (1 - k);
    if (i >= signalPeriod - 1) signal.push({ time: macdLine[i].time, value: prev });
  }
  const hist: Point[] = macdLine
    .map((p) => ({ time: p.time, value: p.value - (signal.find((s) => s.time === p.time)?.value ?? p.value) }))
    .filter((p) => signal.some((s) => s.time === p.time));
  return { macdLine, signal, hist };
}

/** Rolling volume-weighted average price. */
export function vwap(candles: Candle[], period = 30): Point[] {
  const out: Point[] = [];
  for (let i = period - 1; i < candles.length; i++) {
    let pv = 0;
    let v = 0;
    for (let j = i - period + 1; j <= i; j++) {
      const typical = (candles[j].high + candles[j].low + candles[j].close) / 3;
      pv += typical * candles[j].volume;
      v += candles[j].volume;
    }
    out.push({ time: candles[i].time, value: v ? pv / v : candles[i].close });
  }
  return out;
}

export type StudyRow = {
  id: string;
  label: string;
  color: string;
  points: Point[];
};

/** Everything the panel needs for one overlay set. */
export function buildOverlays(candles: Candle[], enabled: Set<string>) {
  const rows: StudyRow[] = [];
  if (enabled.has('ema20')) rows.push({ id: 'ema20', label: 'EMA 20', color: '#f2b544', points: ema(candles, 20) });
  if (enabled.has('ema50')) rows.push({ id: 'ema50', label: 'EMA 50', color: '#7c8cff', points: ema(candles, 50) });
  if (enabled.has('sma200')) rows.push({ id: 'sma200', label: 'SMA 200', color: '#e0709a', points: sma(candles, 200) });
  if (enabled.has('vwap')) rows.push({ id: 'vwap', label: 'VWAP 30', color: '#4fd1c5', points: vwap(candles, 30) });
  return rows;
}
