package com.vjk.goldpulse.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.JUnit4

/**
 * Parser tests against payloads shaped exactly like Yahoo's chart response.
 *
 * A parser bug here does not crash the app — it shows an empty chart, which is
 * indistinguishable from "market closed". That makes it worth pinning down.
 */
@RunWith(JUnit4::class)
class YahooCandleSourceTest {

    private val source = YahooCandleSource()

    /** Real response shape, trimmed to three bars. */
    private val payload = """
    {
      "chart": {
        "result": [
          {
            "meta": {
              "currency": "USD",
              "symbol": "GC=F",
              "exchangeName": "CMX",
              "regularMarketPrice": 2701.3,
              "chartPreviousClose": 2690.0,
              "regularMarketTime": 1762995600
            },
            "timestamp": [1762995600, 1762995660, 1762995720],
            "indicators": {
              "quote": [
                {
                  "open":   [2695.0, 2698.4, null],
                  "high":   [2699.5, 2702.1, null],
                  "low":    [2694.2, 2697.0, null],
                  "close":  [2698.4, 2701.3, null],
                  "volume": [812, 640, null]
                }
              ]
            }
          }
        ],
        "error": null
      }
    }
    """.trimIndent()

    @Test
    fun `parses complete bars and skips padding`() {
        val candles = source.parseCandles(payload)
        assertEquals("the null-padded third slot must be dropped", 2, candles.size)

        val first = candles[0]
        assertEquals(2695.0, first.open, 1e-9)
        assertEquals(2699.5, first.high, 1e-9)
        assertEquals(2694.2, first.low, 1e-9)
        assertEquals(2698.4, first.close, 1e-9)
        assertEquals(812.0, first.volume, 1e-9)
    }

    @Test
    fun `timestamps convert from seconds to milliseconds`() {
        val candles = source.parseCandles(payload)
        assertEquals(1762995600000L, candles[0].time)
        assertEquals(60_000L, candles[1].time - candles[0].time)
    }

    @Test
    fun `quote carries price and percent change`() {
        val quote = source.parseQuote("GC=F", payload)
        assertNotNull(quote)
        quote!!
        assertEquals(2701.3, quote.price, 1e-9)
        assertEquals(2690.0, quote.previousClose, 1e-9)
        assertEquals((2701.3 - 2690.0) / 2690.0 * 100.0, quote.changePercent, 1e-9)
        assertEquals(1762995600000L, quote.marketTime)
        assertTrue("Yahoo is delayed", quote.delayed)
    }

    @Test
    fun `empty result set yields no candles`() {
        val empty = """{"chart":{"result":[],"error":null}}"""
        assertTrue(source.parseCandles(empty).isEmpty())
        assertNull(source.parseQuote("GC=F", empty))
    }

    @Test
    fun `a null result without an error yields no candles`() {
        val nullResult = """{"chart":{"result":null,"error":null}}"""
        assertTrue(source.parseCandles(nullResult).isEmpty())
    }

    @Test
    fun `an error object is surfaced as an exception`() {
        // This is what Yahoo actually returns for an unknown symbol, and the message
        // must reach the UI rather than silently rendering an empty chart.
        val badSymbol = """{"chart":{"result":null,"error":{"code":"Not Found","description":"No data found, symbol may be delisted"}}}"""
        val ex = try {
            source.parseCandles(badSymbol)
            null
        } catch (e: java.io.IOException) {
            e
        }
        assertNotNull("an error payload must throw", ex)
        assertTrue(
            "the description must survive to the message: ${ex!!.message}",
            ex.message!!.contains("No data found"),
        )
    }

    @Test
    fun `zero and negative prices are discarded`() {
        val bad = """
        {"chart":{"result":[{
          "timestamp":[1,2],
          "indicators":{"quote":[{
            "open":[0.0, 100.0],"high":[0.0, 101.0],"low":[0.0, 99.0],
            "close":[0.0, 100.5],"volume":[1, 2]
          }]}
        }],"error":null}}
        """.trimIndent()
        val candles = source.parseCandles(bad)
        assertEquals("a zero-price bar must be dropped", 1, candles.size)
        assertEquals(100.5, candles[0].close, 1e-9)
    }

    @Test
    fun `missing volume defaults to zero`() {
        val noVolume = """
        {"chart":{"result":[{
          "timestamp":[1],
          "indicators":{"quote":[{
            "open":[100.0],"high":[101.0],"low":[99.0],"close":[100.5]
          }]}
        }],"error":null}}
        """.trimIndent()
        val candles = source.parseCandles(noVolume)
        assertEquals(1, candles.size)
        assertEquals(0.0, candles[0].volume, 1e-9)
    }

    @Test
    fun `interval metadata is sane`() {
        assertEquals("15m", Interval.M15.yahooCode)
        assertEquals(5, Interval.M5.minutes)
        assertEquals(1440, Interval.D1.minutes)
        assertTrue(Interval.M15.durationMs() == 15 * 60_000L)
    }

    @Test
    fun `every interval has a range and bar count`() {
        Interval.entries.forEach { i ->
            assertTrue("${i.name} needs a non-empty range", i.range.isNotBlank())
            assertTrue("${i.name} needs bars", i.defaultBars > 50)
        }
    }
}

/** Local helper so the test can assert on bar spacing without a formatter. */
private fun Interval.durationMs(): Long = minutes * 60_000L
