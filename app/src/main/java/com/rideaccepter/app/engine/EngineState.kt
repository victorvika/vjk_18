package com.rideaccepter.app.engine

import android.content.ComponentName
import android.content.Context
import android.content.pm.PackageManager
import android.provider.Settings
import com.rideaccepter.app.prefs.AppPreferences
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/** Shared live state between Accessibility engine, Overlay and Dashboard UI. */
object EngineState {
    private val _running = MutableStateFlow(false)
    val running: StateFlow<Boolean> = _running
    val lastDecision = MutableStateFlow("IDLE")
    val overlayRunning = MutableStateFlow(false)

    fun setRunning(v: Boolean) { _running.value = v }
}

object StatusChecks {
    fun isAccessibilityEnabled(context: Context): Boolean {
        val expected = ComponentName(context, RideAccessibilityService::class.java).flattenToString()
        val enabled = Settings.Secure.getString(
            context.contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: return false
        return enabled.split(':').any { it.equals(expected, ignoreCase = true) }
    }

    fun isOverlayGranted(context: Context): Boolean = Settings.canDrawOverlays(context)

    fun isShizukuInstalled(context: Context): Boolean = try {
        context.packageManager.getPackageInfo("moe.shizuku.privileged.api", 0)
        true
    } catch (e: PackageManager.NameNotFoundException) { false }

    fun isTargetInstalled(context: Context, pkg: String): Boolean = try {
        context.packageManager.getPackageInfo(pkg, 0); true
    } catch (e: PackageManager.NameNotFoundException) { false }

}
