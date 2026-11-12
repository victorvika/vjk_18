package com.vjk.goldpulse.strategy.lsms

/**
 * LSMS — Liquidity Sweep + Market Structure Engine, ported from Pine v3 (FX) to
 * Kotlin for gold futures.
 *
 * Porting rules applied:
 *  - Every evaluation happens on CLOSED bars, matching `barstate.isconfirmed`. The
 *    engine takes a completed bar list; it never looks at a forming bar.
 *  - Structure, sweeps and setups are all evaluated in bar order, because the Pine
 *    script threads mutable state (direction, open swing, pending sweep) through the
 *    same sequence of bars. A vectorised rewrite would silently change the results.
 *  - `request.security(...[1])` in Pine is emulated by reading the higher-timeframe
 *    value from the LAST COMPLETED HTF bar. See [HtfBias].
 *
 * Everything instrument-specific (pip size, contract multiplier, lot maths) has been
 * replaced by tick/point arithmetic driven by [Instrument].
 */
class LsmsEngine(
    private val config: LsmsConfig,
    private val instrument: Instrument,
) {

    init {
        val problems = config.validate()
        require(problems.isEmpty()) { "Invalid LsmsConfig: ${problems.joinToString("; ")}" }
    }

    fun simulate(bars: List<Bar>, htfBiasSeries: IntArray? = null): LsmsResult {
        require(bars.size >= 20) { "Need at least 20 bars, got ${bars.size}" }

        val s = BarSeries(bars)
        val n = s.size

        val atr = Series.atr(s.high, s.low, s.close, 14)
        val rsi = Series.rsi(s.close, 14)
        val pivotHigh = Series.pivotHigh(s.high, config.pivotLength, config.pivotLength)
        val pivotLow = Series.pivotLow(s.low, config.pivotLength, config.pivotLength)

        // --- session bookkeeping -------------------------------------------
        val minutesOfDay = IntArray(n) { minuteOfDay(s.time[it]) }
        val inAsia = BooleanArray(n) { config.asianSession.contains(minutesOfDay[it]) }
        val inKz1 = BooleanArray(n) { config.killZone1.contains(minutesOfDay[it]) }
        val inKz2 = BooleanArray(n) { config.killZone2.contains(minutesOfDay[it]) }
        // Prop-firm session roll: FundedNext resets the trading day at 17:00 New York.
        val fxDay = IntArray(n) { dayIndex(s.time[it]) }
        val newDay = BooleanArray(n) { i -> i == 0 || fxDay[i] != fxDay[i - 1] }

        // --- mutable engine state -------------------------------------------
        val levels = mutableListOf<LiquidityLevel>()
        val htfBullZones = mutableListOf<Fvg>()
        val htfBearZones = mutableListOf<Fvg>()
        val setups = mutableListOf<Setup>()
        val sweeps = mutableListOf<Sweep>()
        val structureEvents = mutableListOf<StructureEvent>()
        val bucketCounts = IntArray(StatBucket.entries.size)
        val bucketWins = IntArray(StatBucket.entries.size)

        var lastSwingHigh = Double.NaN
        var prevSwingHigh = Double.NaN
        var lastSwingLow = Double.NaN
        var prevSwingLow = Double.NaN
        var swingHighOpen = false
        var swingLowOpen = false
        var direction = 0
        var phase = "-"
        var lastEvent = "-"
        var lastSignal = "-"
        var lastSkip: SkipReason? = null
        var signalsToday = 0

        // Asian range
        var asiaHigh = Double.NaN
        var asiaLow = Double.NaN
        var asiaStartBar = -1

        // Previous day high/low, derived from intraday bars (provider independent)
        var dayHigh = Double.NaN
        var dayLow = Double.NaN
        var prevDayHigh = Double.NaN
        var prevDayLow = Double.NaN
        var dayRolled = false

        // Latest LTF fair value gaps
        var bullFvg: Fvg? = null
        var bearFvg: Fvg? = null

        // Pending sweeps waiting for a structure break
        var bullSweep: Sweep? = null
        var bearSweep: Sweep? = null

        // Simulated open trades
        val simTrades = mutableListOf<SimTrade>()
        var netRToday = 0.0
        var lossesToday = 0.0

        var guardStopped = false
        var guardReason: GuardReason? = null

        val costPrice = config.costTicks * instrument.tickSize
        /** Absolute price buffer beyond the sweep extreme, in price units. */
        val stopBufferPrice = maxOf(0.0, config.minStopBufferTicks * instrument.tickSize)

        for (i in 0 until n) {
            // ---------------------------------------------------------------
            // Day roll (FundedNext: 17:00 New York)
            // ---------------------------------------------------------------
            if (newDay[i]) {
                if (!dayHigh.isNaN()) {
                    prevDayHigh = dayHigh
                    prevDayLow = dayLow
                    dayRolled = true
                }
                dayHigh = s.high[i]
                dayLow = s.low[i]
                signalsToday = 0
                netRToday = 0.0
                lossesToday = 0.0
            } else {
                dayHigh = if (dayHigh.isNaN()) s.high[i] else maxOf(dayHigh, s.high[i])
                dayLow = if (dayLow.isNaN()) s.low[i] else minOf(dayLow, s.low[i])
            }

            // ---------------------------------------------------------------
            // Asian range
            // ---------------------------------------------------------------
            val asiaOpen = inAsia[i] && (i == 0 || !inAsia[i - 1])
            val asiaClose = !inAsia[i] && i > 0 && inAsia[i - 1]
            if (inAsia[i]) {
                if (asiaOpen) {
                    asiaHigh = s.high[i]
                    asiaLow = s.low[i]
                    asiaStartBar = i
                } else {
                    asiaHigh = if (asiaHigh.isNaN()) s.high[i] else maxOf(asiaHigh, s.high[i])
                    asiaLow = if (asiaLow.isNaN()) s.low[i] else minOf(asiaLow, s.low[i])
                }
            }

            // ---------------------------------------------------------------
            // Resolve simulated trades on this bar
            // ---------------------------------------------------------------
            if (simTrades.isNotEmpty()) {
                val it2 = simTrades.iterator()
                while (it2.hasNext()) {
                    val t = it2.next()
                    val stopped = if (t.isLong) s.low[i] <= t.stop else s.high[i] >= t.stop
                    val target = if (t.isLong) s.high[i] >= t.target else s.low[i] <= t.target
                    val touched = if (t.isLong) s.low[i] <= t.entry else s.high[i] >= t.entry

                    if (!t.filled) {
                        if (touched) {
                            t.filled = true
                            if (stopped) {
                                record(bucketCounts, bucketWins, t, false)
                                netRToday += -1.0
                                lossesToday += 1.0
                                it2.remove()
                            }
                        } else if (target || i - t.bar > config.fillTimeoutBars) {
                            it2.remove()
                        }
                    } else {
                        if (stopped) {
                            record(bucketCounts, bucketWins, t, false)
                            netRToday += -1.0
                            lossesToday += 1.0
                            it2.remove()
                        } else if (target) {
                            record(bucketCounts, bucketWins, t, true)
                            netRToday += config.targetRr
                            it2.remove()
                        }
                    }
                }
            }

            // ---------------------------------------------------------------
            // LTF fair value gaps (three-bar imbalance)
            // ---------------------------------------------------------------
            if (i >= 2) {
                val atrV = atr[i]
                if (!atrV.isNaN()) {
                    if (s.low[i] > s.high[i - 2] && (s.low[i] - s.high[i - 2]) > atrV * config.minFvgAtr) {
                        bullFvg = Fvg(top = s.low[i], bottom = s.high[i - 2], bar = i, bullish = true)
                    }
                    if (s.high[i] < s.low[i - 2] && (s.low[i - 2] - s.high[i]) > atrV * config.minFvgAtr) {
                        bearFvg = Fvg(top = s.low[i - 2], bottom = s.high[i], bar = i, bullish = false)
                    }
                }
            }

            // ---------------------------------------------------------------
            // HTF POI zones: expire on close through, refresh each bar
            // ---------------------------------------------------------------
            if (config.showHtfPoi || config.requireHtfPoi) {
                htfBullZones.removeAll { s.close[i] < it.bottom }
                htfBearZones.removeAll { s.close[i] > it.top }
            }

            // ---------------------------------------------------------------
            // New swing pivots -> liquidity levels
            // ---------------------------------------------------------------
            val newSwingHigh = !pivotHigh[i].isNaN()
            val newSwingLow = !pivotLow[i].isNaN()

            if (newSwingHigh) {
                prevSwingHigh = lastSwingHigh
                lastSwingHigh = pivotHigh[i]
                swingHighOpen = true
                if (config.showSwings) {
                    val tol = atr[i] * config.equalLevelTolerance
                    var isEqual = false
                    for (lv in levels) {
                        if (lv.side != LevelSide.BUY_SIDE) continue
                        if (lv.kind != LevelKind.SWING_HIGH && lv.kind != LevelKind.EQUAL_HIGHS) continue
                        if (Math.abs(lv.price - lastSwingHigh) <= tol) {
                            isEqual = true
                            val idx = levels.indexOf(lv)
                            levels[idx] = lv.copy(kind = LevelKind.EQUAL_HIGHS)
                            break
                        }
                    }
                    val rsiAtPivot = if (i - config.pivotLength >= 0) rsi[i - config.pivotLength] else Double.NaN
                    val isOb = config.thickenOnRsiExtremes && !rsiAtPivot.isNaN() && rsiAtPivot >= 70
                    val kind = when {
                        isEqual -> LevelKind.EQUAL_HIGHS
                        else -> LevelKind.SWING_HIGH
                    }
                    pushLevel(levels, lastSwingHigh, LevelSide.BUY_SIDE, kind, i - config.pivotLength, isOb)
                }
            }

            if (newSwingLow) {
                prevSwingLow = lastSwingLow
                lastSwingLow = pivotLow[i]
                swingLowOpen = true
                if (config.showSwings) {
                    val tol = atr[i] * config.equalLevelTolerance
                    var isEqual = false
                    for (lv in levels) {
                        if (lv.side != LevelSide.SELL_SIDE) continue
                        if (lv.kind != LevelKind.SWING_LOW && lv.kind != LevelKind.EQUAL_LOWS) continue
                        if (Math.abs(lv.price - lastSwingLow) <= tol) {
                            isEqual = true
                            val idx = levels.indexOf(lv)
                            levels[idx] = lv.copy(kind = LevelKind.EQUAL_LOWS)
                            break
                        }
                    }
                    val rsiAtPivot = if (i - config.pivotLength >= 0) rsi[i - config.pivotLength] else Double.NaN
                    val isOs = config.thickenOnRsiExtremes && !rsiAtPivot.isNaN() && rsiAtPivot <= 30
                    val kind = when {
                        isEqual -> LevelKind.EQUAL_LOWS
                        else -> LevelKind.SWING_LOW
                    }
                    pushLevel(levels, lastSwingLow, LevelSide.SELL_SIDE, kind, i - config.pivotLength, isOs)
                }
            }

            if (config.showPreviousDay && dayRolled && !prevDayHigh.isNaN()) {
                pushLevel(levels, prevDayHigh, LevelSide.BUY_SIDE, LevelKind.PREV_DAY_HIGH, i, false)
                pushLevel(levels, prevDayLow, LevelSide.SELL_SIDE, LevelKind.PREV_DAY_LOW, i, false)
                dayRolled = false
            }

            if (config.showAsianRange && asiaClose && !asiaHigh.isNaN() && asiaStartBar >= 0) {
                pushLevel(levels, asiaHigh, LevelSide.BUY_SIDE, LevelKind.ASIA_HIGH, asiaStartBar, false)
                pushLevel(levels, asiaLow, LevelSide.SELL_SIDE, LevelKind.ASIA_LOW, asiaStartBar, false)
            }

            // ---------------------------------------------------------------
            // Liquidity grabs: wick through, close back inside
            // ---------------------------------------------------------------
            var bullGrab = false
            var bearGrab = false
            var bullKey = false
            var bearKey = false
            var kindBull: LevelKind? = null
            var kindBear: LevelKind? = null

            // Each level is answered independently; a grab on one level must not
            // leak into the classification of the next.
            val toRemove = mutableListOf<LiquidityLevel>()
            for (idx in levels.indices) {
                val lv = levels[idx]
                val hit: Boolean
                val done: Boolean

                if (lv.side == LevelSide.BUY_SIDE) {
                    if (lv.closedBeyondBar == -1) {
                        if (s.high[i] <= lv.price) {
                            hit = false; done = false
                        } else if (s.close[i] < lv.price) {
                            // wicked above, closed back below: a grab
                            hit = true; done = true
                        } else if (config.returnBars == 0) {
                            hit = false; done = true
                        } else {
                            levels[idx] = lv.copy(closedBeyondBar = i)
                            hit = false; done = false
                        }
                    } else {
                        if (s.close[i] < lv.price) { hit = true; done = true }
                        else if (i - lv.closedBeyondBar >= config.returnBars) { hit = false; done = true }
                        else { hit = false; done = false }
                    }
                    if (hit) {
                        bearGrab = true
                        if (lv.kind.isKey) { bearKey = true; kindBear = lv.kind }
                        else if (kindBear == null) kindBear = lv.kind
                    }
                } else {
                    if (lv.closedBeyondBar == -1) {
                        if (s.low[i] >= lv.price) {
                            hit = false; done = false
                        } else if (s.close[i] > lv.price) {
                            hit = true; done = true
                        } else if (config.returnBars == 0) {
                            hit = false; done = true
                        } else {
                            levels[idx] = lv.copy(closedBeyondBar = i)
                            hit = false; done = false
                        }
                    } else {
                        if (s.close[i] > lv.price) { hit = true; done = true }
                        else if (i - lv.closedBeyondBar >= config.returnBars) { hit = false; done = true }
                        else { hit = false; done = false }
                    }
                    if (hit) {
                        bullGrab = true
                        if (lv.kind.isKey) { bullKey = true; kindBull = lv.kind }
                        else if (kindBull == null) kindBull = lv.kind
                    }
                }

                if (done) toRemove += levels[idx]
            }
            if (toRemove.isNotEmpty()) levels.removeAll(toRemove)

            // Keep only the most recent levels, mirroring maxLvls
            while (levels.size > config.maxActiveLevels) levels.removeAt(0)

            // ---------------------------------------------------------------
            // Market structure: BOS / MSS (break must CLOSE beyond the swing)
            // ---------------------------------------------------------------
            var mssUp = false
            var mssDown = false
            var bosUp = false
            var bosDown = false

            if (swingHighOpen && !lastSwingHigh.isNaN() && s.close[i] > lastSwingHigh) {
                val isMss = direction == -1
                mssUp = isMss
                bosUp = !isMss
                lastEvent = if (isMss) "Bullish MSS" else "Bullish BOS"
                structureEvents += if (isMss) StructureEvent.MSS_UP else StructureEvent.BOS_UP
                swingHighOpen = false
                direction = 1
            }

            if (swingLowOpen && !lastSwingLow.isNaN() && s.close[i] < lastSwingLow) {
                val isMss = direction == 1
                mssDown = isMss
                bosDown = !isMss
                lastEvent = if (isMss) "Bearish MSS" else "Bearish BOS"
                structureEvents += if (isMss) StructureEvent.MSS_DOWN else StructureEvent.BOS_DOWN
                swingLowOpen = false
                direction = -1
            }

            // phase: impulse -> correction -> continuation
            phase = when {
                mssUp || mssDown -> "Impulse (post-MSS)"
                bosUp || bosDown -> if (phase == "Correction") "Continuation" else "Impulse"
                (newSwingLow && direction == 1) || (newSwingHigh && direction == -1) -> "Correction"
                else -> phase
            }

            // ---------------------------------------------------------------
            // Risk guard (prop-firm limits)
            // ---------------------------------------------------------------
            val vNetR = if (config.autoGuardFromSimulation) netRToday else 0.0
            val vLosses = if (config.autoGuardFromSimulation) lossesToday else 0.0
            val effTodayLoss = maxOf(
                config.todayLossPercent,
                maxOf(0.0, -vNetR) * config.riskPercent,
            )
            val effLosses = maxOf(config.losingTradesToday.toDouble(), vLosses)
            guardStopped = effLosses >= config.maxLossesPerDay ||
                effTodayLoss + config.riskPercent >= config.dailyLossLimitPercent ||
                config.totalLossPercent + config.riskPercent >= config.maxLossLimitPercent
            guardReason = when {
                effLosses >= config.maxLossesPerDay -> GuardReason.LOSS_COUNT
                effTodayLoss + config.riskPercent >= config.dailyLossLimitPercent -> GuardReason.DAILY_LIMIT
                config.totalLossPercent + config.riskPercent >= config.maxLossLimitPercent -> GuardReason.MAX_LIMIT
                else -> null
            }

            // ---------------------------------------------------------------
            // Track sweeps waiting for a structure break
            // ---------------------------------------------------------------
            val touchesBullZone = htfBullZones.any { s.high[i] >= it.bottom && s.low[i] <= it.top }
            val touchesBearZone = htfBearZones.any { s.high[i] >= it.bottom && s.low[i] <= it.top }

            if (bullGrab && (!config.requireKeyLevel || bullKey)) {
                val alive = bullSweep != null && i - bullSweep!!.bar <= config.setupBars
                val low = if (alive) minOf(bullSweep!!.extreme, s.low[i]) else s.low[i]
                bullSweep = Sweep(
                    bar = i,
                    side = LevelSide.SELL_SIDE,
                    extreme = low,
                    levelKind = kindBull ?: LevelKind.SWING_LOW,
                    touchedHtfPoi = touchesBullZone || (alive && bullSweep!!.touchedHtfPoi),
                )
                sweeps += bullSweep!!
            }

            if (bearGrab && (!config.requireKeyLevel || bearKey)) {
                val alive = bearSweep != null && i - bearSweep!!.bar <= config.setupBars
                val high = if (alive) maxOf(bearSweep!!.extreme, s.high[i]) else s.high[i]
                bearSweep = Sweep(
                    bar = i,
                    side = LevelSide.BUY_SIDE,
                    extreme = high,
                    levelKind = kindBear ?: LevelKind.SWING_HIGH,
                    touchedHtfPoi = touchesBearZone || (alive && bearSweep!!.touchedHtfPoi),
                )
                sweeps += bearSweep!!
            }

            // ---------------------------------------------------------------
            // A+ setup: sweep -> MSS -> FVG entry -> liquidity target
            // ---------------------------------------------------------------
            val inKz = !config.useKillZones || inKz1[i] || inKz2[i]
            val bias = htfBiasSeries?.getOrNull(i) ?: 0

            val longTriggerOk = mssUp || (config.signalMode == SignalMode.MSS_AND_BOS && bosUp)
            val shortTriggerOk = mssDown || (config.signalMode == SignalMode.MSS_AND_BOS && bosDown)

            // A long is only considered on a bullish break; the sweep must still be
            // inside the setup window. If the break is a BOS in "MSS only" mode the
            // trigger is false, and per the Pine script the sweep is NOT consumed —
            // it stays pending so a later MSS on the same sweep can still fire.
            if (longTriggerOk) {
                val sweep = bullSweep
                if (sweep != null && i - sweep.bar <= config.setupBars) {
                    val poiOk = !config.requireHtfPoi || sweep.touchedHtfPoi
                    if (poiOk) {
                        when (val outcome = buildSetup(
                            isLong = true, i = i, bars = s, sweep = sweep,
                            fvg = bullFvg, atr = atr[i], inKz = inKz, inKz2 = inKz2[i],
                            bias = bias, signalsToday = signalsToday,
                            guardStopped = guardStopped, guardReason = guardReason,
                            nearestLiquidity = nearestAbove(levels, s.close[i]),
                        )) {
                            is SetupOutcome.Accepted -> {
                                adopt(outcome.setup, setups, simTrades)
                                signalsToday += 1
                                lastSignal = formatSignal(outcome.setup)
                                lastSkip = null
                            }
                            is SetupOutcome.Skipped -> lastSkip = outcome.reason
                        }
                    }
                }
                // Consumed only once the structure actually broke with this sweep.
                bullSweep = null
            }

            if (shortTriggerOk) {
                val sweep = bearSweep
                if (sweep != null && i - sweep.bar <= config.setupBars) {
                    val poiOk = !config.requireHtfPoi || sweep.touchedHtfPoi
                    if (poiOk) {
                        when (val outcome = buildSetup(
                            isLong = false, i = i, bars = s, sweep = sweep,
                            fvg = bearFvg, atr = atr[i], inKz = inKz, inKz2 = inKz2[i],
                            bias = bias, signalsToday = signalsToday,
                            guardStopped = guardStopped, guardReason = guardReason,
                            nearestLiquidity = nearestBelow(levels, s.close[i]),
                        )) {
                            is SetupOutcome.Accepted -> {
                                adopt(outcome.setup, setups, simTrades)
                                signalsToday += 1
                                lastSignal = formatSignal(outcome.setup)
                                lastSkip = null
                            }
                            is SetupOutcome.Skipped -> lastSkip = outcome.reason
                        }
                    }
                }
                bearSweep = null
            }
        }

        val trend = classifyTrend(prevSwingHigh, lastSwingHigh, prevSwingLow, lastSwingLow, direction)

        val stats = StatBucket.entries.mapIndexed { idx, bucket ->
            bucket to BucketStat(bucketCounts[idx], bucketWins[idx], config.targetRr)
        }.toMap()

        return LsmsResult(
            setups = setups,
            sweeps = sweeps,
            structureEvents = structureEvents,
            levels = levels,
            fvg = listOfNotNull(bullFvg, bearFvg),
            stats = stats,
            trend = trend,
            phase = phase,
            lastEvent = lastEvent,
            lastSignal = lastSignal,
            lastSkip = lastSkip,
            guardStopped = guardStopped,
            guardReason = guardReason,
            htfBias = htfBiasSeries?.lastOrNull() ?: 0,
            netRToday = netRToday,
            lossesToday = lossesToday,
        )
    }

    // =======================================================================
    // Setup construction
    // =======================================================================

    private fun buildSetup(
        isLong: Boolean,
        i: Int,
        bars: BarSeries,
        sweep: Sweep,
        fvg: Fvg?,
        atr: Double,
        inKz: Boolean,
        inKz2: Boolean,
        bias: Int,
        signalsToday: Int,
        guardStopped: Boolean,
        guardReason: GuardReason?,
        nearestLiquidity: Double,
    ): SetupOutcome {
        // Entry: FVG consequent encroachment (midpoint) if the gap formed after the
        // sweep, otherwise a retest of the broken swing.
        val usableFvg = fvg?.takeIf { it.bar >= sweep.bar && it.bullish == isLong }
        val rawEntry = if (usableFvg != null) {
            (usableFvg.top + usableFvg.bottom) / 2.0
        } else {
            if (isLong) bars.high[i] else bars.low[i]
        }
        val entry = if (isLong) minOf(rawEntry, bars.close[i]) else maxOf(rawEntry, bars.close[i])

        val stopRaw = if (isLong) {
            sweep.extreme - maxOf(atr * config.stopBufferAtr, stopBufferPrice)
        } else {
            sweep.extreme + maxOf(atr * config.stopBufferAtr, stopBufferPrice)
        }
        val stop = instrument.roundToTick(stopRaw)
        val roundedEntry = instrument.roundToTick(entry)

        val riskPoints = if (isLong) roundedEntry - stop else stop - roundedEntry
        if (riskPoints <= 0.0) return SetupOutcome.Skipped(SkipReason.StopTooTight(riskPoints))

        // Cost is charged in price terms on the risk side, matching the Pine script
        val riskWithCost = riskPoints + costPrice
        val rrToLiquidity = if (nearestLiquidity.isNaN()) config.targetRr else {
            val reward = if (isLong) nearestLiquidity - roundedEntry - costPrice
            else roundedEntry - nearestLiquidity - costPrice
            reward / riskWithCost
        }

        // ---- filters, in the same order as the Pine script -------------------
        if (!inKz) return SetupOutcome.Skipped(SkipReason.OutsideKillZone)
        if (signalsToday >= config.maxSignalsPerDay) return SetupOutcome.Skipped(SkipReason.MaxSignalsPerDay)
        if (config.blockOnGuardStop && guardStopped) {
            return SetupOutcome.Skipped(SkipReason.RiskGuard(guardReason ?: GuardReason.DAILY_LIMIT))
        }
        if (config.useHtfBias) {
            val required = if (isLong) 1 else -1
            if (bias != required) return SetupOutcome.Skipped(SkipReason.AgainstHtfBias)
        }
        if (config.requireFvg && usableFvg == null) return SetupOutcome.Skipped(SkipReason.NoFvgAfterSweep)

        if (config.minDisplacementAtr > 0.0 && !atr.isNaN()) {
            val body = if (isLong) bars.close[i] - bars.open[i] else bars.open[i] - bars.close[i]
            if (body < atr * config.minDisplacementAtr) {
                return SetupOutcome.Skipped(SkipReason.WeakDisplacement)
            }
        }

        // For GC/MGC one "point" is 1.00 of price, so price distance == points.
        val riskInPoints = riskWithCost
        if (riskInPoints < config.minStopPoints) return SetupOutcome.Skipped(SkipReason.StopTooTight(riskInPoints))
        if (riskInPoints > config.maxStopPoints) return SetupOutcome.Skipped(SkipReason.StopTooWide(riskInPoints))

        if (config.minRrToLiquidity > 0.0 && rrToLiquidity < config.minRrToLiquidity) {
            return SetupOutcome.Skipped(SkipReason.RrTooLiquidity(rrToLiquidity))
        }

        // ---- sizing ---------------------------------------------------------
        val riskDollars = config.riskDollars()
        // contracts = risk$ / (risk in points x dollars per point)
        val contractsRaw = riskDollars / (riskWithCost * instrument.pointValue)
        val contracts = Math.floor(contractsRaw).toInt().coerceIn(0, config.maxContracts)

        val tp2 = instrument.roundToTick(
            if (isLong) roundedEntry + riskWithCost * config.targetRr
            else roundedEntry - riskWithCost * config.targetRr,
        )

        return SetupOutcome.Accepted(
            Setup(
                bar = i,
                time = bars.time[i],
                isLong = isLong,
                entry = roundedEntry,
                stopLoss = stop,
                takeProfit1 = nearestLiquidity.takeIf { !it.isNaN() },
                takeProfit2 = tp2,
                riskPoints = riskWithCost,
                riskDollars = riskDollars,
                contracts = contracts,
                rrToLiquidity = rrToLiquidity,
                entryZone = usableFvg,
                levelKind = sweep.levelKind,
                inKillZone2 = inKz2,
            ),
        )
    }

    private fun formatSignal(setup: Setup): String {
        val dir = if (setup.isLong) "Long" else "Short"
        val liq = setup.takeProfit1?.let { String.format("liq %.1fR", setup.rrToLiquidity) } ?: "no liquidity target"
        return String.format(
            "%s @ %.2f | %d %s | %.1fpt | %s",
            dir, setup.entry, setup.contracts, instrument.symbol, setup.riskPoints, liq,
        )
    }

    /** Register an accepted setup and start tracking its simulated outcome. */
    private fun adopt(setup: Setup, into: MutableList<Setup>, trades: MutableList<SimTrade>) {
        into += setup
        trades += SimTrade(
            isLong = setup.isLong,
            entry = setup.entry,
            stop = setup.stopLoss,
            target = setup.takeProfit2,
            bar = setup.bar,
            bucketKey = setup.levelKind,
            killZone2 = setup.inKillZone2,
        )
    }

    private sealed interface SetupOutcome {
        data class Accepted(val setup: Setup) : SetupOutcome
        data class Skipped(val reason: SkipReason) : SetupOutcome
    }

    private data class SimTrade(
        val isLong: Boolean,
        val entry: Double,
        val stop: Double,
        val target: Double,
        val bar: Int,
        val bucketKey: LevelKind,
        val killZone2: Boolean,
        var filled: Boolean = false,
    )

    // =======================================================================
    // Helpers
    // =======================================================================

    private fun pushLevel(
        levels: MutableList<LiquidityLevel>,
        price: Double,
        side: LevelSide,
        kind: LevelKind,
        bar: Int,
        rsiExtreme: Boolean,
    ) {
        if (price.isNaN()) return
        levels += LiquidityLevel(price, side, kind, bar, rsiExtreme = rsiExtreme)
    }

    /** Nearest intact buy-side pool ABOVE [price] — the natural long target. */
    private fun nearestAbove(levels: List<LiquidityLevel>, price: Double): Double {
        var best = Double.NaN
        for (lv in levels) {
            if (lv.side != LevelSide.BUY_SIDE) continue
            if (lv.price <= price) continue
            best = if (best.isNaN()) lv.price else minOf(best, lv.price)
        }
        return best
    }

    /** Nearest intact sell-side pool BELOW [price] — the natural short target. */
    private fun nearestBelow(levels: List<LiquidityLevel>, price: Double): Double {
        var best = Double.NaN
        for (lv in levels) {
            if (lv.side != LevelSide.SELL_SIDE) continue
            if (lv.price >= price) continue
            best = if (best.isNaN()) lv.price else maxOf(best, lv.price)
        }
        return best
    }

    private fun record(counts: IntArray, wins: IntArray, trade: SimTrade, win: Boolean) {
        val buckets = mutableListOf(StatBucket.ALL)
        buckets += if (trade.killZone2) StatBucket.KILL_ZONE_NEW_YORK else StatBucket.KILL_ZONE_LONDON
        when (trade.bucketKey) {
            LevelKind.ASIA_HIGH, LevelKind.ASIA_LOW -> buckets += StatBucket.ASIA_LEVELS
            LevelKind.PREV_DAY_HIGH, LevelKind.PREV_DAY_LOW -> buckets += StatBucket.PREV_DAY_LEVELS
            LevelKind.EQUAL_HIGHS, LevelKind.EQUAL_LOWS -> buckets += StatBucket.EQUAL_LEVELS
            LevelKind.SWING_HIGH, LevelKind.SWING_LOW -> buckets += StatBucket.SWINGS
        }
        for (b in buckets) {
            counts[b.ordinal] += 1
            if (win) wins[b.ordinal] += 1
        }
    }

    private fun classifyTrend(
        prevHigh: Double,
        lastHigh: Double,
        prevLow: Double,
        lastLow: Double,
        direction: Int,
    ): Trend {
        val hh = !prevHigh.isNaN() && !lastHigh.isNaN() && lastHigh > prevHigh
        val lh = !prevHigh.isNaN() && !lastHigh.isNaN() && lastHigh < prevHigh
        val hl = !prevLow.isNaN() && !lastLow.isNaN() && lastLow > prevLow
        val ll = !prevLow.isNaN() && !lastLow.isNaN() && lastLow < prevLow
        return when {
            hh && hl && direction == 1 -> Trend.UPTREND
            lh && ll && direction == -1 -> Trend.DOWNTREND
            else -> Trend.RANGE
        }
    }

    /** Minutes since midnight in the exchange timezone, derived from the bar timestamp. */
    private fun minuteOfDay(epochMillis: Long): Int = NewYorkClock.minuteOfDay(epochMillis)

    /** Trading-day index with the 17:00 New York roll. */
    private fun dayIndex(epochMillis: Long): Int = NewYorkClock.dayIndex(epochMillis)
}
