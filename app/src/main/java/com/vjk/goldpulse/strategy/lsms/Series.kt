package com.vjk.goldpulse.strategy.lsms

/**
 * Pine-Script-exact technical primitives.
 *
 * These exist as a separate file because getting the smoothing wrong is the single
 * biggest source of "my app disagrees with TradingView" bugs. Every function here
 * documents which Pine function it reproduces and the exact recurrence used.
 *
 * Rules followed:
 *  - Series are NaN-padded, mirroring Pine's `na` for warm-up bars.
 *  - Recurrences are `adjust = false` style (recursive), never windowed EWM.
 *  - RMA (Wilder) is seeded with a simple average, exactly like Pine's `ta.rma`.
 */
object Series {

    const val NA: Double = Double.NaN

    fun isNa(v: Double): Boolean = v.isNaN()

    /**
     * Pine `ta.sma(src, len)`.
     * Returns NaN for the first len-1 bars.
     */
    fun sma(src: DoubleArray, len: Int): DoubleArray {
        require(len >= 1) { "len must be >= 1" }
        val out = DoubleArray(src.size) { NA }
        if (src.size < len) return out
        var sum = 0.0
        for (i in src.indices) {
            sum += src[i]
            if (i >= len) sum -= src[i - len]
            if (i >= len - 1) out[i] = sum / len
        }
        return out
    }

    /**
     * Pine `ta.ema(src, len)`.
     * alpha = 2 / (len + 1). Seeded with the SMA of the first len bars, which is what
     * Pine does; seeding with src[0] instead produces a visible offset for hundreds
     * of bars.
     */
    fun ema(src: DoubleArray, len: Int): DoubleArray {
        require(len >= 1) { "len must be >= 1" }
        val out = DoubleArray(src.size) { NA }
        if (src.size < len) return out
        val alpha = 2.0 / (len + 1.0)
        var seed = 0.0
        for (i in 0 until len) seed += src[i]
        var prev = seed / len
        out[len - 1] = prev
        for (i in len until src.size) {
            prev = alpha * src[i] + (1 - alpha) * prev
            out[i] = prev
        }
        return out
    }

    /**
     * Pine `ta.rma(src, len)` — Wilder's smoothing, a.k.a. SMMA / RMA.
     * alpha = 1 / len, seeded with the SMA of the first len bars.
     *
     * This is the function RSI and ATR are built on. Using `sma` or `ema` here
     * instead is the classic porting bug that makes RSI disagree with TradingView.
     */
    fun rma(src: DoubleArray, len: Int): DoubleArray {
        require(len >= 1) { "len must be >= 1" }
        val out = DoubleArray(src.size) { NA }
        if (src.size < len) return out
        var seed = 0.0
        for (i in 0 until len) seed += src[i]
        var prev = seed / len
        out[len - 1] = prev
        for (i in len until src.size) {
            prev = (prev * (len - 1) + src[i]) / len
            out[i] = prev
        }
        return out
    }

    /** Pine `ta.change(src)` — first difference, NaN on bar 0. */
    fun change(src: DoubleArray): DoubleArray =
        DoubleArray(src.size) { i -> if (i == 0) NA else src[i] - src[i - 1] }

    /**
     * Pine `ta.rsi(src, len)`.
     * Wilder's RSI: RMA of gains over RMA of losses. Bars where the average loss is
     * zero yield 100, which matches Pine's behaviour.
     */
    fun rsi(src: DoubleArray, len: Int = 14): DoubleArray {
        val gains = DoubleArray(src.size) { i -> if (i == 0) 0.0 else maxOf(src[i] - src[i - 1], 0.0) }
        val losses = DoubleArray(src.size) { i -> if (i == 0) 0.0 else maxOf(src[i - 1] - src[i], 0.0) }
        val avgGain = rma(gains, len)
        val avgLoss = rma(losses, len)
        return DoubleArray(src.size) { i ->
            val g = avgGain[i]
            val l = avgLoss[i]
            when {
                isNa(g) || isNa(l) -> NA
                l == 0.0 && g == 0.0 -> 50.0
                l == 0.0 -> 100.0
                else -> {
                    val rs = g / l
                    100.0 - 100.0 / (1.0 + rs)
                }
            }
        }
    }

    /**
     * Pine `ta.tr` (true range, `handle_na = true`).
     * max(high - low, |high - prevClose|, |low - prevClose|). Bar 0 = high - low.
     */
    fun trueRange(high: DoubleArray, low: DoubleArray, close: DoubleArray): DoubleArray =
        DoubleArray(high.size) { i ->
            if (i == 0) high[i] - low[i]
            else maxOf(high[i] - low[i], Math.abs(high[i] - close[i - 1]), Math.abs(low[i] - close[i - 1]))
        }

    /** Pine `ta.atr(len)` = `ta.rma(ta.tr, len)`. */
    fun atr(high: DoubleArray, low: DoubleArray, close: DoubleArray, len: Int = 14): DoubleArray =
        rma(trueRange(high, low, close), len)

    /**
     * Pine `ta.pivothigh(high, left, right)`.
     * A pivot is CONFIRMED `right` bars later, so out[i] is the pivot value that
     * becomes known at bar i (referring to bar i - right), or NaN.
     */
    fun pivotHigh(high: DoubleArray, left: Int, right: Int): DoubleArray {
        val out = DoubleArray(high.size) { NA }
        for (i in (left + right) until high.size) {
            val pivotIdx = i - right
            val v = high[pivotIdx]
            var isPivot = true
            for (j in (pivotIdx - left)..(pivotIdx + right)) {
                if (j == pivotIdx) continue
                if (high[j] >= v) { isPivot = false; break }
            }
            if (isPivot) out[i] = v
        }
        return out
    }

    /** Pine `ta.pivotlow(low, left, right)`. */
    fun pivotLow(low: DoubleArray, left: Int, right: Int): DoubleArray {
        val out = DoubleArray(low.size) { NA }
        for (i in (left + right) until low.size) {
            val pivotIdx = i - right
            val v = low[pivotIdx]
            var isPivot = true
            for (j in (pivotIdx - left)..(pivotIdx + right)) {
                if (j == pivotIdx) continue
                if (low[j] <= v) { isPivot = false; break }
            }
            if (isPivot) out[i] = v
        }
        return out
    }

    /** Pine `ta.crossover(a, b)`: a was <= b and is now > b. */
    fun crossover(a: DoubleArray, b: DoubleArray): BooleanArray =
        BooleanArray(a.size) { i ->
            i > 0 && !isNa(a[i]) && !isNa(b[i]) && !isNa(a[i - 1]) && !isNa(b[i - 1]) &&
                a[i - 1] <= b[i - 1] && a[i] > b[i]
        }

    /** Pine `ta.crossunder(a, b)`. */
    fun crossunder(a: DoubleArray, b: DoubleArray): BooleanArray =
        BooleanArray(a.size) { i ->
            i > 0 && !isNa(a[i]) && !isNa(b[i]) && !isNa(a[i - 1]) && !isNa(b[i - 1]) &&
                a[i - 1] >= b[i - 1] && a[i] < b[i]
        }

    /** Pine `nz(x)` for a single value. */
    fun nz(v: Double, replacement: Double = 0.0): Double = if (isNa(v)) replacement else v
}
