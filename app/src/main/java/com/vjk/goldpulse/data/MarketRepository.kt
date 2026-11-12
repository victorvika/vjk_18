package com.vjk.goldpulse.data

import com.vjk.goldpulse.strategy.lsms.Bar
import com.vjk.goldpulse.strategy.lsms.Instrument
import com.vjk.goldpulse.strategy.lsms.LsmsConfig
import com.vjk.goldpulse.strategy.lsms.LsmsEngine
import com.vjk.goldpulse.strategy.lsms.LsmsResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Glue between the data feed and the strategy engine.
 *
 * Keeps the ViewModel free of threading and parsing concerns, and is the single place
 * where a symbol string is mapped to an [Instrument].
 */
class MarketRepository(
    private val source: CandleSource = YahooCandleSource(),
) {

    data class Analysis(
        val symbol: String,
        val instrument: Instrument,
        val candles: List<Candle>,
        val result: LsmsResult,
        val quote: Quote?,
        val fetchedAt: Long,
    )

    suspend fun analyse(
        symbol: String,
        interval: Interval,
        instrument: Instrument,
        config: LsmsConfig,
        biasMinutes: Int,
    ): Analysis = withContext(Dispatchers.Default) {
        val candles = source.fetchCandles(symbol, interval, interval.defaultBars)
        require(candles.size >= 20) {
            "Only ${candles.size} bars returned for $symbol ${interval.label}. " +
                "Gold may be closed, or the Yahoo interval limits were hit."
        }

        val bars = candles.map {
            Bar(it.time, it.open, it.high, it.low, it.close, it.volume)
        }

        val bias = com.vjk.goldpulse.strategy.lsms.HtfBias.series(
            bars = bars,
            minutesPerBar = biasMinutes,
            emaLength = config.biasEmaLength,
        )

        val engine = LsmsEngine(config, instrument)
        val result = engine.simulate(bars, bias)

        Analysis(
            symbol = symbol,
            instrument = instrument,
            candles = candles,
            result = result,
            quote = runCatching { source.fetchQuote(symbol) }.getOrNull(),
            fetchedAt = System.currentTimeMillis(),
        )
    }
}
