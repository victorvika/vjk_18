package com.rideaccepter.app.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.rideaccepter.app.ui.MainViewModel
import com.rideaccepter.app.ui.theme.DarkGreyCard
import com.rideaccepter.app.ui.theme.NeonGreen
import com.rideaccepter.app.ui.theme.NeonRed



@Composable
fun ProfileScreen(vm: MainViewModel) {
    val total by vm.totalEarnings.collectAsState()
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("PROFILE", fontSize = 28.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(16.dp))
        Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = DarkGreyCard),
            shape = RoundedCornerShape(16.dp)) {
            Column(Modifier.padding(18.dp)) {
                Text("Subscription: None — free build, no plan needed", color = NeonGreen)
                Text("Lifetime auto-accepted earnings: ₹${total.toInt()}", color = NeonGreen)
                Text("App version: 0.3.0 (clean-room rebuild)", color = Color.Gray)
            }
        }
        Text(
            "Safety: automatic developer-options hiding (privileged shell commands) is NOT included. " +
                "Dashboard-la irundhu Developer Options settings open panni neengale manual-a off pannikalam. " +
                "Using automation in third-party driver apps can violate their terms and risk the driver account.",
            color = Color.Gray, fontSize = 12.sp, modifier = Modifier.padding(top = 16.dp)
        )
    }
}
