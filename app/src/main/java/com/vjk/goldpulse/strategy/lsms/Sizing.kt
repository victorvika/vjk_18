package com.vjk.goldpulse.strategy.lsms

/**
 * Contract sizing with a cross-instrument fallback.
 *
 * The naive formula `contracts = floor(risk$ / (stopPoints x pointValue))` has a
 * usability trap on gold: at 0.5% risk on a 50K account ($250) with a 5-point stop,
 * GC sizes to `250 / (5 * 100) = 0.5` -> **0 contracts**. That is arithmetically
 * correct and practically useless — the trader sees "0" on every single GC signal.
 *
 * The right answer is not to inflate the size (that breaks the risk plan). It is to
 * tell the trader the equivalent micro position, and to let them choose.
 */
object Sizing {

    data class Suggestion(
        /** Contracts on the requested instrument. */
        val primary: Int,
        val primaryInstrument: Instrument,
        /** Contracts on the alternate instrument, when primary rounds to zero. */
        val alternate: Int? = null,
        val alternateInstrument: Instrument? = null,
        /** True when the primary instrument cannot express this risk at all. */
        val primaryUnusable: Boolean = false,
        /** Human-readable hint for the UI, or null when the primary size is fine. */
        val hint: String? = null,
    ) {
        /**
         * Clamp to the account's contract limit. Note the limits are per-instrument:
         * FundedNext Rapid Daily 50K allows 4 mini OR 40 micro, so the micro limit is
         * ten times the mini limit.
         */
        fun clamped(maxMiniContracts: Int): Suggestion {
            val alt = alternate?.let { minOf(it, maxMiniContracts * 10) }
            return copy(
                primary = minOf(primary, maxMiniContracts),
                alternate = alt,
            )
        }
    }

    /**
     * @param riskDollars dollar amount to risk on this trade
     * @param stopPoints stop distance in price points (not ticks)
     * @param primary the instrument the chart is on
     * @param alternate the micro or mini counterpart
     */
    fun suggest(
        riskDollars: Double,
        stopPoints: Double,
        primary: Instrument,
        alternate: Instrument? = null,
    ): Suggestion {
        require(stopPoints > 0.0) { "stopPoints must be > 0, got $stopPoints" }
        require(riskDollars > 0.0) { "riskDollars must be > 0, got $riskDollars" }

        val rawPrimary = riskDollars / (stopPoints * primary.pointValue)
        val primaryContracts = Math.floor(rawPrimary).toInt()

        if (primaryContracts > 0 || alternate == null) {
            val hint = if (primaryContracts == 0) {
                "Risk \$${riskDollars.toInt()} is too small for one ${primary.symbol} " +
                    "contract on a ${fmt(stopPoints)}-point stop. Increase risk % or widen the account."
            } else null
            return Suggestion(
                primary = primaryContracts,
                primaryInstrument = primary,
                primaryUnusable = primaryContracts == 0,
                hint = hint,
            )
        }

        val rawAlt = riskDollars / (stopPoints * alternate.pointValue)
        val altContracts = Math.floor(rawAlt).toInt()
        val hint = "Use ${altContracts} ${alternate.symbol} (same \$${riskDollars.toInt()} risk) — " +
            "one ${primary.symbol} contract would be \$${(stopPoints * primary.pointValue).toInt()} of risk."

        return Suggestion(
            primary = 0,
            primaryInstrument = primary,
            alternate = altContracts,
            alternateInstrument = alternate,
            primaryUnusable = true,
            hint = hint,
        )
    }

    /** Convenience: pair an instrument with its micro/mini counterpart. */
    fun counterpartOf(instrument: Instrument): Instrument? = when (instrument.symbol) {
        Instrument.GC.symbol -> Instrument.MGC
        Instrument.MGC.symbol -> Instrument.GC
        else -> null
    }

    /**
     * How many consecutive full-stop losses the account can absorb at this risk.
     * This is the number that keeps a prop account alive, so it belongs in the UI.
     */
    fun lossesRemaining(maxLossLimitDollars: Double, riskDollars: Double): Int =
        if (riskDollars <= 0.0) 0 else Math.floor(maxLossLimitDollars / riskDollars).toInt()

    private fun fmt(v: Double): String =
        if (v == Math.floor(v)) v.toInt().toString() else String.format("%.1f", v)
}
