import type { Candle } from './market';

export type ParseResult = {
  candles: Candle[];
  warnings: string[];
  format: 'csv' | 'json';
  columns: string[];
  timezoneAssumption: 'utc' | 'local';
};

const HEADER_ALIASES: Record<string, string[]> = {
  time: ['time', 'date', 'datetime', 'timestamp', 'date_time', 'date time', 'open time', '<date>', '<time>', 'gmt time', 'local time', 'utc'],
  open: ['open', 'o', 'open price', '<open>', 'bidopen'],
  high: ['high', 'h', 'high price', '<high>', 'bidhigh'],
  low: ['low', 'l', 'low price', '<low>', 'bidlow'],
  close: ['close', 'c', 'close price', '<close>', 'bidclose', 'price', 'last', 'adj close'],
  volume: ['volume', 'vol', 'v', 'tickvol', 'tick volume', '<tickvol>', '<vol>', 'real volume'],
};

function detectDelimiter(line: string): string {
  const candidates = [',', ';', '\t', '|'];
  let best = ',';
  let bestCount = -1;
  for (const c of candidates) {
    const count = line.split(c).length - 1;
    if (count > bestCount) {
      best = c;
      bestCount = count;
    }
  }
  return best;
}

function splitLine(line: string, delim: string): string[] {
  // quoted CSV fields are handled, but trading data rarely uses them
  const out: string[] = [];
  let cur = '';
  let quoted = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (quoted && line[i + 1] === '"') {
        cur += '"';
        i++;
      } else quoted = !quoted;
    } else if (ch === delim && !quoted) {
      out.push(cur);
      cur = '';
    } else cur += ch;
  }
  out.push(cur);
  return out.map((s) => s.trim());
}

const normalise = (s: string) => s.toLowerCase().replace(/["']/g, '').replace(/\s+/g, ' ').trim();

function mapColumns(header: string[]): Record<string, number> {
  const map: Record<string, number> = {};
  header.forEach((raw, i) => {
    const name = normalise(raw);
    for (const [field, aliases] of Object.entries(HEADER_ALIASES)) {
      if (map[field] !== undefined) continue;
      if (aliases.includes(name)) map[field] = i;
    }
  });
  return map;
}

/** Numbers may use either `.` or `,` as the decimal separator. */
function toNumber(raw: string): number {
  const cleaned = raw.replace(/[^\d.,+-]/g, '');
  if (!cleaned) return NaN;
  const lastComma = cleaned.lastIndexOf(',');
  const lastDot = cleaned.lastIndexOf('.');
  let normalised = cleaned;
  if (lastComma > lastDot) normalised = cleaned.replace(/\./g, '').replace(',', '.');
  else normalised = cleaned.replace(/,/g, '');
  return Number(normalised);
}

/**
 * Accepts the timestamp shapes brokers and exporters actually emit:
 * unix seconds/millis, ISO-8601, `YYYY.MM.DD HH:MM`, `DD/MM/YYYY` and friends.
 * Ambiguous day/month orders prefer day-first, matching MetaTrader exports.
 */
export function parseTimestamp(raw: string): { seconds: number; assumedUtc: boolean } | null {
  const value = raw.trim();
  if (!value) return null;

  if (/^\d{10}$/.test(value)) return { seconds: Number(value), assumedUtc: true };
  if (/^\d{13}$/.test(value)) return { seconds: Math.floor(Number(value) / 1000), assumedUtc: true };

  const iso = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?(Z|[+-]\d{2}:?\d{2})?$/.exec(value);
  if (iso) {
    const [, y, mo, d, h = '0', mi = '0', s = '0', tz] = iso;
    const ms = Date.UTC(+y, +mo - 1, +d, +h, +mi, +s);
    if (!tz) return { seconds: Math.floor(ms / 1000), assumedUtc: true };
    if (tz === 'Z') return { seconds: Math.floor(ms / 1000), assumedUtc: true };
    const sign = tz.startsWith('-') ? -1 : 1;
    const [hh, mm] = tz.slice(1).replace(':', '').match(/\d{2}/g)!.map(Number);
    return { seconds: Math.floor(ms / 1000) - sign * (hh * 3600 + mm * 60), assumedUtc: true };
  }

  const dotted = /^(\d{4})[./](\d{2})[./](\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?$/.exec(value);
  if (dotted) {
    const [, y, mo, d, h = '0', mi = '0', s = '0'] = dotted;
    return { seconds: Math.floor(Date.UTC(+y, +mo - 1, +d, +h, +mi, +s) / 1000), assumedUtc: true };
  }

  const dayFirst = /^(\d{1,2})[/.](\d{1,2})[/.](\d{4})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?$/.exec(value);
  if (dayFirst) {
    const [, d, mo, y, h = '0', mi = '0', s = '0'] = dayFirst;
    return { seconds: Math.floor(Date.UTC(+y, +mo - 1, +d, +h, +mi, +s) / 1000), assumedUtc: true };
  }

  const parsed = Date.parse(value);
  if (Number.isFinite(parsed)) return { seconds: Math.floor(parsed / 1000), assumedUtc: false };
  return null;
}

/** Collapse duplicate timestamps, sort ascending, drop impossible OHLC rows. */
function finalise(candles: Candle[], warnings: string[]): Candle[] {
  const byTime = new Map<number, Candle>();
  let dropped = 0;
  let repaired = 0;
  for (const c of candles) {
    if (!Number.isFinite(c.open) || !Number.isFinite(c.high) || !Number.isFinite(c.low) || !Number.isFinite(c.close)) {
      dropped++;
      continue;
    }
    // Some exports swap the high/low columns; restoring the order recovers the
    // real range instead of collapsing it onto the open/close.
    let [rowHigh, rowLow] = c.high >= c.low ? [c.high, c.low] : [c.low, c.high];
    rowHigh = Math.max(rowHigh, c.open, c.close);
    rowLow = Math.min(rowLow, c.open, c.close);
    if (rowHigh !== c.high || rowLow !== c.low) repaired++;
    byTime.set(c.time, { ...c, high: rowHigh, low: rowLow, volume: Number.isFinite(c.volume) ? c.volume : 0 });
  }
  if (dropped) warnings.push(`${dropped} row(s) skipped: unreadable prices.`);
  if (repaired) warnings.push(`${repaired} row(s) had high/low outside open/close and were repaired.`);
  const out = [...byTime.values()].sort((a, b) => a.time - b.time);
  if (out.length !== candles.length) {
    warnings.push(`${candles.length - out.length} duplicate timestamp(s) collapsed.`);
  }
  return out;
}

export function parseCsv(text: string): ParseResult {
  const warnings: string[] = [];
  const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
  if (!lines.length) throw new Error('File is empty.');

  const delim = detectDelimiter(lines[0]);
  const firstFields = splitLine(lines[0], delim);
  // A header row is mostly words: a data row can still contain dates, so require
  // at least two fields that are neither numbers nor timestamps.
  const textual = firstFields.filter(
    (f) => f.trim() !== '' && Number.isNaN(toNumber(f)) && !parseTimestamp(f),
  ).length;
  const looksLikeHeader = textual >= 2;
  const cols = looksLikeHeader
    ? mapColumns(firstFields)
    : // no header: assume date,open,high,low,close[,volume]
      { time: 0, open: 1, high: 2, low: 3, close: 4, volume: 5 };

  if (cols.close === undefined) throw new Error('Could not find a close/price column.');
  if (cols.time === undefined) throw new Error('Could not find a date/time column.');

  // MetaTrader exports the calendar date and the clock time as two columns.
  const clockIndex = looksLikeHeader
    ? firstFields.findIndex((f, i) => i !== cols.time && /^<?time>?$/.test(normalise(f)))
    : -1;

  const start = looksLikeHeader ? 1 : 0;
  const candles: Candle[] = [];
  let assumedUtc = 0;
  let ambiguous = 0;
  let closeOnly = 0;

  for (let i = start; i < lines.length; i++) {
    const fields = splitLine(lines[i], delim);
    if (fields.length <= cols.close) continue;
    let stampSource = fields[cols.time];
    if (clockIndex >= 0 && fields[clockIndex]) stampSource = `${stampSource} ${fields[clockIndex]}`;
    const stamp = parseTimestamp(stampSource);
    if (!stamp) {
      ambiguous++;
      continue;
    }
    const close = toNumber(fields[cols.close]);
    if (!Number.isFinite(close)) continue;
    const open = cols.open !== undefined ? toNumber(fields[cols.open]) : NaN;
    const high = cols.high !== undefined ? toNumber(fields[cols.high]) : NaN;
    const low = cols.low !== undefined ? toNumber(fields[cols.low]) : NaN;
    const volume = cols.volume !== undefined ? toNumber(fields[cols.volume]) : 0;

    if (Number.isFinite(open) && Number.isFinite(high) && Number.isFinite(low)) {
      candles.push({ time: stamp.seconds, open, high, low, close, volume });
    } else if (Number.isFinite(open)) {
      candles.push({ time: stamp.seconds, open, high: Math.max(open, close), low: Math.min(open, close), close, volume });
    } else {
      // close-only series: build a flat bar so the chart still renders
      candles.push({ time: stamp.seconds, open: close, high: close, low: close, close, volume });
      closeOnly++;
    }
    if (stamp.assumedUtc) assumedUtc++;
  }

  if (ambiguous) warnings.push(`${ambiguous} row(s) skipped: timestamp not understood.`);
  if (closeOnly) warnings.push(`${closeOnly} row(s) had close only — OHLC bars were built flat.`);
  if (!candles.length) throw new Error('No usable price rows found.');

  const merged = finalise(candles, warnings);

  return {
    candles: merged,
    warnings,
    format: 'csv',
    columns: Object.keys(cols).filter((k) => cols[k] !== undefined),
    timezoneAssumption: assumedUtc > merged.length / 2 ? 'utc' : 'local',
  };
}

type JsonBar = { time?: unknown; t?: unknown; date?: unknown; open?: unknown; o?: unknown; high?: unknown; h?: unknown; low?: unknown; l?: unknown; close?: unknown; c?: unknown; volume?: unknown; v?: unknown };

export function parseJson(text: string): ParseResult {
  const warnings: string[] = [];
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch (err) {
    throw new Error(`Not valid JSON: ${(err as Error).message}`);
  }

  const root = data as { bars?: unknown; candles?: unknown; data?: unknown };
  const rawList =
    Array.isArray(data) ? data
    : Array.isArray(root?.bars) ? root.bars
    : Array.isArray(root?.candles) ? root.candles
    : Array.isArray(root?.data) ? root.data
    : null;
  if (!rawList) throw new Error('Expected an array of bars, or an object with a "bars"/"candles" array.');

  const candles: Candle[] = [];
  let closeOnly = 0;
  let bad = 0;

  for (const item of rawList as JsonBar[]) {
    if (Array.isArray(item)) {
      // [time, open, high, low, close, volume] or [time, close]
      const [t, a, b, c, d, e] = item as unknown[];
      const stamp = typeof t === 'number' ? { seconds: t > 1e12 ? Math.floor(t / 1000) : t } : parseTimestamp(String(t ?? ''));
      if (!stamp) {
        bad++;
        continue;
      }
      if (typeof a === 'number' && typeof b === 'number' && typeof c === 'number' && typeof d === 'number') {
        candles.push({ time: stamp.seconds, open: a, high: b, low: c, close: d, volume: typeof e === 'number' ? e : 0 });
      } else if (typeof a === 'number') {
        candles.push({ time: stamp.seconds, open: a, high: a, low: a, close: a, volume: 0 });
        closeOnly++;
      } else bad++;
      continue;
    }

    const record = item as Record<string, unknown>;
    const rawTime = record.time ?? record.t ?? record.date;
    const stamp =
      typeof rawTime === 'number'
        ? { seconds: rawTime > 1e12 ? Math.floor(rawTime / 1000) : rawTime, assumedUtc: true }
        : parseTimestamp(String(rawTime ?? ''));
    if (!stamp) {
      bad++;
      continue;
    }
    const pick = (...keys: string[]) => {
      for (const k of keys) {
        const v = record[k];
        if (typeof v === 'number' && Number.isFinite(v)) return v;
        if (typeof v === 'string') {
          const n = toNumber(v);
          if (Number.isFinite(n)) return n;
        }
      }
      return NaN;
    };
    const close = pick('close', 'c', 'Close', 'price');
    const open = pick('open', 'o', 'Open');
    const high = pick('high', 'h', 'High');
    const low = pick('low', 'l', 'Low');
    const volume = pick('volume', 'v', 'Volume');
    if (!Number.isFinite(close)) {
      bad++;
      continue;
    }
    if (Number.isFinite(open) && Number.isFinite(high) && Number.isFinite(low)) {
      candles.push({ time: stamp.seconds, open, high, low, close, volume: Number.isFinite(volume) ? volume : 0 });
    } else {
      candles.push({ time: stamp.seconds, open: close, high: close, low: close, close, volume: Number.isFinite(volume) ? volume : 0 });
      closeOnly++;
    }
  }

  if (bad) warnings.push(`${bad} entry(ies) skipped: missing or unreadable price/time.`);
  if (closeOnly) warnings.push(`${closeOnly} entry(ies) were close-only — OHLC bars were built flat.`);
  if (!candles.length) throw new Error('No usable price rows found.');

  return {
    candles: finalise(candles, warnings),
    warnings,
    format: 'json',
    columns: ['time', 'close'],
    timezoneAssumption: 'utc',
  };
}

export function parseMarketFile(name: string, text: string): ParseResult {
  const lower = name.toLowerCase();
  if (lower.endsWith('.json') || text.trim().startsWith('{') || text.trim().startsWith('[')) return parseJson(text);
  return parseCsv(text);
}

/** Aggregate arbitrary bar spacing up to a coarser bucket, anchored on the hour. */
export function resample(candles: Candle[], bucketSeconds: number): Candle[] {
  if (bucketSeconds <= 0) return candles;
  const out = new Map<number, Candle>();
  for (const c of candles) {
    const bucket = Math.floor(c.time / bucketSeconds) * bucketSeconds;
    const existing = out.get(bucket);
    if (!existing) {
      out.set(bucket, { ...c, time: bucket });
    } else {
      existing.high = Math.max(existing.high, c.high);
      existing.low = Math.min(existing.low, c.low);
      existing.close = c.close;
      existing.volume += c.volume;
    }
  }
  return [...out.values()].sort((a, b) => a.time - b.time);
}

export function inferBarSeconds(candles: Candle[]): number {
  if (candles.length < 3) return 0;
  const deltas: number[] = [];
  for (let i = 1; i < Math.min(candles.length, 200); i++) {
    const d = candles[i].time - candles[i - 1].time;
    if (d > 0) deltas.push(d);
  }
  if (!deltas.length) return 0;
  deltas.sort((a, b) => a - b);
  return deltas[Math.floor(deltas.length / 2)];
}
