package com.rideaccepter.core.rules

import com.rideaccepter.core.model.FilterConfig
import com.rideaccepter.core.model.FilterDecision
import com.rideaccepter.core.model.RideDetails

/**
 * Rule engine — truth table from ENGINE_SPEC.md §2 step 5.
 * Empty allow-list = all locations allowed (matches original UI note).
 */
object FilterRuleEngine {

    fun evaluate(ride: RideDetails, config: FilterConfig): FilterDecision {
        if (config.fareEnabled) {
            val fare = ride.fareAmount
                ?: return FilterDecision.Ignore("Fare not detected")
            if (fare < config.minFare || fare > config.maxFare) {
                return FilterDecision.Ignore("Fare out of range: ₹${fare.toInt()} (allowed ₹${config.minFare.toInt()}–₹${config.maxFare.toInt()})")
            }
        }
        if (config.distanceEnabled) {
            val trip = ride.tripKm
                ?: return FilterDecision.Ignore("Trip distance not detected")
            if (trip < config.minDistanceKm || trip > config.maxDistanceKm) {
                return FilterDecision.Ignore("Distance out of range: $trip km")
            }
        }
        val haystack = normalize(listOfNotNull(ride.pickupText, ride.dropoffText).joinToString(" "))
        if (config.noZoneEnabled) {
            config.noZones.firstOrNull { zone -> haystack.contains(normalize(zone)) }?.let {
                return FilterDecision.Ignore("Blocked location: $it")
            }
        }
        if (config.driverZoneEnabled && config.driverZones.isNotEmpty()) {
            val allowed = config.driverZones.any { zone -> haystack.contains(normalize(zone)) }
            if (!allowed) return FilterDecision.Ignore("Outside driver zones")
        }
        return FilterDecision.Accept
    }

    /** Lowercase, punctuation → space, collapse whitespace (original: normalizeText). */
    fun normalize(text: String): String =
        text.lowercase()
            .replace(Regex("[^a-z0-9\\s]"), " ")
            .replace(Regex("\\s+"), " ")
            .trim()
}
