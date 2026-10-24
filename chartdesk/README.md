# ChartDeck — offline XAUUSD terminal for Android

An installable, phone-first gold (XAUUSD) charting app. Works with **no server,
no account and no subscription**: open one file, or install it once and it runs
offline from cache.

Load your own history exported from MetaTrader, TradingView, Dukascopy or any
CSV/JSON — the data never leaves the device. With no file loaded it falls back
to clearly-labelled synthetic bars so the UI is never empty.

Features: candlestick chart with studies, watchlist, depth ladder, time & sales
tape, and a keyboard command palette.

Built from scratch. It is **not** a copy of TradingView — no TradingView markup,
CSS, client bundle, logo or market data is used. The only thing taken from
TradingView is their open-source charting library **Lightweight Charts™**
(Apache-2.0), which is a normal dependency, credited in the UI footer.

The visual language is a generic dark terminal layout (top bar → ticker tape →
watchlist / chart / depth rail) that is common to every market workstation. All
tokens, components and copy here were written for this project.

## Why not a TradingView clone

`in.tradingview.com` is proprietary: the page markup, stylesheets, bundled JS,
wordmark and price data are all theirs, and the data is licensed per exchange.
Scraping it and rebuilding a look-alike would be copyright and trademark
infringement regardless of how the bundle is obtained. REA/Ghidra would also be
the wrong tools — Ghidra decompiles native machine code, while a web app's JS is
already readable.

So this is a **clean-room build in the same product category**, with data that is
generated locally and labelled as such everywhere it appears.

## Use it on Android (no subscription, no server)

Two builds, pick whichever suits you:

| Build | Path | How to open |
| --- | --- | --- |
| **Single file** (recommended) | `standalone/index.html` (393 kB) | Copy to the phone, tap it, open with Chrome. Classic inline script, works from `file://` with no network. |
| **Installable PWA** | `web/` (444 kB) | Serve the folder once over http(s), then Chrome → ⋮ → *Install app*. Cached by the service worker for offline use. |

```bash
cd chartdesk
npm install
npm run dev                    # http://localhost:5173 (desktop or LAN)
npm run build                  # typecheck + PWA build into web/
npm run build:standalone       # single-file build into standalone/index.html
npm test                       # 33 tests
```

To move the single file to a phone, any of these work: USB copy, `adb push`, a
Telegram/Drive "send to myself", or `python3 -m http.server` on the same Wi-Fi
and open `http://<your-ip>:8000/standalone/`.

Once installed, the app sits in the launcher with its own icon and opens without
a connection. Nothing is uploaded anywhere and there is no telemetry.

## Loading your own XAUUSD data

Tap **Import** (or press `i`), choose a file, review the preview, pick a merge
size, and press *Use this data*. Parsing is automatic:

| Input | Supported |
| --- | --- |
| Delimiters | comma, semicolon, tab, pipe (auto-detected) |
| Headers | `date,time,open,high,low,close,volume` in any case; MetaTrader's `<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL>`; or no header |
| Timestamps | unix seconds/millis, `2025-10-20 04:05:00`, `2025.10.20 04:05`, `20/10/2025 04:05`, ISO-8601 with offsets |
| Decimals | `.` or `,` (European exports) |
| JSON | `[{time,open,high,low,close,volume}]`, short keys, `[[t,o,h,l,c,v]]`, or `[[t,close]]` |

Rows are sorted, duplicate stamps collapsed, impossible OHLC repaired, and every
repair is reported in the preview rather than silently applied. Imported sets are
stored in IndexedDB, so a 100k-bar file survives a reload.

### Bundled sample

`src/data/xauusd-sample.json` holds **1,101 real hourly XAUUSD closes**
(2025-10-20 → 2025-12-30, range 3905–4583) derived from
`Andre2016Ribeiro/Pattern_search_gold_commodity`. It is close-only, so the parser
builds flat OHLC bars and says so in the import preview. It exists so you can see
the pipeline end-to-end before you have your own export.

## Stack

| Piece | Choice |
| --- | --- |
| Bundler | Vite 6 |
| UI | React 18 + TypeScript 5 (strict, `noUnusedLocals`) |
| Charts | `lightweight-charts` 5.2.1 (Apache-2.0) |
| Tests | Vitest 2 + jsdom + Testing Library |

No CSS framework, no UI kit — the whole design is ~700 lines of hand-written CSS
with custom properties.

## How it works

```
src/
  lib/rng.ts        mulberry32 + Box–Muller, so a symbol always redraws identically
  lib/market.ts     instruments, session calendar, procedural OHLCV generator
  lib/studies.ts    SMA / EMA / RSI / MACD / Bollinger / VWAP
  lib/feed.ts       order book, tape, ticker rows, formatters
  components/       Chart, Watchlist, Toolbar, OrderBook, Tape, TickerTape,
                    StatsBar, CommandPalette
  App.tsx           state, persistence, shortcuts, composition
```

**Price generation.** Each series is seeded from `hash(symbol:timeframe)`, so the
same symbol always produces the same history — reloading does not reshuffle the
chart. Bars come from a random walk with mean-reverting volatility clustering,
momentum carry-over and occasional impulse moves, then are clipped to a real
exchange session (NSE 09:15–15:30, NASDAQ 13:30–20:00 UTC, crypto 24/7) with
weekends dropped. `high`/`low` are derived from the open/close so OHLC invariants
hold, which the test suite asserts.

**Chart.** One `createChart` instance for the lifetime of the panel; series are
mutated with `setData` rather than recreated, so switching timeframe doesn't leak
canvas contexts or lose the crosshair. Overlays (EMA/SMA/VWAP) are diffed
against the previous set — removed series are disposed, new ones added.

**UI behaviour.** Symbol, timeframe and enabled indicators persist to
`localStorage`; `⌘K` / `Ctrl-K` / `/` opens the palette; the palette is fully
keyboard-driven (arrows, enter, escape) with `role="listbox"` semantics. The
book and tape re-seed every 4 s to suggest a live feed.

## Accessibility & polish

- Every interactive control is a real `<button>` with `aria-pressed` or
  `aria-current`; the palette is a labelled `role="dialog"`.
- Prices use tabular numerals so columns don't jitter.
- `prefers-reduced-motion` disables the ticker marquee.
- Layout collapses 3 → 2 → 1 column at 1180 px and 760 px.

## Tests

`npm test` → 33 passing.

```
market.test.ts   determinism, OHLC invariants, session/weekend clipping,
                 aggregation, study finiteness, RSI bounds, Bollinger ordering,
                 MACD alignment, book/tape/summary consistency
import.test.ts   timestamp formats, MT5/TradingView/no-header CSV, European
                 decimals, high/low repair, duplicate collapse, JSON shapes,
                 the bundled sample, resampling and bar-size inference
app.test.tsx     render smoke, symbol switch, timeframe toggle, mobile tab
                 switching, sample import flow, palette open + command execution
```

The single-file build is additionally smoke-tested by loading the produced
`standalone/index.html` in a real DOM (jsdom) and asserting that the app mounts
with its canvas stubbed — that check caught a `file://` bug where the inlined
classic script ran before `#root` existed.

The component tests mock `lightweight-charts` because jsdom has no canvas; the
charting path itself was verified in a real browser through the Vite dev server.

## Disclaimer

All prices, volumes, order book levels and trades are procedurally generated for
interface demonstration. Nothing here is a real quote and nothing here is
investment advice.
