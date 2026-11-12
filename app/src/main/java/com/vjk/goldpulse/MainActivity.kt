package com.vjk.goldpulse

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.vjk.goldpulse.ui.CandleChart
import com.vjk.goldpulse.ui.GoldViewModel
import com.vjk.goldpulse.ui.SetupOverlay
import com.vjk.goldpulse.ui.screens.ChecklistRow
import com.vjk.goldpulse.ui.screens.GuardBanner
import com.vjk.goldpulse.ui.screens.IntervalSelector
import com.vjk.goldpulse.ui.screens.InstrumentToggle
import com.vjk.goldpulse.ui.screens.MarketStrip
import com.vjk.goldpulse.ui.screens.RiskPanel
import com.vjk.goldpulse.ui.theme.Bear
import com.vjk.goldpulse.ui.theme.Bg
import com.vjk.goldpulse.ui.theme.Border
import com.vjk.goldpulse.ui.theme.Gold
import com.vjk.goldpulse.ui.theme.GoldPulseTheme
import com.vjk.goldpulse.ui.theme.Surface
import com.vjk.goldpulse.ui.theme.TextMuted
import com.vjk.goldpulse.ui.theme.TextPrimary
import kotlinx.coroutines.delay

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            GoldPulseTheme {
                Box(Modifier.fillMaxSize().background(Bg)) {
                    AppRoot()
                }
            }
        }
    }
}

@Composable
private fun AppRoot(vm: GoldViewModel = viewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()

    // Refresh every 60s while the screen is open and auto-refresh is on.
    LaunchedEffect(state.autoRefresh, state.interval) {
        if (!state.autoRefresh) return@LaunchedEffect
        while (true) {
            delay(60_000)
            vm.refresh()
        }
    }

    val analysis = state.analysis
    val lastSetup = analysis?.result?.setups?.lastOrNull()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 14.dp)
            .verticalScroll(rememberScrollState()),
    ) {
        Spacer(Modifier.height(14.dp))

        // ---- header -----------------------------------------------------
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        Modifier
                            .size(8.dp)
                            .clip(RoundedCornerShape(50))
                            .background(Gold),
                    )
                    Spacer(Modifier.width(7.dp))
                    Text(
                        "GOLDPULSE",
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary,
                        letterSpacing = 1.5.sp,
                    )
                }
                Text(
                    "FundedNext · Rapid Daily 50K",
                    fontSize = 9.sp,
                    color = TextMuted,
                )
            }
            InstrumentToggle(
                selected = state.instrument,
                onSelect = vm::setInstrument,
            )
        }

        Spacer(Modifier.height(12.dp))

        if (state.error != null && analysis == null) {
            ErrorCard(state.error!!) { vm.refresh() }
            Spacer(Modifier.height(12.dp))
        }

        if (analysis == null) {
            Box(
                Modifier.fillMaxWidth().height(240.dp),
                contentAlignment = Alignment.Center,
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator(color = Gold, strokeWidth = 2.dp)
                    Spacer(Modifier.height(12.dp))
                    Text("Loading ${state.symbol} …", color = TextMuted, fontSize = 11.sp)
                }
            }
        } else {
            MarketStrip(analysis)
            Spacer(Modifier.height(10.dp))

            // ---- chart --------------------------------------------------
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(260.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(Surface)
                    .border(1.dp, Border, RoundedCornerShape(12.dp)),
            ) {
                CandleChart(
                    candles = analysis.candles,
                    levels = analysis.result.levels,
                    modifier = Modifier.padding(6.dp),
                )
                SetupOverlay(
                    entry = lastSetup?.entry,
                    stop = lastSetup?.stopLoss,
                    target = lastSetup?.takeProfit2,
                    candles = analysis.candles,
                    modifier = Modifier.padding(6.dp),
                )
                if (state.loading) {
                    Box(
                        Modifier.fillMaxSize().background(Color(0x33000000)),
                        contentAlignment = Alignment.Center,
                    ) {
                        CircularProgressIndicator(color = Gold, strokeWidth = 2.dp, modifier = Modifier.size(26.dp))
                    }
                }
            }

            Spacer(Modifier.height(8.dp))
            IntervalSelector(selected = state.interval, onSelect = vm::setInterval)

            Spacer(Modifier.height(10.dp))
            GuardBanner(
                reason = analysis.result.guardReason,
                netR = analysis.result.netRToday,
                lossesToday = analysis.result.lossesToday,
            )

            Spacer(Modifier.height(10.dp))
            RiskPanel(
                setup = lastSetup,
                instrument = state.instrument,
                accountSize = state.accountSize,
                riskPercent = state.riskPercent,
                maxLossLimit = state.accountSize * 0.04,
            )

            if (state.sizingHint != null) {
                Spacer(Modifier.height(6.dp))
                Text(
                    state.sizingHint!!,
                    fontSize = 9.sp,
                    color = Gold,
                    modifier = Modifier.padding(horizontal = 4.dp),
                )
            }

            Spacer(Modifier.height(12.dp))
            SectionCard("SIGNAL CHECKLIST") {
                ChecklistRow(analysis)
            }

            Spacer(Modifier.height(10.dp))
            SectionCard("RISK PER TRADE") {
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    listOf(0.25, 0.5, 0.75, 1.0).forEach { pct ->
                        val active = kotlin.math.abs(state.riskPercent - pct) < 0.01
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .clip(RoundedCornerShape(7.dp))
                                .background(if (active) Gold else Surface)
                                .border(1.dp, if (active) Gold else Border, RoundedCornerShape(7.dp))
                                .padding(vertical = 7.dp),
                            contentAlignment = Alignment.Center,
                        ) {
                            Text(
                                "${pct}%",
                                fontSize = 11.sp,
                                fontWeight = if (active) FontWeight.Bold else FontWeight.Normal,
                                color = if (active) Color(0xFF1A1405) else TextMuted,
                            )
                        }
                    }
                }
                Spacer(Modifier.height(8.dp))
                Text(
                    "Tap a percentage to resize every setup. Sizing uses " +
                        "${state.instrument.symbol} (\$${state.instrument.pointValue.toInt()}/point).",
                    fontSize = 9.sp,
                    color = TextMuted,
                )
            }

            Spacer(Modifier.height(10.dp))
            SessionNote()

            Spacer(Modifier.height(14.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                ActionButton(
                    label = if (state.loading) "REFRESHING…" else "REFRESH",
                    modifier = Modifier.weight(1f),
                    enabled = !state.loading,
                ) { vm.refresh() }
                ActionButton(
                    label = if (state.autoRefresh) "AUTO 60s ON" else "AUTO OFF",
                    modifier = Modifier.weight(1f),
                    active = state.autoRefresh,
                ) { vm.toggleAutoRefresh() }
            }
            Spacer(Modifier.height(20.dp))
        }
    }
}

@Composable
private fun SectionCard(title: String, content: @Composable () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Surface)
            .border(1.dp, Border, RoundedCornerShape(12.dp))
            .padding(12.dp),
    ) {
        Text(title, fontSize = 9.sp, fontWeight = FontWeight.Bold, color = Gold)
        Spacer(Modifier.height(8.dp))
        content()
    }
}

@Composable
private fun SessionNote() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(Color(0xFF10151B))
            .border(1.dp, Border, RoundedCornerShape(10.dp))
            .padding(10.dp),
    ) {
        Text("FUNDEDNEXT SESSION", fontSize = 9.sp, fontWeight = FontWeight.Bold, color = Gold)
        Spacer(Modifier.height(4.dp))
        Text(
            "Opens 5:00 PM CT · flat by 3:10 PM CT. No overnight or weekend holding — " +
                "positions are auto-closed at the cutoff.",
            fontSize = 9.sp,
            color = TextMuted,
            lineHeight = 13.sp,
        )
    }
}

@Composable
private fun ErrorCard(message: String, onRetry: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Bear.copy(alpha = 0.10f))
            .border(1.dp, Bear.copy(alpha = 0.4f), RoundedCornerShape(12.dp))
            .padding(12.dp),
    ) {
        Text("MARKET DATA UNAVAILABLE", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Bear)
        Spacer(Modifier.height(4.dp))
        Text(message, fontSize = 10.sp, color = TextMuted, lineHeight = 14.sp)
        Spacer(Modifier.height(8.dp))
        ActionButton("TRY AGAIN", Modifier.fillMaxWidth()) { onRetry() }
    }
}

@Composable
private fun ActionButton(
    label: String,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    active: Boolean = true,
    onClick: () -> Unit,
) {
    val fg = if (enabled && active) Gold else TextMuted
    Box(
        modifier = modifier
            .height(38.dp)
            .clip(RoundedCornerShape(9.dp))
            .background(if (active) Gold.copy(alpha = 0.14f) else Surface)
            .border(1.dp, if (active) Gold.copy(alpha = 0.5f) else Border, RoundedCornerShape(9.dp))
            .clickable(enabled = enabled, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Text(label, fontSize = 10.sp, fontWeight = FontWeight.Bold, color = fg)
    }
}
