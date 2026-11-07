package com.rideaccepter.app.ui.screens

import android.content.Intent
import android.net.Uri
import android.provider.Settings
import androidx.compose.foundation.BorderStroke
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
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.rideaccepter.app.engine.StatusChecks
import com.rideaccepter.app.ui.MainViewModel
import com.rideaccepter.app.ui.theme.BorderGray
import com.rideaccepter.app.ui.theme.DarkGreyCard
import com.rideaccepter.app.ui.theme.NeonGreen
import com.rideaccepter.app.ui.theme.NeonRed
import com.rideaccepter.core.target.AppTargets

@Composable
fun SectionTitle(text: String) {
    Text(text, color = NeonRed, fontWeight = FontWeight.Bold, fontSize = 14.sp,
        modifier = Modifier.padding(top = 20.dp, bottom = 8.dp))
}

@Composable
fun StatusRow(label: String, value: String, ok: Boolean) {
    Row(Modifier.fillMaxWidth().padding(vertical = 6.dp), horizontalArrangement = Arrangement.SpaceBetween) {
        Column {
            Text(label, color = Color(0xFFB9B9C4), fontSize = 13.sp)
            Text((if (ok) "● " else "○ ") + value,
                color = if (ok) NeonGreen else Color.Gray, fontWeight = FontWeight.Bold, fontSize = 14.sp)
        }
        Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF2A1218)),
            shape = RoundedCornerShape(8.dp)) {
            Text(if (ok) "GRANTED" else "MISSING", color = Color.White, fontSize = 11.sp,
                fontWeight = FontWeight.Bold, modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp))
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(vm: MainViewModel) {
    val ctx = LocalContext.current
    val running by vm.engineRunning.collectAsState()
    val decision by vm.lastDecision.collectAsState()
    val selectedPkg by vm.selectedPackage.collectAsState()


    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)
    ) {
        // Header card
        Card(
            Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = DarkGreyCard),
            border = BorderStroke(1.5.dp, NeonRed), shape = RoundedCornerShape(20.dp)
        ) {
            Column(Modifier.padding(18.dp)) {
                Text("RideAccepter", fontSize = 24.sp, fontWeight = FontWeight.Bold)
                Text("Automatic High-Speed Assistant", color = NeonRed, fontSize = 14.sp)
                Spacer(Modifier.height(10.dp))
                Text("● ${if (running) decision else "IDLE"}", color = if (running) NeonGreen else Color.Gray)
            }
        }

        // Free build card — no subscription, no expiry
        Card(
            Modifier.fillMaxWidth().padding(top = 14.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF0D1F1A)),
            border = BorderStroke(1.5.dp, NeonGreen), shape = RoundedCornerShape(20.dp)
        ) {
            Column(Modifier.padding(18.dp)) {
                Text("✓  FREE BUILD — NO SUBSCRIPTION", color = NeonGreen, fontSize = 15.sp, fontWeight = FontWeight.Bold)
                Text("No plan, no expiry, no payment. Engine runs whenever you press START OVERLAY.",
                    color = Color.Gray, fontSize = 13.sp, modifier = Modifier.padding(top = 6.dp))
                Text("Status: " + (if (running) decision else "IDLE"),
                    color = if (running) NeonGreen else Color.Gray, modifier = Modifier.padding(top = 6.dp))
            }
        }

        SectionTitle("SYSTEM STATUS")
        Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = DarkGreyCard),
            shape = RoundedCornerShape(16.dp)) {
            Column(Modifier.padding(16.dp)) {
                val acc = StatusChecks.isAccessibilityEnabled(ctx)
                val overlay = StatusChecks.isOverlayGranted(ctx)
                val shizuku = StatusChecks.isShizukuInstalled(ctx)
                StatusRow("Accessibility Service", if (acc) "ENABLED" else "DISABLED", acc)
                StatusRow("Draw Overlays", if (overlay) "GRANTED" else "NOT GRANTED", overlay)
                StatusRow("Shizuku App", if (shizuku) "INSTALLED" else "NOT INSTALLED", shizuku)
                StatusRow("Target App (${vm.targetName()})",
                    if (StatusChecks.isTargetInstalled(ctx, selectedPkg)) "INSTALLED" else "NOT INSTALLED",
                    StatusChecks.isTargetInstalled(ctx, selectedPkg))
                if (!acc) {
                    Button(onClick = {
                        ctx.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                    }, Modifier.fillMaxWidth()) { Text("Open Accessibility Settings") }
                }
                if (!overlay) {
                    OutlinedButton(onClick = {
                        ctx.startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                            Uri.parse("package:${ctx.packageName}")))
                    }, Modifier.fillMaxWidth()) { Text("Grant Overlay Permission") }
                }
            }
        }

        Row(Modifier.fillMaxWidth().padding(top = 16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(
                onClick = { vm.startOverlay() }, enabled = true,
                modifier = Modifier.weight(1f).height(54.dp),
                colors = ButtonDefaults.buttonColors(containerColor = NeonRed),
                shape = RoundedCornerShape(14.dp)
            ) { Icon(Icons.Filled.PlayArrow, null); Text(" START OVERLAY", fontWeight = FontWeight.Bold) }
            OutlinedButton(
                onClick = { vm.stopAll() },
                modifier = Modifier.weight(1f).height(54.dp),
                border = BorderStroke(1.dp, BorderGray), shape = RoundedCornerShape(14.dp)
            ) { Icon(Icons.Filled.Stop, null, tint = NeonRed); Text(" STOP", color = Color.White) }
        }

        SectionTitle("CLICK CONFIGURATION")
        Text("Target Driver Application", fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(bottom = 8.dp))
        var expanded by remember { mutableStateOf(false) }
        ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
            OutlinedTextField(
                value = vm.targetName(), onValueChange = {}, readOnly = true,
                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
                modifier = Modifier.menuAnchor().fillMaxWidth()
            )
            ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                AppTargets.ALL.forEach { target ->
                    DropdownMenuItem(
                        text = { Text("${target.name}  (${target.packageName})") },
                        onClick = { vm.selectTarget(target.packageName); expanded = false }
                    )
                }
            }
        }
        Text("Test loop: select Mock Ride Simulator, press START OVERLAY, then open the Simulator app and generate a ride.",
            color = Color.Gray, fontSize = 12.sp, modifier = Modifier.padding(top = 12.dp))
        Spacer(Modifier.height(24.dp))
    }
}
