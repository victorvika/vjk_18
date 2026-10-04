# TradingView A+ Entry Model

A configurable **Pine Script v6 indicator** that marks selective long and short pullback entries when trend, momentum, volume, trend strength, and price action align.

> This is an indicator and risk-planning aid—not an automated trading system or financial advice. Validate it on your own market and timeframe before making trading decisions.

## Model logic

An entry can score up to six confirmations:

1. **Trend:** 21 EMA, 50 EMA, and 200 EMA are correctly stacked, with price on the trend side.
2. **Pullback:** price touches the fast EMA area and closes back in the trend direction.
3. **Momentum:** RSI is strengthening and directional movement agrees.
4. **Relative volume:** volume exceeds its moving average by the configured multiplier. Symbols without usable volume data are not unfairly rejected.
5. **Trend strength:** ADX is above its minimum.
6. **Trigger candle:** a sufficiently large directional candle breaks the prior candle's high or low.

Trend and pullback are always mandatory. The selected quality mode determines the minimum total score:

| Mode | Required score | Intended behavior |
| --- | ---: | --- |
| Strict | 6/6 | Fewest, highest-confluence signals |
| Balanced | 5/6 | Moderate selectivity |
| Frequent | 4/6 | More opportunities |

## Install in TradingView

1. Open [`aplus_entry_model.pine`](./aplus_entry_model.pine) and copy all its contents.
2. Open a chart on [TradingView](https://www.tradingview.com/).
3. Open **Pine Editor**, create a new indicator, and replace the editor contents.
4. Click **Save**, then **Add to chart**.
5. Start with **Strict** mode and bar-close confirmation enabled.

## Alerts

The indicator exposes three TradingView alert conditions:

- `A+ Long Entry`
- `A+ Short Entry`
- `Any A+ Entry`

It also emits a JSON payload through `alert()` for webhook workflows:

```json
{
  "model": "A+ Entry",
  "side": "long",
  "ticker": "NSE:NIFTY",
  "timeframe": "15",
  "entry": 25000.0,
  "stop": 24950.0,
  "target": 25100.0
}
```

To use the JSON alert, choose **Any alert() function call** while creating the TradingView alert. Keep bar-close confirmation enabled to reduce intrabar/repainting behavior.

## Suggested starting profiles

These are starting points, not performance claims.

### NIFTY / BANKNIFTY intraday

- Chart: 5- or 15-minute
- Session: enable and use `0915-1530`
- Signal quality: Strict
- ADX minimum: 20–25
- Relative volume: 1.2
- Cooldown: 10 bars

### Liquid stocks

- Chart: 15-minute or 1-hour
- Signal quality: Strict or Balanced
- Relative volume: 1.3–1.5
- Check that the chart has reliable volume data

### Crypto

- Chart: 15-minute to 4-hour
- Disable the session filter
- Signal quality: Strict
- Consider increasing ATR stop distance for volatile instruments

## Risk guide

At each signal, the indicator plots:

- entry at the confirmed candle close;
- stop at a configurable ATR distance; and
- target at a configurable reward/risk multiple.

These lines are visual guides only. Position sizing, fees, slippage, gaps, liquidity, and actual order execution are not modeled.

## Practical validation checklist

1. Test multiple years and different market regimes.
2. Avoid optimizing settings against only one symbol or short period.
3. Forward-test on paper before risking capital.
4. Include brokerage, slippage, and taxes in your own evaluation.
5. Define a maximum per-trade and daily loss independently of the indicator.
6. Treat alerts as candidates requiring your own review—not guaranteed entries.

## Customization

All major values are editable from the indicator settings. For deeper changes, the conditions are grouped clearly in `aplus_entry_model.pine`. The script uses confirmed bars by default and does not use future-looking data or `request.security()` lookahead.

## License

MIT—see [LICENSE](./LICENSE).
