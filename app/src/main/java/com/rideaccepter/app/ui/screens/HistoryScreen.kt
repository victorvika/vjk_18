package com.rideaccepter.app.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
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
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun HistoryScreen(vm: MainViewModel) {
    val history by vm.history.collectAsState()
    val total by vm.totalEarnings.collectAsState()
    var confirmClear by remember { mutableStateOf(false) }
    val dateFmt = remember { SimpleDateFormat("dd MMM, hh:mm a", Locale.ENGLISH) }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = DarkGreyCard),
            border = BorderStroke(1.5.dp, NeonRed), shape = RoundedCornerShape(18.dp)) {
            Row(Modifier.fillMaxWidth().padding(18.dp),
                horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Column {
                    Text("TOTAL EARNINGS", color = NeonRed, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    Text("₹${total.toInt()}", fontSize = 36.sp, fontWeight = FontWeight.Bold)
                    Text("${history.size} rides auto-accepted", color = Color.Gray)
                }
                IconButton(onClick = { confirmClear = true }) {
                    Icon(Icons.Filled.Delete, "Clear history", tint = NeonRed)
                }
            }
        }

        Text("ACCEPTED RIDE LIST", color = Color.Gray, fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(top = 20.dp, bottom = 10.dp))

        if (history.isEmpty()) {
            Text("No rides yet. Start the overlay and accept a ride (try the Mock Simulator).",
                color = Color.Gray)
        }
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            items(history) { ride ->
                Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = DarkGreyCard),
                    shape = RoundedCornerShape(16.dp)) {
                    Column(Modifier.padding(16.dp)) {
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Card(colors = CardDefaults.cardColors(containerColor = NeonRed), shape = RoundedCornerShape(6.dp)) {
                                Text(ride.appName, fontSize = 12.sp, fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp))
                            }
                            Text(dateFmt.format(Date(ride.timestamp)), color = Color.Gray, fontSize = 12.sp)
                        }
                        Spacer(Modifier.height(8.dp))
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("₹${ride.fare.toInt()}", fontSize = 26.sp, fontWeight = FontWeight.Bold)
                            val dist = listOfNotNull(ride.pickupKm, ride.tripKm)
                                .joinToString(" + ") { "%.1f".format(it) }
                            if (dist.isNotEmpty()) Text("U $dist km", color = NeonRed, fontWeight = FontWeight.SemiBold)
                        }
                        ride.pickupLocation?.let {
                            Text("● PICKUP • ${ride.pickupKm ?: ""} km", color = NeonGreen, fontSize = 12.sp,
                                modifier = Modifier.padding(top = 10.dp))
                            Text(it)
                        }
                        ride.dropoffLocation?.let {
                            Text("■ DROPOFF • ${ride.tripKm ?: ""} km", color = NeonRed, fontSize = 12.sp,
                                modifier = Modifier.padding(top = 6.dp))
                            Text(it)
                        }
                    }
                }
            }
        }
    }

    if (confirmClear) {
        AlertDialog(onDismissRequest = { confirmClear = false },
            title = { Text("Clear history?") },
            text = { Text("Do you want to permanently clear all accepted ride history and reset earnings?") },
            confirmButton = { TextButton(onClick = { vm.clearHistory(); confirmClear = false }) { Text("CLEAR", color = NeonRed) } },
            dismissButton = { TextButton(onClick = { confirmClear = false }) { Text("CANCEL") } })
    }
}
