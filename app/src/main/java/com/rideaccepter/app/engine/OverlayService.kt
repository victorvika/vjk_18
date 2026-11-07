package com.rideaccepter.app.engine

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.IBinder
import android.provider.Settings
import android.view.Gravity
import android.view.MotionEvent
import android.view.WindowManager
import android.widget.LinearLayout
import android.widget.TextView
import com.rideaccepter.app.MainActivity
import com.rideaccepter.app.prefs.AppPreferences

/** Floating overlay control (original: res/layout/overlay_control.xml behaviour, rebuilt in code). */
class OverlayService : Service() {

    private var windowManager: WindowManager? = null
    private var overlayView: LinearLayout? = null
    private lateinit var prefs: AppPreferences

    override fun onCreate() {
        super.onCreate()
        prefs = AppPreferences(this)
        createNotificationChannel()
        startForeground(NOTIF_ID, buildNotification())
        if (Settings.canDrawOverlays(this)) createOverlayView()
        EngineState.overlayRunning.value = true
    }

    private fun createOverlayView() {
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.END
            x = 24; y = 240
        }

        val density = resources.displayMetrics.density
        fun dp(v: Int) = (v * density).toInt()

        val toggle = TextView(this).apply {
            text = if (prefs.engineEnabled) "■ STOP" else "▶ START"
            setTextColor(Color.WHITE); textSize = 13f; setPadding(dp(14), dp(10), dp(14), dp(10))
            background = GradientDrawable().apply {
                cornerRadius = dp(20).toFloat()
                setColor(if (prefs.engineEnabled) Color.parseColor("#3A3A44") else Color.parseColor("#E6002E"))
            }
        }
        val status = TextView(this).apply {
            val f = prefs.loadFilters()
            text = if (f.fareEnabled) "Fare: ₹${f.minFare.toInt()}–₹${f.maxFare.toInt()}" else "No filter"
            setTextColor(Color.parseColor("#9BE29B")); textSize = 11f; setPadding(dp(10), dp(4), dp(10), dp(2))
        }

        overlayView = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(8), dp(8), dp(8), dp(8))
            background = GradientDrawable().apply {
                cornerRadius = dp(16).toFloat(); setColor(Color.parseColor("#E6121218"))
            }
            addView(toggle); addView(status)

            var initialX = 0; var initialY = 0; var touchX = 0f; var touchY = 0f
            setOnTouchListener { _, event ->
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initialX = params.x; initialY = params.y
                        touchX = event.rawX; touchY = event.rawY; true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        params.x = initialX - (event.rawX - touchX).toInt()
                        params.y = initialY + (event.rawY - touchY).toInt()
                        windowManager?.updateViewLayout(this, params); true
                    }
                    else -> false
                }
            }
        }
        toggle.setOnClickListener {
            prefs.engineEnabled = !prefs.engineEnabled
            EngineState.setRunning(prefs.engineEnabled)
            toggle.text = if (prefs.engineEnabled) "■ STOP" else "▶ START"
            (toggle.background as? GradientDrawable)?.setColor(
                if (prefs.engineEnabled) Color.parseColor("#3A3A44") else Color.parseColor("#E6002E")
            )
            val f = prefs.loadFilters()
            status.text = EngineState.lastDecision.value.takeIf { prefs.engineEnabled }
                ?: if (f.fareEnabled) "Fare: ₹${f.minFare.toInt()}–₹${f.maxFare.toInt()}" else "No filter"
        }
        overlayView?.setOnLongClickListener {
            startActivity(Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            true
        }
        windowManager?.addView(overlayView, params)
    }

    private fun buildNotification(): Notification {
        val intent = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, CHANNEL_ID)
        } else {
            @Suppress("DEPRECATION") Notification.Builder(this)
        }
        return builder
            .setContentTitle("RideAccepter overlay")
            .setContentText(if (prefs.engineEnabled) "Engine running — watching for ride offers" else "Overlay ready — engine paused")
            .setSmallIcon(android.R.drawable.ic_media_play)
            .setContentIntent(intent)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(CHANNEL_ID, "Overlay Service", NotificationManager.IMPORTANCE_LOW)
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).createNotificationChannel(channel)
        }
    }

    override fun onDestroy() {
        overlayView?.let { windowManager?.removeView(it) }
        EngineState.overlayRunning.value = false
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    companion object {
        private const val CHANNEL_ID = "rideaccepter_overlay"
        private const val NOTIF_ID = 42
    }
}
