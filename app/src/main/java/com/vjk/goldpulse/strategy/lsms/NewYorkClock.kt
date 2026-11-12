package com.vjk.goldpulse.strategy.lsms

import java.util.Calendar
import java.util.GregorianCalendar
import java.util.TimeZone

/**
 * Exchange-time helpers.
 *
 * The Pine script used `dayofmonth(time + 25200000, "America/New_York")` — a fixed
 * 7-hour offset to push the trading day over the 17:00 New York boundary. That works
 * in summer (EDT, UTC-4) and silently breaks in winter (EST, UTC-5), because 7 hours
 * from UTC is 02:00 EST, not 17:00.
 *
 * This uses a real timezone database instead. It deliberately sticks to
 * [java.util.Calendar] rather than `java.time`: the app ships with minSdk 24 and
 * `java.time` only exists from API 26, so using it would crash with
 * NoClassDefFoundError on Android 7 devices. `Calendar` with a TimeZone id honours
 * DST on every API level.
 */
object NewYorkClock {

    val ZONE: TimeZone = TimeZone.getTimeZone("America/New_York")

    /** Hour at which the trading day rolls over (17:00 ET). */
    const val TRADING_DAY_ROLL_HOUR: Int = 17

    /** FundedNext requires every position flat by 15:10 ET. */
    const val FLAT_BY_HOUR: Int = 15
    const val FLAT_BY_MINUTE: Int = 10

    private fun calendarAt(epochMillis: Long): Calendar =
        GregorianCalendar(ZONE).apply { timeInMillis = epochMillis }

    fun minuteOfDay(epochMillis: Long): Int {
        val c = calendarAt(epochMillis)
        return c.get(Calendar.HOUR_OF_DAY) * 60 + c.get(Calendar.MINUTE)
    }

    /**
     * Monotonic trading-day index. Any instant at or after 17:00 ET belongs to the
     * next calendar day's session, so those timestamps are shifted forward one day
     * before the day number is taken.
     */
    fun dayIndex(epochMillis: Long): Int {
        val c = calendarAt(epochMillis)
        if (c.get(Calendar.HOUR_OF_DAY) >= TRADING_DAY_ROLL_HOUR) {
            c.add(Calendar.DAY_OF_MONTH, 1)
        }
        // A stable integer per calendar day, independent of month lengths.
        val year = c.get(Calendar.YEAR)
        val dayOfYear = c.get(Calendar.DAY_OF_YEAR)
        return year * 400 + dayOfYear
    }

    /** True when the CME session is closed (Friday 17:00 ET -> Sunday 17:00 ET). */
    fun isWeekendClosed(epochMillis: Long): Boolean {
        val c = calendarAt(epochMillis)
        val hour = c.get(Calendar.HOUR_OF_DAY)
        return when (c.get(Calendar.DAY_OF_WEEK)) {
            Calendar.SATURDAY -> true
            Calendar.FRIDAY -> hour >= TRADING_DAY_ROLL_HOUR
            Calendar.SUNDAY -> hour < TRADING_DAY_ROLL_HOUR
            else -> false
        }
    }

    /**
     * Minutes remaining until the 15:10 ET flat-by cutoff, or null when the cutoff
     * has already passed or the market is closed.
     */
    fun minutesUntilFlatBy(epochMillis: Long): Int? {
        if (isWeekendClosed(epochMillis)) return null
        val now = minuteOfDay(epochMillis)
        val flatBy = FLAT_BY_HOUR * 60 + FLAT_BY_MINUTE
        return if (now < flatBy) flatBy - now else null
    }
}
