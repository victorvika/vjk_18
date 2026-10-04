# Smart Risk A+ Trading Model

An advanced, non-repainting-by-design **TradingView Pine Script v6 indicator** that follows a strict top-down sequence:

**HTF liquidity sweep → LTF market structure shift → FVG violation → IFVG → 50% CE retracement → risk-defined entry**

The default profile uses a **1-hour liquidity context** and a **5-minute execution chart**.

> This indicator is an analytical and risk-planning tool—not financial advice or an automated trading system. Signals are not guarantees. Validate the model on your instrument, session, and data feed before making trading decisions.

## Model sequence

### 1. Confirmed higher-timeframe liquidity sweep

The model finds confirmed major HTF swing highs and lows with pivot logic. A sweep requires price to:

- trade beyond the major swing;
- close back inside the swept level;
- print a wick that meets both wick/range and wick/body thresholds; and
- complete the HTF candle.

HTF values use a one-bar offset with `barmerge.lookahead_on`. This intentionally delays recognition until the higher-timeframe candle is closed, avoiding future leakage and unstable live-HTF signals.

- A low sweep starts a potential bullish sequence.
- A high sweep starts a potential bearish sequence.

### 2. Lower-timeframe market structure shift

After the liquidity sweep, the indicator snapshots the latest opposing LTF swing:

- bullish MSS: a displacement close above the swing high;
- bearish MSS: a displacement close below the swing low.

The displacement body must meet the configurable ATR threshold.

### 3. Inversed Fair Value Gap

The script registers regular three-candle FVGs without drawing them, keeping the chart clean:

- bullish FVG: current low is above the high from two bars earlier;
- bearish FVG: current high is below the low from two bars earlier.

A regular FVG becomes an IFVG only after a strong body closes through its far boundary. The flip must agree with the active LS/MSS direction. Candidate FVGs are stored in bounded Pine arrays and removed after violation or expiry.

### 4. Consequent Encroachment

Every confirmed IFVG receives an exact 50% midpoint, or **Consequent Encroachment (CE)**. It is drawn as a one-pixel dotted line inside a dashed, 95%-transparent IFVG box.

### 5. Entry

An entry can occur only on a later confirmed candle that retraces to the CE:

- Buy: price taps CE after a bullish sequence.
- Sell: price taps CE after a bearish sequence.

By default, the candle must close back through CE in the expected direction. Disable **Require close back through CE** to accept any touch.

### 6. Smart risk targets

The entry guide uses:

- **Entry:** exact IFVG CE;
- **Stop:** recent swing low for buys or recent swing high for sells;
- **Take profit:** `5R` when entry direction agrees with the HTF EMA trend;
- **Take profit:** `2.5R` when counter-trend.

The entry, stop, and target use short one-pixel dotted/dashed lines extending only to the right.

## Minimalist UI

The indicator intentionally avoids chart clutter:

- muted slate, teal, soft green, crimson, and amber palette;
- no neon colors or candle recoloring;
- transparent IFVG interiors with thin dashed borders;
- dotted one-pixel CE lines;
- tiny structure labels with `label.style_none` above/below price;
- bounded drawing history;
- a fully transparent, tiny-text dashboard in the bottom-right.

Regular FVGs remain hidden until they flip into a setup-relevant IFVG.

## Install in TradingView

1. Open [`aplus_entry_model.pine`](./aplus_entry_model.pine).
2. Copy the complete script.
3. Open a TradingView chart and select **Pine Editor**.
4. Create a new indicator and replace the editor contents.
5. Select **Save**, then **Add to chart**.
6. Use a 5-minute chart with the default 1-hour HTF profile, or update both timeframe settings together.

## Alerts

The script exposes these alert conditions:

- `Bullish HTF Liquidity Sweep`
- `Bearish HTF Liquidity Sweep`
- `Bullish Market Structure Shift`
- `Bearish Market Structure Shift`
- `Smart Risk A+ Buy`
- `Smart Risk A+ Sell`
- `Any Smart Risk A+ Entry`

For automation workflows, choose **Any alert() function call**. Entry alerts emit JSON:

```json
{
  "model": "Smart Risk A+",
  "side": "buy",
  "ticker": "NSE:NIFTY",
  "timeframe": "5",
  "entry": 25000.0,
  "stop": 24950.0,
  "target": 25250.0,
  "rr": 5.0
}
```

Create alerts **Once Per Bar Close**. The model itself requires confirmed chart candles.

## Default workflow

1. Open a 5-minute chart.
2. Keep HTF at `60` and **Require execution timeframe** enabled.
3. Wait for the bottom-right sequence status to progress:
   - `LS confirmed`
   - `MSS confirmed`
   - `CE pending`
   - `Entry active`
4. Review the IFVG, recent-swing stop, target, spread, liquidity, and event risk before making any decision.

If the dashboard displays **Check timeframe**, the chart does not match the configured execution timeframe or is not lower than the HTF.

## Important implementation details

- No `request.security()` lookahead bias: only the previous confirmed HTF candle is consumed.
- Entries and structure shifts require `barstate.isconfirmed`.
- Old FVG candidates, zones, and target guides are bounded to protect TradingView object limits.
- A setup expires after a configurable number of chart bars.
- An invalid or expired IFVG returns the sequence to the post-MSS search stage.
- A newer confirmed liquidity sweep replaces the unfinished sequence.
- The script does not place orders, size positions, account for costs, or claim profitability.

## Suggested validation checklist

1. Replay the sequence candle by candle before using live alerts.
2. Test multiple years, symbols, sessions, and volatility regimes.
3. Include slippage, brokerage, taxes, gaps, and missed fills in evaluation.
4. Avoid optimizing parameters against one short sample.
5. Paper trade before risking capital.
6. Define independent per-trade and daily loss limits.

## License

MIT—see [LICENSE](./LICENSE).
