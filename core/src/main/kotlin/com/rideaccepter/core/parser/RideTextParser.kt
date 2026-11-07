package com.rideaccepter.core.parser

import com.rideaccepter.core.model.AppTarget
import com.rideaccepter.core.model.RideDetails

/**
 * Parses a ride offer from screen leaf texts (AccessibilityNodeInfo texts).
 * Clean-room implementation of the behaviour in ENGINE_SPEC.md §3.
 * Fix vs original: action words (Accept/Reject) are stripped from addresses —
 * the original saved "..., India, Reject" into history.
 */
object RideTextParser {

    private val fareRegex = Regex("""(?:₹|Rs\.?|INR)\s*([0-9][0-9,]*(?:\.[0-9]+)?)""", RegexOption.IGNORE_CASE)
    private val labelledFareRegex = Regex("""(?:Estimated\s+)?Fare\s*[:\-]?\s*(?:₹|Rs\.?)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)""", RegexOption.IGNORE_CASE)
    private val kmRegex = Regex("""([0-9]+(?:\.[0-9]+)?)\s*km""", RegexOption.IGNORE_CASE)
    private val actionWords = listOf("accept", "reject", "view >", "accept ride", "accept order")

    fun parse(leafTexts: List<String>, target: AppTarget): RideDetails {
        val lines = leafTexts.map { it.trim() }.filter { it.isNotEmpty() }

        // ---- fare: first ₹/Rs match, else labelled "Fare ..." line
        var fare: Double? = null
        var fareText: String? = null
        for (line in lines) {
            val m = fareRegex.find(line) ?: labelledFareRegex.find(line)
            if (m != null) {
                fare = m.groupValues[1].replace(",", "").toDoubleOrNull()
                fareText = m.value.trim()
                if (fare != null) break
            }
        }

        // ---- distances: first km = pickup distance, second = trip distance
        val kms = lines.flatMap { line -> kmRegex.findAll(line).map { it.groupValues[1].toDouble() }.toList() }

        // ---- addresses: longest non-action, non-fare, non-km-only lines
        val addressCandidates = lines.filter { line ->
            val low = line.lowercase()
            line.length >= 18 &&
                !fareRegex.containsMatchIn(line) &&
                actionWords.none { low == it } &&
                !low.startsWith("pickup") && !low.startsWith("drop") &&
                !low.contains("total earnings")
        }.map { cleanAddress(it) }

        return RideDetails(
            appName = target.name,
            appPackage = target.packageName,
            fareAmount = fare,
            fareText = fareText,
            pickupKm = kms.getOrNull(0),
            tripKm = kms.getOrNull(1),
            pickupText = addressCandidates.getOrNull(0),
            dropoffText = addressCandidates.getOrNull(1),
            rawTexts = lines
        )
    }

    /** Remove trailing action words the target UI merged into the address node. */
    fun cleanAddress(text: String): String {
        var out = text.trim()
        for (w in actionWords) {
            out = out.replace(Regex(""",?\s*${Regex.escape(w)}\s*$""", RegexOption.IGNORE_CASE), "")
        }
        return out.trim().trimEnd(',')
    }
}
