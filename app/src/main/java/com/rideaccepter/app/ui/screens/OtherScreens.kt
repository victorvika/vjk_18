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


/** Login — local demo (stores user id). Production: own /auth/login (docs/BACKEND_SPEC.md). */
@Composable
fun LoginScreen(vm: MainViewModel) {
    val userId by vm.userId.collectAsState()
    var idInput by remember { mutableStateOf("") }
    var passInput by remember { mutableStateOf("") }
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("LOGIN TO TERMINAL", fontSize = 26.sp, fontWeight = FontWeight.Bold)
        Text("Enter your unique User ID and Password to unlock terminal access.",
            color = Color.Gray, modifier = Modifier.padding(vertical = 10.dp))
        if (userId.isNotBlank()) {
            Text("Logged in as: $userId", color = NeonGreen, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(12.dp))
            OutlinedButton(onClick = { vm.logout() }) { Text("LOGOUT") }
        } else {
            OutlinedTextField(idInput, { idInput = it }, label = { Text("User ID") },
                modifier = Modifier.fillMaxWidth(), singleLine = true)
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(passInput, { passInput = it }, label = { Text("Password") },
                modifier = Modifier.fillMaxWidth(), singleLine = true)
            Spacer(Modifier.height(16.dp))
            Button(onClick = { vm.login(idInput) }, Modifier.fillMaxWidth().height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = NeonRed),
                shape = RoundedCornerShape(12.dp)) { Text("LOGIN", fontWeight = FontWeight.Bold) }
            Text("Demo mode: any User ID works, password is not verified locally.",
                color = Color.Gray, fontSize = 12.sp, modifier = Modifier.padding(top = 10.dp))
        }
    }
}

@Composable
fun ProfileScreen(vm: MainViewModel) {
    val userId by vm.userId.collectAsState()
    val total by vm.totalEarnings.collectAsState()
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("PROFILE", fontSize = 28.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(16.dp))
        Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = DarkGreyCard),
            shape = RoundedCornerShape(16.dp)) {
            Column(Modifier.padding(18.dp)) {
                Text("User ID: ${userId.ifBlank { "—" }}")
                Text("Subscription: None — free build, no plan needed", color = NeonGreen)
                Text("Lifetime auto-accepted earnings: ₹${total.toInt()}", color = NeonGreen)
                Text("App version: 0.2.0 (clean-room rebuild)", color = Color.Gray)
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
