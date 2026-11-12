package com.vjk.goldpulse.strategy.lsms

/**
 * Contract specification for an instrument the LSMS engine can run on.
 *
 * The original Pine Script assumed FX (contract 100_000, pip 0.0001). Gold futures
 * need completely different numbers, so every value that the script hardcoded is
 * now a property of the instrument instead.
 *
 * Reference: CME COMEX gold futures.
 */
data class Instrument(
    /** Symbol as the data feed reports it, e.g. "GC" or "MGC". */
    val symbol: String,
    /** Full contract multiplier in troy ounces (100 for GC, 10 for MGC). */
    val contractSize: Double,
    /** Minimum price increment (0.10 for both GC and MGC). */
    val tickSize: Double,
    /**
     * Dollar value of one full price point (1.00) move.
     * GC: 100 oz x $1 = $100. MGC: 10 oz x $1 = $10.
     */
    val pointValue: Double,
) {
    /** Dollar value of a single tick. GC = $10, MGC = $1. */
    val tickValue: Double get() = pointValue * tickSize

    /** Round a price to the nearest valid tick. */
    fun roundToTick(price: Double): Double = Math.round(price / tickSize) * tickSize

    /** Number of ticks between two prices. */
    fun ticksBetween(from: Double, to: Double): Double = Math.abs(to - from) / tickSize

    companion object {
        /** COMEX Gold, full contract. $100 per point, $10 per tick. */
        val GC = Instrument(
            symbol = "GC",
            contractSize = 100.0,
            tickSize = 0.10,
            pointValue = 100.0,
        )

        /** Micro Gold. $10 per point, $1 per tick. */
        val MGC = Instrument(
            symbol = "MGC",
            contractSize = 10.0,
            tickSize = 0.10,
            pointValue = 10.0,
        )
    }
}
