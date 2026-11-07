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
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

enum class AppTab(val label: String) { Plans("Plans"), Login("Login"), Dashboard("Dashboard"), Filter("Filter"), History("History"), Profile("Profile") }

data class PlanOption(val id: String, val title: String, val days: Int, val priceText: String)

val DEFAULT_PLANS = listOf(
    PlanOption("1_day", "1 Day Plan (24 hours)", 1, "₹150"),
    PlanOption("7_day", "1 Week Plan (7 days)", 7, "₹270"),
    PlanOption("15_day", "15 Days Plan", 15, "₹399"),
    PlanOption("30_day", "30 Days Plan", 30, "₹699"),
    PlanOption("365_day", "1 Year Plan (365 days)", 365, "₹2999")
)

class MainViewModel(app: Application) : AndroidViewModel(app) {
    val prefs = AppPreferences(app)
    private val repo = RideRepository(app)

    val currentTab = MutableStateFlow(AppTab.Dashboard)
    val filters = MutableStateFlow(prefs.loadFilters())
    val selectedPackage = MutableStateFlow(prefs.selectedPackage)
    val userId = MutableStateFlow(prefs.userId ?: "")
    val planName = MutableStateFlow(prefs.planName ?: "")
    val secondsRemaining = MutableStateFlow(prefs.secondsRemaining)
    val expiryFormatted = MutableStateFlow(formatExpiry(prefs.planExpiresTs))

    val history: StateFlow<List<RideHistoryEntity>> =
        repo.allRides.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    val totalEarnings: StateFlow<Double> =
        repo.totalEarnings.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), 0.0)

    val engineRunning: StateFlow<Boolean> = EngineState.running
    val overlayRunning: StateFlow<Boolean> = EngineState.overlayRunning
    val lastDecision: StateFlow<String> = EngineState.lastDecision

    init {
        EngineState.setRunning(prefs.engineEnabled && prefs.isPlanActive)
        viewModelScope.launch {
            while (true) {
                secondsRemaining.value = prefs.secondsRemaining
                expiryFormatted.value = formatExpiry(prefs.planExpiresTs)
                if (prefs.engineEnabled && !prefs.isPlanActive) {
                    prefs.engineEnabled = false
                    EngineState.setRunning(false)
                    EngineState.lastDecision.value = "PLAN EXPIRED"
                }
                delay(1000)
            }
        }
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

    // ---- plan / auth (LOCAL DEMO — replace with own backend, docs/BACKEND_SPEC.md) ----
    fun activateDemoPlan(plan: PlanOption) {
        val now = System.currentTimeMillis()
        val base = maxOf(now, prefs.planExpiresTs)
        prefs.planExpiresTs = base + plan.days * 24L * 60 * 60 * 1000
        prefs.planName = plan.id
        planName.value = plan.id
    }

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

    private fun formatExpiry(ts: Long): String =
        if (ts <= 0) "—" else SimpleDateFormat("dd MMM yyyy, hh:mm a", Locale.ENGLISH).format(Date(ts))
}
