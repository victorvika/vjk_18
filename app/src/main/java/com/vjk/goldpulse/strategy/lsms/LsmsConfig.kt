package com.vjk.goldpulse.strategy.lsms

/**
 * All tunables for the LSMS engine.
 *
 * Mirrors the Pine `input.*` declarations one-for-one so the app and TradingView can
 * be kept in sync, but instrument-specific constants (pip size, contract size) are
 * gone: those live on [Instrument] now.
 *
 * Defaults are retuned for GC/MGC on a prop-firm account, not for EURUSD.
 * See LSMS_PORT_NOTES.md for why each default changed.
 */
data class LsmsConfig(
    // ---- Market structure -------------------------------------------------
    val pivotLength: Int = 2,
    val showStructure: Boolean = true,
    val signalMode: SignalMode = SignalMode.MSS_ONLY,
    val showPullbacks: Boolean = false,

    // ---- Liquidity --------------------------------------------------------
    val showSwings: Boolean = true,
    val thickenOnRsiExtremes: Boolean = true,
    /** EQH/EQL tolerance as a multiple of ATR. */
    val equalLevelTolerance: Double = 0.25,
    val showPreviousDay: Boolean = true,
    val showAsianRange: Boolean = true,
    /** Asian range window in exchange (New York) time. */
    val asianSession: Session = Session("20:00", "00:00"),
    val londonSession: Session = Session("02:00", "05:00"),
    /** Only close-beyond-then-back-inside within this many bars counts as a grab. */
    val returnBars: Int = 2,
    val maxActiveLevels: Int = 15,
    val showLiquidityGrabs: Boolean = true,

    // ---- A+ setup ---------------------------------------------------------
    val showSetup: Boolean = true,
    /** Max bars allowed between the sweep and the structure break. */
    val setupBars: Int = 15,
    /** Stop-loss buffer beyond the sweep wick, as a multiple of ATR. */
    val stopBufferAtr: Double = 0.10,
    /** Take-profit 2 in R multiples. */
    val targetRr: Double = 3.0,
    /** Minimum fair-value-gap size, as a multiple of ATR. */
    val minFvgAtr: Double = 0.10,

    // ---- Filters ----------------------------------------------------------
    val useKillZones: Boolean = true,
    val killZone1: Session = Session("02:00", "05:00"),
    val killZone2: Session = Session("07:00", "10:00"),
    val requireKeyLevel: Boolean = true,
    /** Minimum displacement candle body, as a multiple of ATR. 0 disables. */
    val minDisplacementAtr: Double = 0.8,
    /** Minimum reward:risk to the nearest liquidity target. 0 disables. */
    val minRrToLiquidity: Double = 2.5,
    val maxSignalsPerDay: Int = 2,
    val requireFvg: Boolean = true,
    val useHtfBias: Boolean = true,
    /** HTF bias timeframe in minutes (240 = 4H). */
    val biasTimeframeMinutes: Int = 240,
    val biasEmaLength: Int = 50,

    // ---- Costs & stops (instrument-aware) ---------------------------------
    /**
     * Assumed round-trip cost in TICKS, not pips.
     * GC/MGC spread is usually 1 tick; add slippage. Default 2 ticks.
     */
    val costTicks: Double = 2.0,
    /** Minimum stop distance beyond the sweep, in ticks. */
    val minStopBufferTicks: Double = 10.0,
    /** Minimum stop distance, in points. */
    val minStopPoints: Double = 1.5,
    /** Maximum stop distance, in points. */
    val maxStopPoints: Double = 15.0,

    // ---- Risk panel -------------------------------------------------------
    val accountSize: Double = 50_000.0,
    val riskPercent: Double = 0.5,
    val dailyLossLimitPercent: Double = 2.0,
    val maxLossLimitPercent: Double = 4.0,
    /** Manual override: loss already taken today, in percent. */
    val todayLossPercent: Double = 0.0,
    /** Manual override: total loss so far, in percent of initial balance. */
    val totalLossPercent: Double = 0.0,
    val losingTradesToday: Int = 0,
    /** Stop after this many losing trades in a session. */
    val maxLossesPerDay: Int = 2,
    val blockOnGuardStop: Boolean = true,
    val autoGuardFromSimulation: Boolean = true,

    // ---- Learning ---------------------------------------------------------
    val showStats: Boolean = true,
    val blockNegativeBuckets: Boolean = false,
    val minTradesForBucket: Int = 25,
    /** Cancel an unfilled limit entry after this many bars. */
    val fillTimeoutBars: Int = 20,

    // ---- HTF points of interest -------------------------------------------
    val showHtfPoi: Boolean = true,
    val htfPoiMinutes: Int = 60,
    val maxZonesPerSide: Int = 5,
    val requireHtfPoi: Boolean = false,

    // ---- Contract limits (prop firm guard) --------------------------------
    /** Max contracts allowed for the account. Rapid Daily 50K = 4 mini / 40 micro. */
    val maxContracts: Int = 4,

    // ---- Display ----------------------------------------------------------
    val showDashboard: Boolean = true,
) {
    /**
     * Validate before running. Catches the classic "I reused the FX defaults" mistake:
     * a 0.5% risk on a 50K account with a contract multiplier of 100_000 would size
     * nonsense on gold.
     */
    fun validate(): List<String> {
        val problems = mutableListOf<String>()
        if (riskPercent <= 0.0 || riskPercent > 5.0) {
            problems += "riskPercent must be in (0, 5]; got $riskPercent"
        }
        if (maxStopPoints <= minStopPoints) {
            problems += "maxStopPoints ($maxStopPoints) must exceed minStopPoints ($minStopPoints)"
        }
        if (targetRr < 1.0) problems += "targetRr must be >= 1.0; got $targetRr"
        if (setupBars < 2) problems += "setupBars must be >= 2; got $setupBars"
        if (maxContracts < 1) problems += "maxContracts must be >= 1; got $maxContracts"
        if (biasEmaLength < 5) problems += "biasEmaLength must be >= 5; got $biasEmaLength"
        return problems
    }

    /** Dollar risk for one trade at the configured percentage. */
    fun riskDollars(accountBalance: Double = accountSize): Double =
        accountBalance * riskPercent / 100.0
}

enum class SignalMode { MSS_ONLY, MSS_AND_BOS }

/** A wall-clock window on a 24h clock, in exchange time. */
data class Session(val start: String, val end: String) {
    init {
        require(start.matches(Regex("\\d{2}:\\d{2}"))) { "Session start must be HH:MM, got $start" }
        require(end.matches(Regex("\\d{2}:\\d{2}"))) { "Session end must be HH:MM, got $end" }
    }

    val startMinutes: Int get() = toMinutes(start)
    val endMinutes: Int get() = toMinutes(end)

    /** Session can wrap past midnight (e.g. 20:00 -> 00:00). */
    val wrapsMidnight: Boolean get() = endMinutes <= startMinutes

    fun contains(minuteOfDay: Int): Boolean =
        if (wrapsMidnight) minuteOfDay >= startMinutes || minuteOfDay < endMinutes
        else minuteOfDay >= startMinutes && minuteOfDay < endMinutes

    private fun toMinutes(hhmm: String): Int {
        val (h, m) = hhmm.split(":").map { it.toInt() }
        return h * 60 + m
    }
}
