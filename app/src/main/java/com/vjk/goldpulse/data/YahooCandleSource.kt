package com.vjk.goldpulse.data

import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.TimeUnit

/**
 * Historical candle + quote source.
 *
 * Phase 1 uses Yahoo Finance because it needs no API key, no OAuth and no signup,
 * which is what makes a sideloadable APK possible with zero backend. Yahoo serves
 * COMEX gold front-month as `GC=F` with roughly a 10-minute delay.
 *
 * Phase 2 swaps this for Tradovate (`/md/getChart` + market-data WebSocket). The
 * [CandleSource] interface exists so the UI never learns which feed is behind it.
 */
interface CandleSource {
    suspend fun fetchCandles(symbol: String, interval: Interval, bars: Int): List<Candle>
    suspend fun fetchQuote(symbol: String): Quote?
}

data class Candle(
    val time: Long,
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double,
    val volume: Double,
)

data class Quote(
    val symbol: String,
    val price: Double,
    val previousClose: Double,
    val changePercent: Double,
    val marketTime: Long,
    val delayed: Boolean,
)

/** Bar intervals Yahoo accepts for the chart endpoint. */
enum class Interval(
    val yahooCode: String,
    val label: String,
    val minutes: Int,
    val range: String,
) {
    M1("1m", "1m", 1, "1d"),
    M5("5m", "5m", 5, "5d"),
    M15("15m", "15m", 15, "5d"),
    M30("30m", "30m", 30, "1mo"),
    H1("60m", "1H", 60, "3mo"),
    D1("1d", "1D", 1440, "1y"),
    ;

    /** How many bars to request, capped by what Yahoo will return for this range. */
    val defaultBars: Int
        get() = when (this) {
            M1, M5 -> 400
            M15 -> 300
            M30 -> 250
            H1 -> 200
            D1 -> 250
        }
}

/**
 * Yahoo Finance chart API client.
 *
 * Deliberately dependency-free: plain [HttpURLConnection] + org.json, both of which
 * ship with Android. Retrofit/OkHttp would be nicer but each added library is another
 * thing that can break the build for a sideloaded APK.
 */
class YahooCandleSource(
    private val userAgent: String = DEFAULT_UA,
) : CandleSource {

    override suspend fun fetchCandles(symbol: String, interval: Interval, bars: Int): List<Candle> {
        val encoded = symbol.replace("=", "%3D")
        val url = "https://query1.finance.yahoo.com/v8/finance/chart/$encoded" +
            "?interval=${interval.yahooCode}&range=${interval.range}&includePrePost=false"

        val body = httpGet(url)
        return parseCandles(body)
    }

    override suspend fun fetchQuote(symbol: String): Quote? {
        val encoded = symbol.replace("=", "%3D")
        val url = "https://query1.finance.yahoo.com/v8/finance/chart/$encoded?interval=1m&range=1d"
        val body = runCatching { httpGet(url) }.getOrNull() ?: return null
        return runCatching { parseQuote(symbol, body) }.getOrNull()
    }

    /** Parses the chart payload. Visible for testing. */
    fun parseCandles(body: String): List<Candle> {
        val root = JSONObject(body)
        val chart = root.optJSONObject("chart") ?: return emptyList()
        // `error` is JSON null on success and an OBJECT on failure. optJSONObject
        // returns null for both, so test for the object explicitly and only then throw.
        if (!chart.isNull("error")) {
            val err = chart.optJSONObject("error")
            throw IOException("Yahoo error: ${err?.optString("description").orEmpty()}")
        }
        val results = chart.optJSONArray("result") ?: return emptyList()
        if (results.length() == 0) return emptyList()

        val result = results.getJSONObject(0)
        val timestamps = result.optJSONArray("timestamp") ?: return emptyList()
        val indicators = result.optJSONObject("indicators") ?: return emptyList()
        val quotes = indicators.optJSONArray("quote") ?: return emptyList()
        if (quotes.length() == 0) return emptyList()
        val q = quotes.getJSONObject(0)

        val opens = q.optJSONArray("open")
        val highs = q.optJSONArray("high")
        val lows = q.optJSONArray("low")
        val closes = q.optJSONArray("close")
        val volumes = q.optJSONArray("volume")

        val out = ArrayList<Candle>(timestamps.length())
        for (i in 0 until timestamps.length()) {
            // Yahoo pads non-trading slots with nulls; skip any incomplete bar.
            val o = opens?.optDoubleOrNull(i) ?: continue
            val h = highs?.optDoubleOrNull(i) ?: continue
            val l = lows?.optDoubleOrNull(i) ?: continue
            val c = closes?.optDoubleOrNull(i) ?: continue
            if (o <= 0.0 || h <= 0.0 || l <= 0.0 || c <= 0.0) continue
            out.add(
                Candle(
                    time = timestamps.getLong(i) * 1000L,
                    open = o,
                    high = h,
                    low = l,
                    close = c,
                    volume = volumes?.optDoubleOrNull(i) ?: 0.0,
                ),
            )
        }
        return out
    }

    fun parseQuote(symbol: String, body: String): Quote? {
        val root = JSONObject(body)
        val chart = root.optJSONObject("chart") ?: return null
        val results = chart.optJSONArray("result") ?: return null
        if (results.length() == 0) return null
        val result = results.getJSONObject(0)
        val meta = result.optJSONObject("meta") ?: return null

        val price = meta.optDouble("regularMarketPrice", Double.NaN)
        if (price.isNaN()) return null
        val prev = meta.optDouble("chartPreviousClose", meta.optDouble("previousClose", price))
        val pct = if (prev > 0) (price - prev) / prev * 100.0 else 0.0

        return Quote(
            symbol = symbol,
            price = price,
            previousClose = prev,
            changePercent = pct,
            marketTime = meta.optLong("regularMarketTime", 0L) * 1000L,
            delayed = true,
        )
    }

    private fun httpGet(url: String): String {
        val conn = (URL(url).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = TimeUnit.SECONDS.toMillis(15).toInt()
            readTimeout = TimeUnit.SECONDS.toMillis(20).toInt()
            setRequestProperty("User-Agent", userAgent)
            setRequestProperty("Accept", "application/json")
            instanceFollowRedirects = true
        }
        try {
            val code = conn.responseCode
            if (code !in 200..299) {
                val err = conn.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
                throw IOException("HTTP $code from Yahoo: ${err.take(200)}")
            }
            return conn.inputStream.bufferedReader().use { it.readText() }
        } finally {
            conn.disconnect()
        }
    }

    private fun org.json.JSONArray.optDoubleOrNull(i: Int): Double? {
        if (isNull(i)) return null
        val v = optDouble(i, Double.NaN)
        return if (v.isNaN()) null else v
    }

    companion object {
        // Yahoo rejects the default Java user agent.
        const val DEFAULT_UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
    }
}
