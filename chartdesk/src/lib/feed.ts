import { gaussian, hashString, mulberry32 } from './rng';
import type { Candle, Instrument } from './market';

export type BookLevel = { price: number; size: number; total: number };
export type OrderBook = { bids: BookLevel[]; asks: BookLevel[]; spread: number; mid: number };
export type TapePrint = { id: number; time: number; price: number; size: number; side: 'buy' | 'sell' };

function decimalsFor(price: number): number {
  if (price >= 1000) return 2;
  if (price >= 10) return 2;
  if (price >= 1) return 4;
  return 5;
}

export const fmtPrice = (value: number, reference?: number) =>
  value.toLocaleString('en-IN', {
    minimumFractionDigits: decimalsFor(reference ?? value),
    maximumFractionDigits: decimalsFor(reference ?? value),
  });

export const fmtCompact = (value: number): string => {
  const abs = Math.abs(value);
  if (abs >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
  return value.toFixed(0);
};

export const fmtPct = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;

/** A snapshot order book built around the last price; sizes are synthetic. */
export function buildOrderBook(inst: Instrument, last: number, depth = 12, seedSalt = 0): OrderBook {
  const rand = mulberry32(hashString(`${inst.symbol}:book:${seedSalt}`));
  const tick = last * 0.00012;
  const bids: BookLevel[] = [];
  const asks: BookLevel[] = [];
  let bidTotal = 0;
  let askTotal = 0;
  for (let i = 0; i < depth; i++) {
    const bidSize = Math.round(120 + rand() * 1800 * (1 - i / (depth + 4)));
    const askSize = Math.round(120 + rand() * 1800 * (1 - i / (depth + 4)));
    bidTotal += bidSize;
    askTotal += askSize;
    bids.push({ price: last - tick * (i + 0.5), size: bidSize, total: bidTotal });
    asks.push({ price: last + tick * (i + 0.5), size: askSize, total: askTotal });
  }
  return { bids, asks, spread: tick, mid: last };
}

/** Time & sales feed, newest first. */
export function buildTape(inst: Instrument, last: number, count = 26, seedSalt = 0): TapePrint[] {
  const rand = mulberry32(hashString(`${inst.symbol}:tape:${seedSalt}`));
  const now = Date.now();
  const prints: TapePrint[] = [];
  let price = last;
  for (let i = 0; i < count; i++) {
    price = price * (1 + gaussian(rand) * inst.volatility * 0.35);
    prints.push({
      id: i,
      time: now - i * (900 + Math.round(rand() * 2600)),
      price,
      size: Math.round(1 + Math.abs(gaussian(rand)) * 240),
      side: rand() > 0.48 ? 'buy' : 'sell',
    });
  }
  return prints;
}

export type TickerRow = {
  symbol: string;
  name: string;
  last: number;
  changePct: number;
  spark: number[];
  currency: string;
};

export function buildTicker(candles: Candle[], inst: Instrument): TickerRow {
  const first = candles[Math.max(0, candles.length - 60)]?.close ?? inst.basePrice;
  const last = candles[candles.length - 1]?.close ?? inst.basePrice;
  return {
    symbol: inst.symbol,
    name: inst.name,
    last,
    changePct: ((last - first) / first) * 100,
    spark: candles.slice(-40).map((c) => c.close),
    currency: inst.currency,
  };
}

export function summarize(candles: Candle[]) {
  if (!candles.length) return null;
  const last = candles[candles.length - 1];
  const prev = candles[candles.length - 2] ?? last;
  const change = last.close - prev.close;
  const changePct = prev.close ? (change / prev.close) * 100 : 0;
  const highs = candles.map((c) => c.high);
  const lows = candles.map((c) => c.low);
  return {
    last: last.close,
    open: candles[0].open,
    high: Math.max(...highs),
    low: Math.min(...lows),
    change,
    changePct,
    volume: candles.reduce((a, c) => a + c.volume, 0),
    barCount: candles.length,
  };
}

export const clock = (ms: number) =>
  new Date(ms).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
