package com.rideaccepter.core.model

/** One ride offer parsed from the target app's screen (leaf-node texts). */
data class RideDetails(
    val appName: String,
    val appPackage: String,
    val fareAmount: Double? = null,
    val fareText: String? = null,
    val pickupKm: Double? = null,
    val tripKm: Double? = null,
    val pickupText: String? = null,
    val dropoffText: String? = null,
    val rawTexts: List<String> = emptyList()
) {
    /** Screenshot format: "1.0 km + 3.2 km" (pickup + trip). */
    val distanceSummary: String
        get() = listOfNotNull(pickupKm, tripKm).joinToString(" + ") { "%.1f km".format(it) }
}

data class FilterConfig(
    val fareEnabled: Boolean = true,
    val minFare: Double = 60.0,
    val maxFare: Double = 1000.0,
    val distanceEnabled: Boolean = false,
    val minDistanceKm: Double = 0.0,
    val maxDistanceKm: Double = 100.0,
    val driverZoneEnabled: Boolean = false,
    val driverZones: List<String> = emptyList(),
    val noZoneEnabled: Boolean = false,
    val noZones: List<String> = emptyList()
)

sealed class FilterDecision {
    data object Accept : FilterDecision()
    data class Ignore(val reason: String) : FilterDecision()
}

data class AppTarget(
    val name: String,
    val packageName: String,
    val acceptTextVariants: List<String> = emptyList(),
    val fareTextVariants: List<String> = listOf("₹", "Rs.", "INR", "Fare", "Estimated Fare")
)

/** History record (mirrors Room entity fields in the app module). */
data class AcceptedRide(
    val id: Long = 0,
    val appName: String,
    val fareAmount: Double,
    val fareText: String,
    val pickupKm: Double?,
    val tripKm: Double?,
    val pickupText: String?,
    val dropoffText: String?,
    val timestampMs: Long
)
