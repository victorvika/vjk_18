package com.rideaccepter.app.prefs

import android.content.Context
import android.content.SharedPreferences
import com.rideaccepter.core.model.FilterConfig
import org.json.JSONArray

/** Own SharedPreferences store (file name from ENGINE_SPEC config discovery). */
class AppPreferences(context: Context) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("auto_accept_config", Context.MODE_PRIVATE)

    var userId: String?
        get() = prefs.getString(KEY_USER_ID, null)
        set(v) = prefs.edit().putString(KEY_USER_ID, v).apply()

    var authToken: String?
        get() = prefs.getString(KEY_TOKEN, null)
        set(v) = prefs.edit().putString(KEY_TOKEN, v).apply()

    var selectedPackage: String
        get() = prefs.getString(KEY_SELECTED_PACKAGE, "com.rideaccepter.simulator") ?: "com.rideaccepter.simulator"
        set(v) = prefs.edit().putString(KEY_SELECTED_PACKAGE, v).apply()

    var engineEnabled: Boolean
        get() = prefs.getBoolean(KEY_ENABLED, false)
        set(v) = prefs.edit().putBoolean(KEY_ENABLED, v).apply()

    var ttsEnabled: Boolean
        get() = prefs.getBoolean(KEY_TTS, true)
        set(v) = prefs.edit().putBoolean(KEY_TTS, v).apply()

    var clickIntervalMs: Long
        get() = prefs.getLong(KEY_CLICK_INTERVAL, 300L)
        set(v) = prefs.edit().putLong(KEY_CLICK_INTERVAL, v).apply()

    /** Event -> scan delay (ms). Lower = faster reaction to a ride offer appearing. */
    var scanDebounceMs: Long
        get() = prefs.getLong(KEY_SCAN_DEBOUNCE, 100L)
        set(v) = prefs.edit().putLong(KEY_SCAN_DEBOUNCE, v).apply()

    /** Fare matched -> tap delay (ms). 0 = instant tap. */
    var reactionDelayMs: Long
        get() = prefs.getLong(KEY_REACTION_DELAY, 0L)
        set(v) = prefs.edit().putLong(KEY_REACTION_DELAY, v).apply()

    /** Gesture tap press duration (ms) when node-click falls back to gesture. */
    var tapDurationMs: Long
        get() = prefs.getLong(KEY_TAP_DURATION, 60L)
        set(v) = prefs.edit().putLong(KEY_TAP_DURATION, v).apply()

    var cooldownSeconds: Int
        get() = prefs.getInt(KEY_COOLDOWN, 5)
        set(v) = prefs.edit().putInt(KEY_COOLDOWN, v).apply()


    fun loadFilters(): FilterConfig = FilterConfig(
        fareEnabled = prefs.getBoolean(K_FARE_ON, true),
        minFare = prefs.getFloat(K_MIN_FARE, 60f).toDouble(),
        maxFare = prefs.getFloat(K_MAX_FARE, 1000f).toDouble(),
        distanceEnabled = prefs.getBoolean(K_DIST_ON, false),
        minDistanceKm = prefs.getFloat(K_MIN_DIST, 0f).toDouble(),
        maxDistanceKm = prefs.getFloat(K_MAX_DIST, 100f).toDouble(),
        driverZoneEnabled = prefs.getBoolean(K_ZONE_ON, false),
        driverZones = getList(K_ZONE_LIST),
        noZoneEnabled = prefs.getBoolean(K_NOZONE_ON, false),
        noZones = getList(K_NOZONE_LIST)
    )

    fun saveFilters(f: FilterConfig) {
        prefs.edit()
            .putBoolean(K_FARE_ON, f.fareEnabled).putFloat(K_MIN_FARE, f.minFare.toFloat()).putFloat(K_MAX_FARE, f.maxFare.toFloat())
            .putBoolean(K_DIST_ON, f.distanceEnabled).putFloat(K_MIN_DIST, f.minDistanceKm.toFloat()).putFloat(K_MAX_DIST, f.maxDistanceKm.toFloat())
            .putBoolean(K_ZONE_ON, f.driverZoneEnabled).putString(K_ZONE_LIST, JSONArray(f.driverZones).toString())
            .putBoolean(K_NOZONE_ON, f.noZoneEnabled).putString(K_NOZONE_LIST, JSONArray(f.noZones).toString())
            .apply()
    }

    private fun getList(key: String): List<String> = try {
        val arr = JSONArray(prefs.getString(key, "[]"))
        List(arr.length()) { arr.optString(it) }.filter { it.isNotBlank() }
    } catch (e: Exception) { emptyList() }

    fun clearSession() = prefs.edit().remove(KEY_USER_ID).remove(KEY_TOKEN).apply()

    companion object {
        private const val KEY_USER_ID = "user_id"
        private const val KEY_TOKEN = "auth_token"
        private const val KEY_SELECTED_PACKAGE = "selected_package"
        private const val KEY_ENABLED = "engine_enabled"
        private const val KEY_TTS = "tts_enabled"
        private const val KEY_CLICK_INTERVAL = "click_interval_ms"
        private const val KEY_SCAN_DEBOUNCE = "scan_debounce_ms"
        private const val KEY_REACTION_DELAY = "reaction_delay_ms"
        private const val KEY_TAP_DURATION = "tap_duration_ms"
        private const val KEY_COOLDOWN = "cooldown_seconds"
        private const val K_FARE_ON = "fare_filter_enabled"
        private const val K_MIN_FARE = "min_fare"; private const val K_MAX_FARE = "max_fare"
        private const val K_DIST_ON = "distance_filter_enabled"
        private const val K_MIN_DIST = "min_distance"; private const val K_MAX_DIST = "max_distance"
        private const val K_ZONE_ON = "driver_zone_enabled"; private const val K_ZONE_LIST = "driver_zone_list"
        private const val K_NOZONE_ON = "no_zone_enabled"; private const val K_NOZONE_LIST = "no_zone_list"
    }
}
