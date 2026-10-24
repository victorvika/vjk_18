import { describe, expect, it } from 'vitest';
import { INSTRUMENTS, generateCandles, aggregate } from '../lib/market';
import { bollinger, ema, macd, rsi, sma, vwap } from '../lib/studies';
import { buildOrderBook, buildTape, summarize } from '../lib/feed';

const inst = INSTRUMENTS[0];
const bars = generateCandles(inst, '5m', 260);

describe('market generator', () => {
  it('is deterministic for a symbol/timeframe pair', () => {
    const again = generateCandles(inst, '5m', 260);
    expect(again.map((c) => c.close)).toEqual(bars.map((c) => c.close));
  });

  it('produces well-formed OHLC with positive volume', () => {
    expect(bars.length).toBe(260);
    for (const c of bars) {
      expect(c.high).toBeGreaterThanOrEqual(Math.max(c.open, c.close) - 1e-9);
      expect(c.low).toBeLessThanOrEqual(Math.min(c.open, c.close) + 1e-9);
      expect(c.low).toBeGreaterThan(0);
      expect(c.volume).toBeGreaterThan(0);
      expect(Number.isFinite(c.close)).toBe(true);
    }
  });

  it('keeps bars inside the exchange session window', () => {
    for (const c of bars) {
      const d = new Date(c.time * 1000);
      const minutes = d.getUTCHours() * 60 + d.getUTCMinutes();
      expect(minutes).toBeGreaterThanOrEqual(inst.session.openMinute);
      expect(minutes).toBeLessThan(inst.session.closeMinute);
      expect([0, 6]).not.toContain(d.getUTCDay());
    }
  });

  it('aggregates candles without inventing gaps', () => {
    const hourly = aggregate(bars, 60, 5);
    const factor = 12;
    expect(hourly.length).toBe(Math.ceil(bars.length / factor));
    expect(hourly[0].open).toBe(bars[0].open);
    expect(hourly[0].volume).toBe(bars.slice(0, factor).reduce((a, c) => a + c.volume, 0));
  });
});

describe('studies', () => {
  it('returns finite series that track the input length', () => {
    for (const series of [sma(bars, 20), ema(bars, 20), vwap(bars, 20), rsi(bars), sma(bars, 50)]) {
      expect(series.length).toBeGreaterThan(0);
      expect(series.length).toBeLessThanOrEqual(bars.length);
      expect(series.every((p) => Number.isFinite(p.value))).toBe(true);
    }
  });

  it('keeps RSI inside 0..100', () => {
    expect(rsi(bars).every((p) => p.value >= 0 && p.value <= 100)).toBe(true);
  });

  it('orders Bollinger bands low < mid < high', () => {
    const { mid, upper, lower } = bollinger(bars, 20, 2);
    expect(upper.length).toBe(lower.length);
    for (let i = 0; i < upper.length; i++) {
      expect(lower[i].value).toBeLessThanOrEqual(mid[i].value);
      expect(upper[i].value).toBeGreaterThanOrEqual(mid[i].value);
      expect(upper[i].time).toBe(lower[i].time);
    }
  });

  it('aligns MACD histogram times with the signal line', () => {
    const { hist, signal } = macd(bars);
    const times = new Set(signal.map((p) => p.time));
    expect(hist.every((p) => times.has(p.time))).toBe(true);
  });
});

describe('feed', () => {
  it('builds a book whose best bid sits below the best ask', () => {
    const book = buildOrderBook(inst, 24187.4, 10);
    expect(book.bids[0].price).toBeLessThan(book.asks[0].price);
    expect(book.bids[0].total).toBe(book.bids[0].size);
    expect(book.bids.at(-1)!.total).toBeGreaterThan(book.bids[0].total);
  });

  it('emits newest-first tape prints with valid sides', () => {
    const tape = buildTape(inst, 24187.4, 12);
    expect(tape).toHaveLength(12);
    expect(tape[0].time).toBeGreaterThanOrEqual(tape[1].time);
    expect(tape.every((p) => p.side === 'buy' || p.side === 'sell')).toBe(true);
  });

  it('summarises the session consistently', () => {
    const s = summarize(bars)!;
    expect(s.high).toBeGreaterThanOrEqual(s.low);
    expect(s.last).toBe(bars.at(-1)!.close);
    expect(s.barCount).toBe(bars.length);
  });
});
