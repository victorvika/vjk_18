package com.rideaccepter.app.engine

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.graphics.Rect
import android.os.Handler
import android.os.Looper
import android.speech.tts.TextToSpeech
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.rideaccepter.app.data.RideHistoryEntity
import com.rideaccepter.app.data.RideRepository
import com.rideaccepter.app.prefs.AppPreferences
import com.rideaccepter.core.model.FilterDecision
import com.rideaccepter.core.parser.RideTextParser
import com.rideaccepter.core.rules.FilterRuleEngine
import com.rideaccepter.core.target.AppTargets
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.util.Locale

/**
 * Core engine (clean-room, see docs/ENGINE_SPEC.md).
 * Flow: event → debounced scan → parse → filter rules → accept action → history + TTS.
 * Runs ONLY while the user has pressed START (engineEnabled). No subscription/plan gate.
 */
class RideAccessibilityService : AccessibilityService() {

    private val handler = Handler(Looper.getMainLooper())
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private lateinit var prefs: AppPreferences
    private lateinit var repo: RideRepository
    private var tts: TextToSpeech? = null
    private var isProcessing = false
    private var lastAcceptTime = 0L
    private val knownCoordinates = mutableMapOf<String, Pair<Float, Float>>()

    private val scanRunnable = Runnable { scanAndClick() }

    override fun onServiceConnected() {
        super.onServiceConnected()
        prefs = AppPreferences(this)
        repo = RideRepository(this)
        if (prefs.ttsEnabled) {
            tts = TextToSpeech(this) { status ->
                if (status == TextToSpeech.SUCCESS) tts?.language = Locale.US
            }
        }
        EngineState.setRunning(prefs.engineEnabled)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null || !::prefs.isInitialized) return
        if (!prefs.engineEnabled) return
        val pkg = event.packageName?.toString() ?: return
        if (AppTargets.findByPackage(pkg) == null) return
        // Debounce: collapse event bursts into one scan (original: SCAN_DEBOUNCE_MS)
        handler.removeCallbacks(scanRunnable)
        handler.postDelayed(scanRunnable, prefs.scanDebounceMs.coerceIn(0, 2000))
    }

    private fun scanAndClick() {
        if (isProcessing) return
        val root = rootInActiveWindow ?: return
        val target = AppTargets.findByPackage(root.packageName?.toString() ?: return) ?: return
        isProcessing = true
        try {
            val texts = mutableListOf<String>()
            collectLeafTexts(root, texts)
            val ride = RideTextParser.parse(texts, target)

            when (val decision = FilterRuleEngine.evaluate(ride, prefs.loadFilters())) {
                is FilterDecision.Ignore -> EngineState.lastDecision.value = "IGNORED: ${decision.reason}"
                FilterDecision.Accept -> {
                    val delay = prefs.reactionDelayMs.coerceIn(0, 5000)
                    if (delay <= 0) performAccept(root, target.packageName, ride)
                    else {
                        EngineState.lastDecision.value = "MATCHED ₹${ride.fareAmount?.toInt() ?: 0} — tapping in ${delay}ms"
                        handler.postDelayed({ performAccept(root, target.packageName, ride) }, delay)
                    }
                }
            }
        } finally {
            isProcessing = false
        }
    }

    private fun performAccept(root: AccessibilityNodeInfo, pkg: String, ride: com.rideaccepter.core.model.RideDetails) {
        val now = System.currentTimeMillis()
        if (now - lastAcceptTime < prefs.cooldownSeconds * 1000L) return
        val target = AppTargets.findByPackage(pkg) ?: return
        val button = findAcceptButton(root, AppTargets.acceptVariantsFor(target))
        val clicked = when {
            button != null -> performNodeClick(button)
            else -> {
                val c = knownCoordinates[pkg]
                if (c != null) performGestureTap(c.first, c.second) else false
            }
        }
        if (clicked && button != null) {
            val r = Rect(); button.getBoundsInScreen(r)
            knownCoordinates[pkg] = r.exactCenterX() to r.exactCenterY()
        }
        if (clicked) {
            lastAcceptTime = now
            EngineState.lastDecision.value = "ACCEPTED ₹${ride.fareAmount?.toInt() ?: 0} • ${target.name}"
            saveRideToHistory(ride.appName, ride.fareAmount ?: 0.0, ride.fareText, ride.pickupKm, ride.tripKm, ride.pickupText, ride.dropoffText)
            if (prefs.ttsEnabled) speak("Ride accepted. Fare ${ride.fareAmount?.toInt() ?: 0} rupees")
        }
    }

    private fun collectLeafTexts(node: AccessibilityNodeInfo?, out: MutableList<String>) {
        if (node == null) return
        val text = node.text?.toString()?.trim()
        if (node.childCount == 0 && !text.isNullOrEmpty()) out.add(text)
        for (i in 0 until node.childCount) collectLeafTexts(node.getChild(i), out)
    }

    private fun findAcceptButton(root: AccessibilityNodeInfo, variants: List<String>): AccessibilityNodeInfo? {
        for (v in variants) {
            val found = root.findAccessibilityNodeInfosByText(v)
            val clickable = found?.firstOrNull { it.isClickable } ?: found?.firstOrNull()
            if (clickable != null) return clickable
        }
        return null
    }

    private fun performNodeClick(node: AccessibilityNodeInfo): Boolean {
        var current: AccessibilityNodeInfo? = node
        while (current != null) {
            if (current.isClickable && current.performAction(AccessibilityNodeInfo.ACTION_CLICK)) return true
            current = current.parent
        }
        val r = Rect(); node.getBoundsInScreen(r)
        return performGestureTap(r.exactCenterX(), r.exactCenterY())
    }

    private fun performGestureTap(x: Float, y: Float): Boolean {
        val path = Path().apply { moveTo(x, y) }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, prefs.tapDurationMs.coerceIn(10, 500)))
            .build()
        return dispatchGesture(gesture, null, null)
    }

    private fun saveRideToHistory(
        appName: String, fare: Double, fareText: String?,
        pickupKm: Double?, tripKm: Double?, pickup: String?, drop: String?
    ) {
        scope.launch {
            repo.insert(
                RideHistoryEntity(
                    appName = appName, fare = fare, fareString = fareText ?: "₹${fare.toInt()}",
                    pickupKm = pickupKm, tripKm = tripKm,
                    pickupLocation = pickup, dropoffLocation = drop,
                    timestamp = System.currentTimeMillis()
                )
            )
        }
    }

    private fun speak(text: String) {
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "rideaccepted")
    }

    override fun onInterrupt() { /* no-op */ }

    override fun onDestroy() {
        handler.removeCallbacks(scanRunnable)
        tts?.shutdown()
        super.onDestroy()
    }

}
