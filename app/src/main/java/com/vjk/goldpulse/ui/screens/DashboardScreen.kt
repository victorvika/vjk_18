package com.vjk.goldpulse.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.vjk.goldpulse.data.Interval
import com.vjk.goldpulse.data.MarketRepository
import com.vjk.goldpulse.strategy.lsms.GuardReason
import com.vjk.goldpulse.strategy.lsms.Instrument
import com.vjk.goldpulse.strategy.lsms.Setup
import com.vjk.goldpulse.strategy.lsms.Sizing
import com.vjk.goldpulse.strategy.lsms.Trend
import com.vjk.goldpulse.ui.formatPrice
import com.vjk.goldpulse.ui.theme.Bear
import com.vjk.goldpulse.ui.theme.Border
import com.vjk.goldpulse.ui.theme.Bull
import com.vjk.goldpulse.ui.theme.Gold
import com.vjk.goldpulse.ui.theme.Surface
import com.vjk.goldpulse.ui.theme.TextMuted
import com.vjk.goldpulse.ui.theme.TextPrimary

/** Compact stat tile used across the dashboard. */
@Composable
fun StatTile(
    label: String,
    value: String,
    valueColor: Color = TextPrimary,
    modifier: Modifier = Modifier,
    sub: String? = null,
) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(10.dp))
            .background(Surface)
            .border(1.dp, Border, RoundedCornerShape(10.dp))
            .padding(horizontal = 10.dp, vertical = 8.dp),
    ) {
        Text(label, fontSize = 10.sp, color = TextMuted, maxLines = 1)
        Spacer(Modifier.height(3.dp))
        Text(value, fontSize = 15.sp, fontWeight = FontWeight.SemiBold, color = valueColor, maxLines = 1)
        if (sub != null) {
            Spacer(Modifier.height(2.dp))
            Text(sub, fontSize = 9.sp, color = TextMuted, maxLines = 2)
        }
    }
}

@Composable
fun IntervalSelector(
    selected: Interval,
    onSelect: (Interval) -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Interval.entries.forEach { iv ->
            val active = iv == selected
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(7.dp))
                    .background(if (active) Gold else Surface)
                    .border(1.dp, if (active) Gold else Border, RoundedCornerShape(7.dp))
                    .padding(vertical = 6.dp),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    iv.label,
                    fontSize = 11.sp,
                    fontWeight = if (active) FontWeight.Bold else FontWeight.Normal,
                    color = if (active) Color(0xFF1A1405) else TextMuted,
                    textAlign = TextAlign.Center,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 1.dp),
                )
            }
        }
    }
}

@Composable
fun InstrumentToggle(
    selected: Instrument,
    onSelect: (Instrument) -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(modifier = modifier, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        listOf(Instrument.MGC, Instrument.GC).forEach { inst ->
            val active = inst.symbol == selected.symbol
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(7.dp))
                    .background(if (active) Gold else Surface)
                    .border(1.dp, if (active) Gold else Border, RoundedCornerShape(7.dp))
                    .padding(horizontal = 12.dp, vertical = 6.dp),
            ) {
                Text(
                    inst.symbol,
                    fontSize = 11.sp,
                    fontWeight = if (active) FontWeight.Bold else FontWeight.Normal,
                    color = if (active) Color(0xFF1A1405) else TextMuted,
                )
            }
        }
    }
}

/** Market summary strip: price, change, trend, phase. */
@Composable
fun MarketStrip(
    analysis: MarketRepository.Analysis,
    modifier: Modifier = Modifier,
) {
    val quote = analysis.quote
    val last = analysis.candles.lastOrNull()
    val price = quote?.price ?: last?.close ?: 0.0
    val change = quote?.changePercent ?: run {
        val first = analysis.candles.firstOrNull()?.close ?: price
        if (first > 0) (price - first) / first * 100.0 else 0.0
    }
    val up = change >= 0
    val trend = analysis.result.trend

    Column(modifier = modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.Bottom) {
            Text(
                formatPrice(price),
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                color = TextPrimary,
            )
            Spacer(Modifier.width(8.dp))
            Text(
                (if (up) "+" else "") + String.format("%.2f%%", change),
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium,
                color = if (up) Bull else Bear,
                modifier = Modifier.padding(bottom = 4.dp),
            )
            Spacer(Modifier.weight(1f))
            TrendChip(trend)
        }
        Spacer(Modifier.height(2.dp))
        Text(
            "${analysis.symbol}  ·  ${analysis.instrument.symbol} contract  ·  " +
                (if (quote?.delayed != false) "delayed ~10m" else "live"),
            fontSize = 10.sp,
            color = TextMuted,
        )
    }
}

@Composable
private fun TrendChip(trend: Trend) {
    val (label, color) = when (trend) {
        Trend.UPTREND -> "UPTREND" to Bull
        Trend.DOWNTREND -> "DOWNTREND" to Bear
        Trend.RANGE -> "RANGE" to Gold
    }
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))
            .background(color.copy(alpha = 0.15f))
            .border(1.dp, color.copy(alpha = 0.5f), RoundedCornerShape(6.dp))
            .padding(horizontal = 8.dp, vertical = 3.dp),
    ) {
        Text(label, fontSize = 9.sp, fontWeight = FontWeight.Bold, color = color)
    }
}

/** The risk panel — this is the part that keeps a prop account alive. */
@Composable
fun RiskPanel(
    setup: Setup?,
    instrument: Instrument,
    accountSize: Double,
    riskPercent: Double,
    maxLossLimit: Double,
    modifier: Modifier = Modifier,
) {
    val riskDollars = accountSize * riskPercent / 100.0
    val lossesLeft = Sizing.lossesRemaining(maxLossLimit, riskDollars)

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Surface)
            .border(1.dp, Border, RoundedCornerShape(12.dp))
            .padding(12.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("RISK", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Gold)
            Spacer(Modifier.weight(1f))
            Text(
                "$${riskDollars.toInt()} / trade  ·  ${riskPercent}%",
                fontSize = 10.sp,
                color = TextMuted,
            )
        }
        Spacer(Modifier.height(8.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            StatTile(
                "CONTRACTS",
                value = setup?.contracts?.toString() ?: "—",
                valueColor = if ((setup?.contracts ?: 0) > 0) TextPrimary else Bear,
                sub = instrument.symbol,
                modifier = Modifier.weight(1f),
            )
            StatTile(
                "STOP",
                value = setup?.let { "${String.format("%.1f", it.riskPoints)}pt" } ?: "—",
                sub = setup?.let { "$${it.riskDollars.toInt()} risk" },
                modifier = Modifier.weight(1f),
            )
            StatTile(
                "LOSSES LEFT",
                value = lossesLeft.toString(),
                valueColor = when {
                    lossesLeft <= 2 -> Bear
                    lossesLeft <= 4 -> Gold
                    else -> Bull
                },
                sub = "vs $${maxLossLimit.toInt()} MLL",
                modifier = Modifier.weight(1f),
            )
        }

        if (setup != null) {
            Spacer(Modifier.height(8.dp))
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .background(Color(0xFF10151B))
                    .padding(8.dp),
            ) {
                TradeLine("ENTRY", formatPrice(setup.entry), Gold, Modifier.weight(1f))
                TradeLine("STOP", formatPrice(setup.stopLoss), Bear, Modifier.weight(1f))
                TradeLine("TP1", setup.takeProfit1?.let { formatPrice(it) } ?: "—", Bull, Modifier.weight(1f))
                TradeLine("TP2", formatPrice(setup.takeProfit2), Bull, Modifier.weight(1f))
            }
            Spacer(Modifier.height(6.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    if (setup.isLong) "LONG" else "SHORT",
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    color = if (setup.isLong) Bull else Bear,
                )
                Spacer(Modifier.width(6.dp))
                Text(
                    "· ${setup.levelKind.name.replace('_', ' ').lowercase()} sweep" +
                        " · RR ${String.format("%.1f", setup.rrToLiquidity)}",
                    fontSize = 10.sp,
                    color = TextMuted,
                )
            }
        }
    }
}

@Composable
private fun TradeLine(label: String, value: String, color: Color, modifier: Modifier) {
    Column(modifier = modifier) {
        Text(label, fontSize = 8.sp, color = TextMuted)
        Text(value, fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = color)
    }
}

/** Guard banner: shows when the firm's loss limits say stop trading. */
@Composable
fun GuardBanner(reason: GuardReason?, netR: Double, lossesToday: Double) {
    val stopped = reason != null
    val color = if (stopped) Bear else Bull
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(9.dp))
            .background(color.copy(alpha = 0.10f))
            .border(1.dp, color.copy(alpha = 0.45f), RoundedCornerShape(9.dp))
            .padding(horizontal = 10.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .size(7.dp)
                .clip(RoundedCornerShape(50))
                .background(color),
        )
        Spacer(Modifier.width(8.dp))
        Column {
            Text(
                if (stopped) "STAND DOWN" else "CLEAR TO TRADE",
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                color = color,
            )
            Text(
                if (stopped) {
                    "Guard hit: ${reason!!.label} — no new setups until the next session"
                } else {
                    String.format("Session P&L %+.1fR · %d losses", netR, lossesToday.toInt())
                },
                fontSize = 9.sp,
                color = TextMuted,
            )
        }
    }
}

/** Where the setup stands relative to the five-stage checklist. */
@Composable
fun ChecklistRow(
    analysis: MarketRepository.Analysis,
    modifier: Modifier = Modifier,
) {
    val r = analysis.result
    val swept = r.sweeps.isNotEmpty()
    val structure = r.structureEvents.isNotEmpty()
    val bias = r.htfBias
    val setup = r.setups.lastOrNull()

    Column(modifier = modifier.fillMaxWidth().padding(horizontal = 2.dp)) {
        CheckLine("Sweep", if (swept) "${r.sweeps.size} detected" else "waiting", swept)
        CheckLine("Structure break", if (structure) r.lastEvent else "waiting", structure)
        CheckLine(
            "HTF bias",
            when (bias) {
                1 -> "bullish (4H)"
                -1 -> "bearish (4H)"
                else -> "neutral"
            },
            bias != 0,
        )
        CheckLine(
            "Setup",
            setup?.let { "RR ${String.format("%.1f", it.rrToLiquidity)}" } ?: (r.lastSkip?.toString() ?: "none"),
            setup != null,
        )
    }
}

@Composable
private fun CheckLine(label: String, detail: String, ok: Boolean) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .size(6.dp)
                .clip(RoundedCornerShape(50))
                .background(if (ok) Bull else Border),
        )
        Spacer(Modifier.width(7.dp))
        Text(label, fontSize = 10.sp, color = TextMuted, modifier = Modifier.width(96.dp))
        Text(
            detail,
            fontSize = 10.sp,
            color = if (ok) TextPrimary else TextMuted,
            maxLines = 1,
        )
    }
}
