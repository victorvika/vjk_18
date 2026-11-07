package com.rideaccepter.core.target

import com.rideaccepter.core.model.AppTarget

/**
 * Supported target apps — reconstructed from SupportedApps in the analysis
 * (docs/FEATURE_INVENTORY.md). The Mock Simulator entry comes FIRST so the
 * whole loop can be tested without any real driver app.
 */
object AppTargets {
    val UNIVERSAL_ACCEPT_VARIANTS = listOf("Accept", "ACCEPT", "accept", "Ride Accept", "RIDE ACCEPT", "View >")

    val ALL: List<AppTarget> = listOf(
        AppTarget("Mock Ride Simulator", "com.rideaccepter.simulator", listOf("Accept Ride", "Accept")),
        AppTarget("Ola Driver", "com.olacabs.oladriver", listOf("Accept Order", "ACCEPT ORDER")),
        AppTarget("Rapido Captain", "com.rapido.rider", emptyList()),
        AppTarget("Porter Driver", "com.theporter.driverapp", listOf("Start Delivery", "Pick Up")),
        AppTarget("Swiggy Delivery", "in.swiggy.deliveryapp", listOf("Go Online")),
        AppTarget("Uber Driver", "com.ubercab.driver", listOf("ACCEPT RIDE", "Start Ride"))
    )

    fun findByPackage(pkg: String): AppTarget? = ALL.firstOrNull { it.packageName == pkg }

    fun acceptVariantsFor(target: AppTarget): List<String> =
        (target.acceptTextVariants + UNIVERSAL_ACCEPT_VARIANTS).distinct()
}
