package com.rideaccepter.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.rideaccepter.app.ui.MainViewModel
import com.rideaccepter.app.ui.theme.DarkGreyCard
import com.rideaccepter.app.ui.theme.NeonGreen
import com.rideaccepter.app.ui.theme.NeonRed

@Composable
private fun FilterCard(
    title: String, subtitle: String, icon: String, enabled: Boolean,
    onToggle: (Boolean) -> Unit, content: @Composable () -> Unit
) {
    Card(Modifier.fillMaxWidth().padding(bottom = 14.dp),
        colors = CardDefaults.cardColors(containerColor = DarkGreyCard), shape = RoundedCornerShape(16.dp)) {
        Column(Modifier.padding(16.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("$icon  $title", fontWeight = FontWeight.Bold, fontSize = 17.sp)
                    Text(subtitle, color = Color.Gray, fontSize = 13.sp)
                }
                Switch(checked = enabled, onCheckedChange = onToggle,
                    colors = SwitchDefaults.colors(checkedThumbColor = Color.Black, checkedTrackColor = NeonRed))
            }
            content()
        }
    }
}

@Composable
fun FiltersScreen(vm: MainViewModel) {
    val f by vm.filters.collectAsState()
    var minFare by remember(f.minFare) { mutableStateOf(f.minFare.toInt().toString()) }
    var maxFare by remember(f.maxFare) { mutableStateOf(f.maxFare.toInt().toString()) }
    var showAddZone by remember { mutableStateOf<Boolean?>(null) } // null=hidden, true=blocked, false=allowed
    var zoneText by remember { mutableStateOf("") }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)) {
        Text("RIDE FILTERS", fontSize = 28.sp, fontWeight = FontWeight.Bold,
            modifier = Modifier.align(Alignment.CenterHorizontally))
        Text("Customize fare limits, trip distances, and location filters for auto accepting.",
            color = Color.Gray, modifier = Modifier.padding(vertical = 10.dp))

        FilterCard("Fare Value Filter", "Filter by total ride price", "₹", f.fareEnabled,
            { vm.updateFilters(f.copy(fareEnabled = it)) }) {
            Row(Modifier.fillMaxWidth().padding(top = 12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(minFare, { minFare = it.filter { c -> c.isDigit() } },
                    label = { Text("Min Fare (₹)") }, modifier = Modifier.weight(1f), singleLine = true)
                OutlinedTextField(maxFare, { maxFare = it.filter { c -> c.isDigit() } },
                    label = { Text("Max Fare (₹)") }, modifier = Modifier.weight(1f), singleLine = true)
            }
            Row(Modifier.fillMaxWidth().padding(top = 10.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("60" to "300", "100" to "500", "60" to "1000", "150" to "999").forEach { (lo, hi) ->
                    OutlinedButton(onClick = { minFare = lo; maxFare = hi; vm.saveFareRange(lo, hi) }) {
                        Text("₹$lo–$hi", fontSize = 12.sp)
                    }
                }
            }
            Button(onClick = { vm.saveFareRange(minFare, maxFare) },
                Modifier.fillMaxWidth().padding(top = 14.dp).height(50.dp),
                colors = ButtonDefaults.buttonColors(containerColor = NeonRed), shape = RoundedCornerShape(12.dp)) {
                Text("SAVE FARE RANGE", fontWeight = FontWeight.Bold)
            }
        }

        FilterCard("Distance (KM) Filter", "Filter by trip distance in km", "🚗", f.distanceEnabled,
            { vm.updateFilters(f.copy(distanceEnabled = it)) }) { }

        FilterCard("Driver Zone Filter", "Accept rides matching allowed locations", "📍", f.driverZoneEnabled,
            { vm.updateFilters(f.copy(driverZoneEnabled = it)) }) {
            Button(onClick = { showAddZone = false },
                Modifier.fillMaxWidth().padding(top = 12.dp).height(48.dp),
                colors = ButtonDefaults.buttonColors(containerColor = NeonRed), shape = RoundedCornerShape(12.dp)) {
                Text("+  Add Location", fontWeight = FontWeight.Bold)
            }
            if (f.driverZones.isEmpty()) {
                Text("No driver zone locations saved. All locations accepted when empty.",
                    color = Color.Gray, fontSize = 13.sp, modifier = Modifier.padding(top = 12.dp))
            }
            f.driverZones.forEach { zone ->
                ZoneRow(zone) { vm.removeZone(false, zone) }
            }
        }

        FilterCard("No Zone Filter", "Skip rides containing blocked locations", "🚫", f.noZoneEnabled,
            { vm.updateFilters(f.copy(noZoneEnabled = it)) }) {
            Button(onClick = { showAddZone = true },
                Modifier.fillMaxWidth().padding(top = 12.dp).height(48.dp),
                colors = ButtonDefaults.buttonColors(containerColor = NeonRed), shape = RoundedCornerShape(12.dp)) {
                Text("+  Add Blocked Location", fontWeight = FontWeight.Bold)
            }
            f.noZones.forEach { zone ->
                ZoneRow(zone) { vm.removeZone(true, zone) }
            }
        }
        Spacer(Modifier.height(20.dp))
    }

    if (showAddZone != null) {
        AlertDialog(
            onDismissRequest = { showAddZone = null },
            title = { Text(if (showAddZone == true) "Add Blocked Location" else "Add Location") },
            text = {
                OutlinedTextField(zoneText, { zoneText = it }, label = { Text("Location name (e.g. Seven Wells)") },
                    singleLine = true)
            },
            confirmButton = {
                TextButton(onClick = {
                    vm.addZone(showAddZone == true, zoneText); zoneText = ""; showAddZone = null
                }) { Text("ADD", color = NeonGreen) }
            },
            dismissButton = { TextButton(onClick = { showAddZone = null }) { Text("CANCEL") } }
        )
    }
}

@Composable
private fun ZoneRow(name: String, onDelete: () -> Unit) {
    Card(Modifier.fillMaxWidth().padding(top = 10.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Black), shape = RoundedCornerShape(10.dp)) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text("●  $name", color = Color.White)
            IconButton(onClick = onDelete) { Icon(Icons.Filled.Delete, "Delete", tint = NeonRed) }
        }
    }
}
