package com.rideaccepter.simulator

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

/**
 * Mock target app for SAFE end-to-end testing of the engine.
 * Shows a fake ride-offer card (fare / km / addresses / Accept button) exactly
 * like a driver app — the main app's AccessibilityService sees these texts.
 * Test data defaults are the Screenshot #3 rides (Sembakkam, Chennai).
 */
class MainActivity : Activity() {

    private lateinit var card: LinearLayout
    private lateinit var status: TextView
    private lateinit var fareInput: EditText

    private data class MockRide(val fare: Int, val pickupKm: Double, val tripKm: Double, val pickup: String, val drop: String)

    private val rides = listOf(
        MockRide(100, 1.0, 3.2, "Sembakkam - 3A, MF Nagar, Thirumalai Nagar, Sembakkam, Chennai - 600073", "Rajakilpakkam - St. Joseph's Church, Chitlapakkam Main Road, Chennai"),
        MockRide(40, 0.8, 6.3, "Rajakilpakkam - 2/6, Chitlapakkam Main Rd, Tambaram East, Chennai - 600073", "Selaiyur - JJ Garden Road, Tiruvanchery, Selaiyur, Chennai"),
        MockRide(125, 0.9, 0.8, "Selaiyur - Jagjeevan, 5/14, Bharathi Nagar, Ram Nagar, Selaiyur, Chennai", "Seven Wells - George Town, Chennai - 600001")
    )
    private var index = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 48, 48, 48)
            setBackgroundColor(Color.BLACK)
        }
        val title = TextView(this).apply {
            text = "Mock Ride Simulator (Target App)"; textSize = 20f; setTextColor(Color.WHITE)
        }
        status = TextView(this).apply {
            text = "No ride yet. Main app-la START OVERLAY pottutu, inga ride generate pannunga."
            setTextColor(Color.GRAY); setPadding(0, 24, 0, 24)
        }
        fareInput = EditText(this).apply {
            hint = "Custom fare (₹) — blank = preset ride"; setTextColor(Color.WHITE)
            setHintTextColor(Color.GRAY)
        }
        val generate = Button(this).apply { text = "Simulate Incoming Ride" }
        card = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; visibility = View.GONE
            setPadding(32, 32, 32, 32)
        }
        generate.setOnClickListener { showRide() }
        root.addView(title); root.addView(status); root.addView(fareInput); root.addView(generate); root.addView(card)
        setContentView(root)
    }

    private fun showRide() {
        val preset = rides[index % rides.size]; index++
        val fare = fareInput.text.toString().toIntOrNull() ?: preset.fare
        card.removeAllViews()
        fun tv(text: String, size: Float = 16f, color: Int = Color.WHITE, padTop: Int = 8) = TextView(this).apply {
            this.text = text; textSize = size; setTextColor(color); setPadding(0, padTop, 0, 0)
        }
        val fareTv = tv("₹$fare", 30f)
        // These leaf texts are what the parser reads:
        card.addView(fareTv)
        card.addView(tv("${preset.pickupKm} km away", 15f, Color.LTGRAY))
        card.addView(tv("${preset.tripKm} km trip", 15f, Color.LTGRAY))
        card.addView(tv("PICKUP", 12f, Color.GREEN, 20))
        card.addView(tv(preset.pickup, 15f))
        card.addView(tv("DROP", 12f, Color.RED, 16))
        card.addView(tv(preset.drop, 15f))
        val accept = Button(this).apply {
            text = "Accept"
            setOnClickListener {
                text = "Accepted ✓"
                status.text = "Ride ACCEPTED (tap was real — node click or gesture)"
                status.setTextColor(Color.GREEN)
                card.visibility = View.GONE
            }
        }
        val reject = Button(this).apply {
            text = "Reject"
            setOnClickListener {
                status.text = "Ride screen closed (rejected manually)"
                card.visibility = View.GONE
            }
        }
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER
            addView(reject); addView(accept)
        }
        card.addView(row)
        card.visibility = View.VISIBLE
        status.text = "Incoming ride: ₹$fare — engine filter check seiyum… (₹40 ride = ignore aaganum, ₹100 = accept aaganum)"
        status.setTextColor(Color.YELLOW)
    }
}
