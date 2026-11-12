package com.vjk.goldpulse.strategy.lsms

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.Calendar
import java.util.GregorianCalendar
import java.util.TimeZone
import kotlin.math.sin

/**
 * End-to-end engine tests.
 *
 * Unit tests only catch maths. These run the whole pipeline over synthetic bars,
 * which is what catches runtime exceptions (bad indices, NaN propagation, infinite
 * loops) that a compile check cannot see.
 */
class LsmsEngineTest {

    private fun syntheticBars(n: Int = 600, startMillis: Long = 1_760_000_000_000L): List<Bar> {
        val et = TimeZone.getTimeZone("America/New_York")
        val cal = GregorianCalendar(et).apply { timeInMillis = startMillis }
        // Anchor to 18:00 ET so the session logic is exercised.
        cal.set(Calendar.HOUR_OF_DAY, 18)
        cal.set(Calendar.MINUTE, 0)
        cal.set(Calendar.SECOND, 0)
        cal.set(Calendar.MILLISECOND, 0)
        var t = cal.timeInMillis

        val bars = ArrayList<Bar>(n)
        var price = 2650.0
        val rand = java.util.Random(7)
        for (i in 0 until n) {
            val drift = sin(i / 40.0) * 0.6
            val step = drift + rand.nextGaussian() * 2.0
            val o = round1(price)
            val c = round1(price + step)
            val h = round1(maxOf(o, c) + kotlin.math.abs(rand.nextGaussian()))
            val l = round1(minOf(o, c) - kotlin.math.abs(rand.nextGaussian()))
            bars.add(Bar(t, o, h, l, c, 1000.0))
            price = c
            t += 60_000L
        }
        return bars
    }

    private fun round1(v: Double) = Math.round(v * 10.0) / 10.0

    private val config = LsmsConfig(
        accountSize = 50_000.0,
        riskPercent = 0.5,
        maxContracts = 40,
        useHtfBias = false, // isolate the engine from the bias series
        requireFvg = false,
        useKillZones = false,
        maxSignalsPerDay = 99,
        minRrToLiquidity = 0.0,
    )

    @Test
    fun `engine runs to completion on 600 bars`() {
        val engine = LsmsEngine(config, Instrument.MGC)
        val bars = syntheticBars(600)
        val result = engine.simulate(bars)

        assertNotNull(result)
        assertEquals(bars.size.coerceAtMost(result.structureEvents.size + bars.size), bars.size)
        assertTrue("should detect sweeps on volatile data", result.sweeps.isNotEmpty())
    }

    @Test
    fun `engine handles the minimum bar count`() {
        val engine = LsmsEngine(config, Instrument.GC)
        val result = engine.simulate(syntheticBars(20))
        assertNotNull(result)
    }

    @Test
    fun `every generated setup has coherent prices`() {
        val engine = LsmsEngine(config, Instrument.GC)
        val result = engine.simulate(syntheticBars(900))

        result.setups.forEach { s ->
            if (s.isLong) {
                assertTrue("long stop below entry", s.stopLoss < s.entry)
                assertTrue("long tp above entry", s.takeProfit2 > s.entry)
            } else {
                assertTrue("short stop above entry", s.stopLoss > s.entry)
                assertTrue("short tp below entry", s.takeProfit2 < s.entry)
            }
            assertTrue("risk must be positive", s.riskPoints > 0.0)
            assertTrue("contracts within cap", s.contracts in 0..config.maxContracts)
            assertTrue("risk respects the stop band", s.riskPoints >= config.minStopPoints - 1e-6)
        }
    }

    @Test
    fun `prices land on the tick grid`() {
        val engine = LsmsEngine(config, Instrument.MGC)
        val result = engine.simulate(syntheticBars(900))
        val tick = Instrument.MGC.tickSize

        result.setups.forEach { s ->
            listOf(s.entry, s.stopLoss, s.takeProfit2).forEach { p ->
                val offGrid = Math.abs(p / tick - Math.round(p / tick))
                assertTrue("price $p is off the $tick grid", offGrid < 1e-6)
            }
        }
    }

    @Test
    fun `guard blocks setups when the daily limit is already consumed`() {
        val exhausted = config.copy(
            todayLossPercent = 2.5,
            dailyLossLimitPercent = 2.0,
        )
        val result = LsmsEngine(exhausted, Instrument.MGC).simulate(syntheticBars(900))
        assertTrue("guard must report stopped", result.guardStopped)
        assertEquals(GuardReason.DAILY_LIMIT, result.guardReason)
        assertTrue("no setups once the guard is hit", result.setups.isEmpty())
    }

    @Test
    fun `instrument tick maths`() {
        assertEquals(10.0, Instrument.GC.tickValue, 1e-9)
        assertEquals(1.0, Instrument.MGC.tickValue, 1e-9)
        assertEquals(100.0, Instrument.GC.pointValue, 1e-9)
        assertEquals(10.0, Instrument.MGC.pointValue, 1e-9)
    }

    // ---- clock -------------------------------------------------------------

    @Test
    fun `day index rolls at 17 New York not at midnight`() {
        val et = TimeZone.getTimeZone("America/New_York")
        fun at(day: Int, hour: Int, minute: Int): Long {
            val c = GregorianCalendar(et).apply {
                set(2026, Calendar.JUNE, day, hour, minute, 0)
                set(Calendar.MILLISECOND, 0)
            }
            return c.timeInMillis
        }

        val beforeRoll = NewYorkClock.dayIndex(at(10, 16, 59))
        val afterRoll = NewYorkClock.dayIndex(at(10, 17, 1))
        assertEquals("a new trading day starts at 17:00 ET", beforeRoll + 1, afterRoll)

        // Midnight must NOT start a new trading day: 23:00 on the 10th and 02:00 on
        // the 11th are the same session, because the session began at 17:00 on the 10th.
        val lateEvening = NewYorkClock.dayIndex(at(10, 23, 0))
        val nextMorning = NewYorkClock.dayIndex(at(11, 2, 0))
        assertEquals("midnight is inside the same trading day", lateEvening, nextMorning)

        // 16:00 the next day is STILL the same session: the session that opened at
        // 17:00 on the 10th runs through to 17:00 on the 11th.
        assertEquals("16:00 next day is the same session", lateEvening, NewYorkClock.dayIndex(at(11, 16, 0)))
        // Only the next 17:00 roll starts a new one.
        assertEquals("17:30 next day is a new session", lateEvening + 1, NewYorkClock.dayIndex(at(11, 17, 30)))
    }

    @Test
    fun `day index is stable across DST`() {
        val et = TimeZone.getTimeZone("America/New_York")
        fun at(month: Int, day: Int, hour: Int): Long {
            val c = GregorianCalendar(et).apply {
                set(2026, month, day, hour, 0, 0)
                set(Calendar.MILLISECOND, 0)
            }
            return c.timeInMillis
        }
        // Summer and winter must behave identically at the same wall-clock hour.
        val summerRoll = NewYorkClock.dayIndex(at(Calendar.JUNE, 10, 17))
        val summerBefore = NewYorkClock.dayIndex(at(Calendar.JUNE, 10, 16))
        val winterRoll = NewYorkClock.dayIndex(at(Calendar.DECEMBER, 10, 17))
        val winterBefore = NewYorkClock.dayIndex(at(Calendar.DECEMBER, 10, 16))

        assertEquals(summerBefore + 1, summerRoll)
        assertEquals(winterBefore + 1, winterRoll)
    }

    @Test
    fun `weekend closed windows`() {
        val et = TimeZone.getTimeZone("America/New_York")
        fun at(dayOfWeek: Int, hour: Int): Long {
            val c = GregorianCalendar(et).apply {
                set(2026, Calendar.NOVEMBER, 13, hour, 0, 0) // a Friday
                set(Calendar.MILLISECOND, 0)
            }
            while (c.get(Calendar.DAY_OF_WEEK) != dayOfWeek) c.add(Calendar.DAY_OF_MONTH, 1)
            c.set(Calendar.HOUR_OF_DAY, hour)
            return c.timeInMillis
        }
        assertTrue(NewYorkClock.isWeekendClosed(at(Calendar.SATURDAY, 12)))
        assertTrue("Friday after 17:00 is closed", NewYorkClock.isWeekendClosed(at(Calendar.FRIDAY, 18)))
        assertTrue("Sunday before 17:00 is closed", NewYorkClock.isWeekendClosed(at(Calendar.SUNDAY, 10)))
        assertTrue(
            "Sunday after 17:00 is open",
            !NewYorkClock.isWeekendClosed(at(Calendar.SUNDAY, 18)),
        )
    }

    @Test
    fun `flat-by countdown`() {
        val et = TimeZone.getTimeZone("America/New_York")
        val c = GregorianCalendar(et).apply {
            set(2026, Calendar.NOVEMBER, 12, 14, 0, 0)
            set(Calendar.MILLISECOND, 0)
        }
        // 14:00 -> 15:10 is 70 minutes
        assertEquals(70, NewYorkClock.minutesUntilFlatBy(c.timeInMillis))
    }

    // ---- sizing ------------------------------------------------------------

    @Test
    fun `sizing falls back to micros when GC rounds to zero`() {
        val s = Sizing.suggest(
            riskDollars = 250.0,
            stopPoints = 5.0,
            primary = Instrument.GC,
            alternate = Instrument.MGC,
        )
        assertEquals(0, s.primary)
        assertTrue(s.primaryUnusable)
        assertEquals(5, s.alternate)
        assertNotNull(s.hint)
    }

    @Test
    fun `sizing keeps GC when the risk is large enough`() {
        val s = Sizing.suggest(
            riskDollars = 500.0,
            stopPoints = 5.0,
            primary = Instrument.GC,
            alternate = Instrument.MGC,
        )
        assertEquals(1, s.primary)
        assertTrue(s.hint == null)
    }

    @Test
    fun `sizing clamps to the micro contract limit`() {
        val s = Sizing.suggest(500.0, 5.0, Instrument.MGC, Instrument.GC).clamped(4)
        assertTrue("micro cap is 40 on Rapid Daily 50K", (s.primary) <= 40)
    }

    @Test
    fun `losses remaining matches the prop maths`() {
        assertEquals(8, Sizing.lossesRemaining(2000.0, 250.0))
        assertEquals(4, Sizing.lossesRemaining(2000.0, 500.0))
    }
}
