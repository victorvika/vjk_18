package com.rideaccepter.core

import com.rideaccepter.core.model.FilterConfig
import com.rideaccepter.core.model.FilterDecision
import com.rideaccepter.core.parser.RideTextParser
import com.rideaccepter.core.rules.FilterRuleEngine
import com.rideaccepter.core.target.AppTargets

/**
 * Framework-free verification runner (no Android SDK / JUnit needed):
 *   kotlinc core/src/main/kotlin core/src/test/kotlin -include-runtime -d verify.jar
 *   java -jar verify.jar
 * In Android Studio the same scenarios can be wrapped as JUnit tests.
 */
private var failures = 0
private fun check(name: String, cond: Boolean, detail: String = "") {
    println((if (cond) "PASS  " else "FAIL  ") + name + if (detail.isNotEmpty()) "  -> $detail" else "")
    if (!cond) failures++
}

fun main() {
    val rapido = AppTargets.findByPackage("com.rapido.rider")!!

    // Screenshot ride #1: ₹100, 1.0 km pickup + 3.2 km trip, Sembakkam -> Rajakilpakkam
    val ride = RideTextParser.parse(
        listOf(
            "₹100", "1.0 km away", "3.2 km trip",
            "Sembakkam - 3A, MF Nagar, Thirumalai Nagar, Sembakkam, Chennai - 600073",
            "Rajakilpakkam - St. Joseph's Church, Chitlapakkam Main Road, Chennai, Reject",
            "Accept"
        ), rapido
    )
    check("fare parsed", ride.fareAmount == 100.0, "fare=${ride.fareAmount}")
    check("kms parsed", ride.pickupKm == 1.0 && ride.tripKm == 3.2, ride.distanceSummary)
    check("address cleaned (no 'Reject')", ride.dropoffText?.contains("Reject") == false, ride.dropoffText ?: "")

    val defaultConfig = FilterConfig() // fare 60..1000 ON, rest OFF (screenshot state)
    check("₹100 accepted", FilterRuleEngine.evaluate(ride, defaultConfig) is FilterDecision.Accept)
    check("₹40 ignored", FilterRuleEngine.evaluate(ride.copy(fareAmount = 40.0), defaultConfig) is FilterDecision.Ignore)
    check("₹60 boundary accepted", FilterRuleEngine.evaluate(ride.copy(fareAmount = 60.0), defaultConfig) is FilterDecision.Accept)
    check("₹1000 boundary accepted", FilterRuleEngine.evaluate(ride.copy(fareAmount = 1000.0), defaultConfig) is FilterDecision.Accept)
    check("₹1001 ignored", FilterRuleEngine.evaluate(ride.copy(fareAmount = 1001.0), defaultConfig) is FilterDecision.Ignore)

    val noZone = defaultConfig.copy(noZoneEnabled = true, noZones = listOf("sembakkam"))
    check("No-Zone blocks Sembakkam", FilterRuleEngine.evaluate(ride, noZone) is FilterDecision.Ignore)
    val zone = defaultConfig.copy(driverZoneEnabled = true, driverZones = listOf("Rajakilpakkam"))
    check("Driver-Zone allows Rajakilpakkam", FilterRuleEngine.evaluate(ride, zone) is FilterDecision.Accept)
    val zoneMiss = defaultConfig.copy(driverZoneEnabled = true, driverZones = listOf("Delhi"))
    check("Driver-Zone blocks outside", FilterRuleEngine.evaluate(ride, zoneMiss) is FilterDecision.Ignore)

    check("normalize", FilterRuleEngine.normalize("  Seven  Wells, Chennai! ") == "seven wells chennai")

    println(if (failures == 0) "\nALL CHECKS PASSED" else "\n$failures CHECK(S) FAILED")
    if (failures > 0) kotlin.system.exitProcess(1)
}
