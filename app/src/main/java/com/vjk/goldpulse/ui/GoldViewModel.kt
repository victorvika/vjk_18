package com.vjk.goldpulse.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vjk.goldpulse.data.Interval
import com.vjk.goldpulse.data.MarketRepository
import com.vjk.goldpulse.strategy.lsms.Instrument
import com.vjk.goldpulse.strategy.lsms.LsmsConfig
import com.vjk.goldpulse.strategy.lsms.Sizing
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Everything the UI needs in one immutable snapshot. */
data class UiState(
    val loading: Boolean = false,
    val analysis: MarketRepository.Analysis? = null,
    val error: String? = null,
    val interval: Interval = Interval.M15,
    val instrument: Instrument = Instrument.MGC,
    val riskPercent: Double = 0.5,
    val accountSize: Double = 50_000.0,
    val autoRefresh: Boolean = true,
    val lastRefreshMs: Long = 0L,
) {
    val symbol: String get() = if (instrument.symbol == "MGC") "MGC=F" else "GC=F"

    /** Yahoo serves MGC as MGC=F; fall back to GC=F when the micro feed is empty. */
    val config: LsmsConfig
        get() = LsmsConfig(
            accountSize = accountSize,
            riskPercent = riskPercent,
            dailyLossLimitPercent = 2.0,
            maxLossLimitPercent = 4.0,
            maxContracts = if (instrument.symbol == "MGC") 40 else 4,
            // Traders on a 50K prop account usually take 2 signals a session max.
            maxSignalsPerDay = 2,
            useHtfBias = true,
            requireFvg = true,
            useKillZones = true,
        )

    /** Survives a GC->MGC swap, so the card shows a usable size on both. */
    val sizingHint: String?
        get() {
            val result = analysis?.result ?: return null
            val last = result.setups.lastOrNull() ?: return null
            val s = Sizing.suggest(
                riskDollars = accountSize * riskPercent / 100.0,
                stopPoints = last.riskPoints,
                primary = instrument,
                alternate = Sizing.counterpartOf(instrument),
            )
            return s.hint
        }
}

class GoldViewModel(
    private val repo: MarketRepository = MarketRepository(),
) : ViewModel() {

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state.asStateFlow()

    init {
        refresh()
    }

    fun setInterval(interval: Interval) {
        if (interval == _state.value.interval) return
        _state.update { it.copy(interval = interval) }
        refresh()
    }

    fun setInstrument(instrument: Instrument) {
        if (instrument == _state.value.instrument) return
        _state.update { it.copy(instrument = instrument) }
        refresh()
    }

    fun setRiskPercent(pct: Double) {
        _state.update { it.copy(riskPercent = pct.coerceIn(0.1, 3.0)) }
    }

    fun toggleAutoRefresh() {
        _state.update { it.copy(autoRefresh = !it.autoRefresh) }
    }

    fun refresh() {
        val current = _state.value
        if (current.loading) return
        _state.update { it.copy(loading = true, error = null) }

        viewModelScope.launch {
            val outcome = runCatching {
                repo.analyse(
                    symbol = current.symbol,
                    interval = current.interval,
                    instrument = current.instrument,
                    config = current.config,
                    biasMinutes = 240,
                )
            }

            // MGC=F is thin on Yahoo; fall back to the full contract feed so the
            // chart is never empty. Sizing still uses the MGC instrument.
            val fallback = if (outcome.isFailure && current.symbol == "MGC=F") {
                runCatching {
                    repo.analyse(
                        symbol = "GC=F",
                        interval = current.interval,
                        instrument = current.instrument,
                        config = current.config,
                        biasMinutes = 240,
                    )
                }
            } else null

            val resolved = outcome.getOrNull() ?: fallback?.getOrNull()

            _state.update {
                if (resolved != null) {
                    it.copy(
                        loading = false,
                        analysis = resolved,
                        error = if (outcome.isFailure) "MGC feed empty — showing GC=F prices" else null,
                        lastRefreshMs = System.currentTimeMillis(),
                    )
                } else {
                    it.copy(
                        loading = false,
                        error = outcome.exceptionOrNull()?.message ?: "Could not load market data",
                    )
                }
            }
        }
    }
}
