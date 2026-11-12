package com.vjk.goldpulse.strategy.lsms

/** A single OHLCV bar. `time` is epoch milliseconds at bar OPEN. */
data class Bar(
    val time: Long,
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double,
    val volume: Double = 0.0,
)

/**
 * Columnar view of bars — the indicator code works on DoubleArrays so it stays
 * allocation-light and can be reused for incremental updates.
 */
class BarSeries(val bars: List<Bar>) {
    val size: Int get() = bars.size
    val open: DoubleArray = DoubleArray(bars.size) { bars[it].open }
    val high: DoubleArray = DoubleArray(bars.size) { bars[it].high }
    val low: DoubleArray = DoubleArray(bars.size) { bars[it].low }
    val close: DoubleArray = DoubleArray(bars.size) { bars[it].close }
    val volume: DoubleArray = DoubleArray(bars.size) { bars[it].volume }
    val time: LongArray = LongArray(bars.size) { bars[it].time }
}

/** Liquidity level side. */
enum class LevelSide { BUY_SIDE, SELL_SIDE }

/** What kind of liquidity a level represents. */
enum class LevelKind {
    SWING_HIGH,
    SWING_LOW,
    EQUAL_HIGHS,
    EQUAL_LOWS,
    PREV_DAY_HIGH,
    PREV_DAY_LOW,
    ASIA_HIGH,
    ASIA_LOW,
    ;

    /** Key levels qualify a setup; plain swings do not. */
    val isKey: Boolean
        get() = this != SWING_HIGH && this != SWING_LOW
}

/** A tracked liquidity level. */
data class LiquidityLevel(
    val price: Double,
    val side: LevelSide,
    val kind: LevelKind,
    val createdBar: Int,
    /** Bar at which price first closed beyond the level, or -1 while intact. */
    val closedBeyondBar: Int = -1,
    /** Overbought/oversold turning point, drawn thicker. */
    val rsiExtreme: Boolean = false,
)

/** A fair value gap. */
data class Fvg(
    val top: Double,
    val bottom: Double,
    val bar: Int,
    val bullish: Boolean,
)

/** Market structure state. */
enum class StructureEvent { NONE, BOS_UP, BOS_DOWN, MSS_UP, MSS_DOWN }

/** Trend classification for the dashboard. */
enum class Trend { UPTREND, DOWNTREND, RANGE }

/** A liquidity sweep (grab). */
data class Sweep(
    val bar: Int,
    val side: LevelSide,
    /** Extreme reached by the sweep: the low for sell-side, the high for buy-side. */
    val extreme: Double,
    val levelKind: LevelKind,
    val touchedHtfPoi: Boolean = false,
)

/** A generated trade setup. */
data class Setup(
    val bar: Int,
    val time: Long,
    val isLong: Boolean,
    /** Entry price (limit at the FVG consequent encroachment, or a retest). */
    val entry: Double,
    val stopLoss: Double,
    /** Nearest liquidity target, if one exists. */
    val takeProfit1: Double?,
    /** Fixed-R target. */
    val takeProfit2: Double,
    val riskPoints: Double,
    val riskDollars: Double,
    /** Contracts to trade, already clamped to the contract limit. */
    val contracts: Int,
    /** Reward:risk to the nearest liquidity target (or targetRr when none). */
    val rrToLiquidity: Double,
    /** Entry zone, when the entry came from a fair value gap. */
    val entryZone: Fvg?,
    val levelKind: LevelKind,
    val inKillZone2: Boolean,
)

/** Why a setup candidate was rejected — surfaced in the dashboard. */
sealed interface SkipReason {
    data object OutsideKillZone : SkipReason
    data object MaxSignalsPerDay : SkipReason
    data class RiskGuard(val why: GuardReason) : SkipReason
    data object AgainstHtfBias : SkipReason
    data object NoFvgAfterSweep : SkipReason
    data object WeakDisplacement : SkipReason
    data class StopTooTight(val points: Double) : SkipReason
    data class StopTooWide(val points: Double) : SkipReason
    data class RrTooLiquidity(val rr: Double) : SkipReason
    data object NegativeBucket : SkipReason
    override fun toString(): String = when (this) {
        OutsideKillZone -> "outside kill zone"
        MaxSignalsPerDay -> "max signals per day"
        is RiskGuard -> "risk guard: ${why.label}"
        AgainstHtfBias -> "against HTF bias"
        NoFvgAfterSweep -> "no FVG after sweep"
        WeakDisplacement -> "weak MSS candle"
        is StopTooTight -> "SL too tight ${fmt(points)}pt"
        is StopTooWide -> "SL too wide ${fmt(points)}pt"
        is RrTooLiquidity -> "RR to liquidity ${fmt(rr)}"
        NegativeBucket -> "learned: weak bucket"
    }

    private fun fmt(v: Double): String = String.format("%.1f", v)
}

enum class GuardReason(val label: String) {
    LOSS_COUNT("loss count"),
    DAILY_LIMIT("daily limit"),
    MAX_LIMIT("max loss limit"),
}

/** Buckets used by the simulated-outcome learning stats. */
enum class StatBucket(val label: String) {
    ALL("Sim all (n|win|avgR)"),
    KILL_ZONE_LONDON("Sim KZ1 London"),
    KILL_ZONE_NEW_YORK("Sim KZ2 New York"),
    ASIA_LEVELS("Sim Asia levels"),
    PREV_DAY_LEVELS("Sim PDH / PDL"),
    EQUAL_LEVELS("Sim EQH / EQL"),
    SWINGS("Sim Swings"),
}

/** Running simulation statistics for one bucket. */
data class BucketStat(val count: Int, val wins: Int, val rr: Double) {
    val winRate: Double get() = if (count == 0) 0.0 else wins * 100.0 / count
    /** Expectancy in R. */
    val expectancyR: Double get() = if (count == 0) 0.0 else (wins * rr - (count - wins)) / count

    fun format(): String =
        if (count == 0) "-" else "$count | ${winRate.toInt()}% | ${String.format("%.2f", expectancyR)}R"
}

/** Result of one simulate() pass over history. */
data class LsmsResult(
    val setups: List<Setup>,
    val sweeps: List<Sweep>,
    val structureEvents: List<StructureEvent>,
    val levels: List<LiquidityLevel>,
    val fvg: List<Fvg>,
    val stats: Map<StatBucket, BucketStat>,
    val trend: Trend,
    val phase: String,
    val lastEvent: String,
    val lastSignal: String,
    val lastSkip: SkipReason?,
    val guardStopped: Boolean,
    val guardReason: GuardReason?,
    val htfBias: Int,
    val netRToday: Double,
    val lossesToday: Double,
)
