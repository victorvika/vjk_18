package com.vjk.goldpulse.strategy.lsms

/**
 * Stand-in for Pine's `request.security(sym, tf, close[1], lookahead_on)`.
 *
 * Pine's `close[1]` on a higher timeframe means "the last COMPLETED higher-timeframe
 * bar". Reproducing that in Kotlin is a two-step job:
 *   1. Resample the base bars into HTF bars.
 *   2. For each base bar, read the HTF value from the most recent HTF bar that had
 *      already closed at that point in time.
 *
 * Reading the HTF bar that is still forming is the classic lookahead bug: it makes
 * backtests look great and live results terrible.
 */
object HtfBias {

    /**
     * Returns +1 when the HTF close is above its EMA, -1 when below, 0 while the
     * higher timeframe has not warmed up yet.
     *
     * @param bars base-timeframe bars
     * @param minutesPerBar HTF period in minutes (240 = 4H)
     * @param emaLength EMA length applied on the HTF closes
     * @return one bias value per base bar, aligned by index
     */
    fun series(
        bars: List<Bar>,
        minutesPerBar: Int,
        emaLength: Int = 50,
    ): IntArray {
        if (bars.isEmpty()) return IntArray(0)
        val periodMillis = minutesPerBar * 60_000L

        // --- 1. bucket base bars into HTF bars -----------------------------
        val bucketIds = LongArray(bars.size) { bars[it].time / periodMillis }
        val htfCloses = ArrayList<Double>()
        val htfBucket = ArrayList<Long>()
        var currentBucket = Long.MIN_VALUE
        var runningClose = 0.0
        for (i in bars.indices) {
            val b = bucketIds[i]
            if (b != currentBucket) {
                if (currentBucket != Long.MIN_VALUE) {
                    htfBucket += currentBucket
                    htfCloses += runningClose
                }
                currentBucket = b
            }
            runningClose = bars[i].close
        }
        if (currentBucket != Long.MIN_VALUE) {
            htfBucket += currentBucket
            htfCloses += runningClose
        }
        if (htfCloses.size < emaLength + 1) return IntArray(bars.size)

        // --- 2. EMA on the HTF closes --------------------------------------
        val closes = htfCloses.toDoubleArray()
        val ema = Series.ema(closes, emaLength)

        // --- 3. map each base bar to the last CLOSED HTF bar ---------------
        // The HTF bar at index k is complete once the base bar enters bucket k+1.
        // So a base bar in bucket k may only see HTF index k-1.
        val out = IntArray(bars.size)
        val bucketArr = htfBucket.toLongArray()
        for (i in bars.indices) {
            // Binary search: first HTF bucket >= this base bar's bucket. Everything
            // before it has already closed, so index-1 is the last completed HTF bar.
            var lo = 0
            var hi = bucketArr.size
            while (lo < hi) {
                val mid = (lo + hi) ushr 1
                if (bucketArr[mid] < bucketIds[i]) lo = mid + 1 else hi = mid
            }
            val closedIdx = lo - 1
            if (closedIdx <= 0 || closedIdx >= closes.size) { out[i] = 0; continue }
            val c = closes[closedIdx]
            val e = ema[closedIdx]
            out[i] = when {
                c.isNaN() || e.isNaN() -> 0
                c > e -> 1
                c < e -> -1
                else -> 0
            }
        }
        return out
    }
}
