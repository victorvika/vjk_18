package com.vjk.goldpulse.strategy.lsms

import java.time.LocalDate
import java.time.LocalDateTime
import java.time.ZoneId
import java.time.ZonedDateTime

/**
 * Exchange-time helpers.
 *
 * The Pine script used `dayofmonth(time + 25200000, "America/New_York")` — a fixed
 * offset of 7 hours to push the trading day over the 17:00 New York boundary. That
 * works in summer (EDT, UTC-4) and silently breaks in winter (EST, UTC-5), because
 * 7 hours from UTC is 02:00 EST, not 17:00.
 *
 * Use a real timezone database instead. This matters more for gold futures than for
 * FX because the FundedNext daily reset, the max-loss reset and the Asian-session
 * window are all anchored to New York wall-clock time.
 */
object NewYorkClock {

    val ZONE: ZoneId = ZoneId.of("America/New_York")

    /** Hour at which the trading day rolls over (17:00 ET). */
    const val TRADING_DAY_ROLL_HOUR: Int = 17

    fun minuteOfDay(epochMillis: Long): Int {
        val t = ZonedDateTime.ofInstant(java.time.Instant.ofEpochMilli(epochMillis), ZONE)
        return t.hour * 60 + t.minute
    }

    /**
     * Monotonic trading-day index. Any instant at or after 17:00 ET belongs to the
     * next calendar day's session, so those timestamps are shifted forward one day
     * before taking the epoch day.
     */
    fun dayIndex(epochMillis: Long): Int {
        val t = ZonedDateTime.ofInstant(java.time.Instant.ofEpochMilli(epochMillis), ZONE)
        val shifted: LocalDateTime = if (t.hour >= TRADING_DAY_ROLL_HOUR) {
            t.toLocalDateTime().plusDays(1)
        } else {
            t.toLocalDateTime()
        }
        val date: LocalDate = shifted.toLocalDate()
        return date.toEpochDay().toInt()
    }

    /** True when the CME session is closed (Friday 17:00 ET -> Sunday 17:00 ET). */
    fun isWeekendClosed(epochMillis: Long): Boolean {
        val t = ZonedDateTime.ofInstant(java.time.Instant.ofEpochMilli(epochMillis), ZONE)
        val dow = t.dayOfWeek.value // Monday = 1 ... Sunday = 7
        return when (dow) {
            6 -> true // Saturday, always closed
            5 -> t.hour >= 17 // Friday after the close
            7 -> t.hour < 17 // Sunday before the open
            else -> false
        }
    }

    /**
     * FundedNext requires every position flat by 15:10 ET; the exchange session runs
     * 18:00-17:00 ET. Returns minutes remaining until the flat-by cutoff, or null
     * when the market is closed.
     */
    fun minutesUntilFlatBy(epochMillis: Long): Int? {
        if (isWeekendClosed(epochMillis)) return null
        val t = ZonedDateTime.ofInstant(java.time.Instant.ofEpochMilli(epochMillis), ZONE)
        val nowMin = t.hour * 60 + t.minute
        val flatBy = 15 * 60 + 10
        return if (nowMin < flatBy) flatBy - nowMin else null
    }
}
