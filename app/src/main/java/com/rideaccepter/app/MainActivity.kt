package com.rideaccepter.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Dashboard
import androidx.compose.material.icons.filled.FilterList
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.sp
import androidx.compose.ui.graphics.Color
import androidx.lifecycle.viewmodel.compose.viewModel
import com.rideaccepter.app.ui.AppTab
import com.rideaccepter.app.ui.MainViewModel
import com.rideaccepter.app.ui.screens.DashboardScreen
import com.rideaccepter.app.ui.screens.FiltersScreen
import com.rideaccepter.app.ui.screens.HistoryScreen
import com.rideaccepter.app.ui.screens.ProfileScreen
import com.rideaccepter.app.ui.theme.NeonRed
import com.rideaccepter.app.ui.theme.RideAccepterTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            RideAccepterTheme { MainRoot() }
        }
    }
}

@Composable
fun MainRoot(vm: MainViewModel = viewModel()) {
    val tab by vm.currentTab.collectAsState()
    val icons = mapOf(
        AppTab.Dashboard to Icons.Filled.Dashboard,
        AppTab.Filter to Icons.Filled.FilterList,
        AppTab.History to Icons.Filled.History,
        AppTab.Profile to Icons.Filled.Person
    )
    Scaffold(
        bottomBar = {
            NavigationBar(containerColor = Color(0xFF1A0D12)) {
                AppTab.values().forEach { t ->
                    NavigationBarItem(
                        selected = tab == t,
                        onClick = { vm.setTab(t) },
                        icon = { Icon(icons[t]!!, t.label) },
                        label = { Text(t.label, fontSize = 10.sp) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = Color.White,
                            selectedTextColor = NeonRed,
                            indicatorColor = NeonRed,
                            unselectedIconColor = Color.Gray,
                            unselectedTextColor = Color.Gray
                        )
                    )
                }
            }
        }
    ) { padding ->
        androidx.compose.foundation.layout.Box(Modifier.padding(padding)) {
            when (tab) {
                AppTab.Dashboard -> DashboardScreen(vm)
                AppTab.Filter -> FiltersScreen(vm)
                AppTab.History -> HistoryScreen(vm)
                AppTab.Profile -> ProfileScreen(vm)
            }
        }
    }
}
