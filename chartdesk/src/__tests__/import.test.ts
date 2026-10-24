import { describe, expect, it } from 'vitest';
import { inferBarSeconds, parseCsv, parseJson, parseMarketFile, parseTimestamp, resample } from '../lib/import';
import sample from '../data/xauusd-sample.json';

describe('timestamp parsing', () => {
  it('reads the formats brokers actually export', () => {
    expect(parseTimestamp('2025-10-20 04:05:00')!.seconds).toBe(1760933100);
    expect(parseTimestamp('2025.10.20 04:05')!.seconds).toBe(1760933100);
    expect(parseTimestamp('20/10/2025 04:05')!.seconds).toBe(1760933100);
    expect(parseTimestamp('2025-10-20T04:05:00Z')!.seconds).toBe(1760933100);
    expect(parseTimestamp('1760933100')!.seconds).toBe(1760933100);
    expect(parseTimestamp('1760933100000')!.seconds).toBe(1760933100);
  });

  it('applies explicit offsets and rejects nonsense', () => {
    expect(parseTimestamp('2025-10-20T09:35:00+05:30')!.seconds).toBe(1760933100);
    expect(parseTimestamp('not a date')).toBeNull();
    expect(parseTimestamp('')).toBeNull();
  });
});

describe('CSV import', () => {
  it('handles a MetaTrader-style header and tab delimiter', () => {
    const csv = [
      '<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>',
      '2025.10.20\t04:05\t4276.40\t4277.10\t4275.90\t4276.80\t812',
      '2025.10.20\t04:10\t4276.80\t4277.55\t4276.20\t4277.20\t640',
    ].join('\n');
    const { candles, warnings } = parseCsv(csv);
    expect(candles).toHaveLength(2);
    expect(candles[0].close).toBe(4276.8);
    expect(candles[0].volume).toBe(812);
    expect(candles[1].high).toBe(4277.55);
    expect(warnings).toHaveLength(0);
  });

  it('handles TradingView-style unix seconds and a BOM-free header', () => {
    const csv = ['time,open,high,low,close,volume', '1760933100,4276.4,4277.1,4275.9,4276.8,0'].join('\n');
    const { candles } = parseCsv(csv);
    expect(candles[0]).toMatchObject({ time: 1760933100, open: 4276.4, close: 4276.8 });
  });

  it('works without a header row', () => {
    const csv = ['2025-10-20 04:05:00,1.0860,1.0864,1.0858,1.0862,1200'].join('\n');
    expect(parseCsv(csv).candles[0].close).toBeCloseTo(1.0862, 4);
  });

  it('repairs high/low that sit inside the open/close range', () => {
    const csv = ['date,open,high,low,close', '2025-10-20 04:05:00,10,9,11,10.5'].join('\n');
    const { candles, warnings } = parseCsv(csv);
    expect(candles[0].high).toBe(11);
    expect(candles[0].low).toBe(9);
    expect(warnings.join(' ')).toMatch(/repaired/i);
  });

  it('sorts rows, collapses duplicates and reports bad lines', () => {
    const csv = [
      'date,open,high,low,close',
      '2025-10-20 04:10:00,2,3,1,2.5',
      '2025-10-20 04:05:00,1,2,0.5,1.5',
      'garbage line',
      '2025-10-20 04:10:00,2,3,1,2.6',
    ].join('\n');
    const { candles, warnings } = parseCsv(csv);
    expect(candles).toHaveLength(2);
    expect(candles[0].close).toBe(1.5);
    expect(candles[1].close).toBe(2.6);
    expect(warnings.join(' ')).toMatch(/timestamp|duplicate/i);
  });

  it('accepts European decimal commas when the delimiter is a semicolon', () => {
    const csv = ['time;open;high;low;close', '2025-10-20 04:05:00;4276,40;4277,10;4275,90;4276,80'].join('\n');
    expect(parseCsv(csv).candles[0].close).toBeCloseTo(4276.8, 2);
  });

  it('throws a readable error when there is no price column', () => {
    expect(() => parseCsv('foo,bar\n1,2')).toThrow(/close\/price column/i);
    expect(() => parseCsv('')).toThrow(/empty/i);
  });
});

describe('JSON import', () => {
  it('reads object bars with short keys', () => {
    const json = JSON.stringify({ bars: [{ t: 1760933100, o: 1, h: 2, l: 0.5, c: 1.5, v: 10 }] });
    const { candles } = parseJson(json);
    expect(candles[0]).toMatchObject({ time: 1760933100, open: 1, high: 2, low: 0.5, close: 1.5 });
  });

  it('reads flat [time, close] arrays and builds flat bars', () => {
    const json = JSON.stringify([[1760933100, 4276.4], [1760933400, 4277.1]]);
    const { candles, warnings } = parseJson(json);
    expect(candles).toHaveLength(2);
    expect(candles[1].high).toBe(4277.1);
    expect(warnings.join(' ')).toMatch(/close-only/i);
  });

  it('rejects malformed payloads', () => {
    expect(() => parseJson('{"nope":1}')).toThrow(/array of bars/i);
    expect(() => parseJson('{oops')).toThrow(/not valid json/i);
  });

  it('loads the bundled XAUUSD sample', () => {
    const { candles, warnings } = parseMarketFile('xauusd-sample.json', JSON.stringify(sample));
    expect(candles.length).toBeGreaterThan(1000);
    expect(candles[0].close).toBeGreaterThan(2000);
    expect(candles.every((c) => c.high >= c.low)).toBe(true);
    // the upstream series carries closes only, so the parser says so plainly
    expect(warnings.every((w) => /duplicate|close-only/i.test(w))).toBe(true);
    expect(warnings.some((w) => /close-only/i.test(w))).toBe(true);
  });
});

describe('resampling', () => {
  const bars = Array.from({ length: 24 }, (_, i) => ({
    time: 1760932800 + i * 300,
    open: 100 + i,
    high: 102 + i,
    low: 99 + i,
    close: 101 + i,
    volume: 10,
  }));

  it('folds 5-minute bars into hourly buckets', () => {
    const hourly = resample(bars, 3600);
    expect(hourly).toHaveLength(2);
    expect(hourly[0].open).toBe(bars[0].open);
    expect(hourly[0].close).toBe(bars[11].close);
    expect(hourly[0].high).toBe(bars[11].high);
    expect(hourly[0].low).toBe(bars[0].low);
    expect(hourly[0].volume).toBe(120);
  });

  it('infers the bar size from the data', () => {
    expect(inferBarSeconds(bars)).toBe(300);
    expect(inferBarSeconds([])).toBe(0);
  });
});
