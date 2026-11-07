package com.rideaccepter.app.ui

import android.app.Application
import android.content.Intent
import android.os.Build
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.rideaccepter.app.data.RideHistoryEntity
import com.rideaccepter.app.data.RideRepository
import com.rideaccepter.app.engine.EngineState
import com.rideaccepter.app.engine.OverlayService
import com.rideaccepter.app.prefs.AppPreferences
import com.rideaccepter.core.model.FilterConfig
import com.rideaccepter.core.target.AppTargets
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

enum class AppTab(val label: String) { Login("Login"), Dashboard("Dashboard"), Filter("Filter"), History("History"), Profile("Profile") }


class MainViewModel(app: Application) : AndroidViewModel(app) {
    val prefs = AppPreferences(app)
    private val repo = RideRepository(app)

    val currentTab = MutableStateFlow(AppTab.Dashboard)
    val filters = MutableStateFlow(prefs.loadFilters())
    val selectedPackage = MutableStateFlow(prefs.selectedPackage)
    val userId = MutableStateFlow(prefs.userId ?: "")

    val history: StateFlow<List<RideHistoryEntity>> =
        repo.allRides.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    val totalEarnings: StateFlow<Double> =
        repo.totalEarnings.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), 0.0)

    data class TimingSettings(val scanDebounceMs: Long, val reactionDelayMs: Long, val tapDurationMs: Long, val cooldownSeconds: Int)
    val timing = MutableStateFlow(TimingSettings(prefs.scanDebounceMs, prefs.reactionDelayMs, prefs.tapDurationMs, prefs.cooldownSeconds))

    fun saveTiming(scan: String, reaction: String, tap: String, cooldown: String) {
        val s = (scan.toLongOrNull() ?: timing.value.scanDebounceMs).coerceIn(0, 2000)
        val r = (reaction.toLongOrNull() ?: timing.value.reactionDelayMs).coerceIn(0, 5000)
        val tp = (tap.toLongOrNull() ?: timing.value.tapDurationMs).coerceIn(10, 500)
        val cd = (cooldown.toIntOrNull() ?: timing.value.cooldownSeconds).coerceIn(0, 120)
        prefs.scanDebounceMs = s; prefs.reactionDelayMs = r; prefs.tapDurationMs = tp; prefs.cooldownSeconds = cd
        timing.value = TimingSettings(s, r, tp, cd)
        EngineState.lastDecision.value = "Timing saved: scan ${s}ms • tap in ${r}ms"
    }

    val engineRunning: StateFlow<Boolean> = EngineState.running
    val overlayRunning: StateFlow<Boolean> = EngineState.overlayRunning
    val lastDecision: StateFlow<String> = EngineState.lastDecision

    init {
        EngineState.setRunning(prefs.engineEnabled)
    }

    fun setTab(tab: AppTab) { currentTab.value = tab }

    // ---- filters ----
    fun updateFilters(f: FilterConfig) {
        filters.value = f
        prefs.saveFilters(f)
    }

    fun saveFareRange(min: String, max: String) {
        val minV = min.toDoubleOrNull() ?: return
        val maxV = max.toDoubleOrNull() ?: return
        if (minV < 0 || maxV < minV) return
        updateFilters(filters.value.copy(minFare = minV, maxFare = maxV))
    }

    fun addZone(blocked: Boolean, name: String) {
        val n = name.trim(); if (n.isEmpty()) return
        val f = filters.value
        updateFilters(
            if (blocked) f.copy(noZones = (f.noZones + n).distinct())
            else f.copy(driverZones = (f.driverZones + n).distinct())
        )
    }

    fun removeZone(blocked: Boolean, name: String) {
        val f = filters.value
        updateFilters(
            if (blocked) f.copy(noZones = f.noZones - name)
            else f.copy(driverZones = f.driverZones - name)
        )
    }

    // ---- engine ----
    fun selectTarget(pkg: String) {
        selectedPackage.value = pkg
        prefs.selectedPackage = pkg
    }

    fun startOverlay() {
        val ctx = getApplication<Application>()
        prefs.engineEnabled = true
        EngineState.setRunning(true)
        EngineState.lastDecision.value = "ACTIVE SCANNING"
        val intent = Intent(ctx, OverlayService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) ctx.startForegroundService(intent) else ctx.startService(intent)
    }

    fun stopAll() {
        val ctx = getApplication<Application>()
        prefs.engineEnabled = false
        EngineState.setRunning(false)
        EngineState.lastDecision.value = "IDLE"
        ctx.stopService(Intent(ctx, OverlayService::class.java))
    }

    // ---- auth (LOCAL DEMO — replace with own backend, docs/BACKEND_SPEC.md) ----
    fun login(id: String) {
        if (id.isBlank()) return
        prefs.userId = id.trim()
        userId.value = id.trim()
    }

    fun logout() {
        prefs.clearSession()
        userId.value = ""
    }

    fun clearHistory() {
        viewModelScope.launch { repo.clear() }
    }

    fun targetName(): String =
        AppTargets.findByPackage(selectedPackage.value)?.name ?: selectedPackage.value

}
