# ChartDeck

An original browser trading terminal: candlestick chart with studies, watchlist,
synthetic order book, time & sales tape, and a keyboard command palette.

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

## Run

```bash
cd chartdesk
npm install
npm run dev        # http://localhost:5173
npm run build      # typecheck + production bundle into dist/
npm test           # 15 tests
```

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

`npm test` → 15 passing.

```
market.test.ts   determinism, OHLC invariants, session/weekend clipping,
                 aggregation, study finiteness, RSI bounds, Bollinger ordering,
                 MACD alignment, book/tape/summary consistency
app.test.tsx     render smoke, symbol switch from watchlist, timeframe toggle,
                 palette open + command execution
```

The component tests mock `lightweight-charts` because jsdom has no canvas; the
charting path itself was verified in a real browser through the Vite dev server.

## Disclaimer

All prices, volumes, order book levels and trades are procedurally generated for
interface demonstration. Nothing here is a real quote and nothing here is
investment advice.
