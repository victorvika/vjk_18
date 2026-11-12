package com.vjk.goldpulse.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.TextMeasurer
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.unit.sp
import com.vjk.goldpulse.data.Candle
import com.vjk.goldpulse.strategy.lsms.LiquidityLevel
import com.vjk.goldpulse.strategy.lsms.LevelKind
import com.vjk.goldpulse.strategy.lsms.LevelSide
import com.vjk.goldpulse.ui.theme.Bear
import com.vjk.goldpulse.ui.theme.Bull
import com.vjk.goldpulse.ui.theme.Gold
import com.vjk.goldpulse.ui.theme.TextMuted
import kotlin.math.max
import kotlin.math.min

/**
 * Candlestick chart drawn with Compose Canvas.
 *
 * No charting library: Vico/MPAndroidChart both add dependencies and neither draws
 * liquidity levels or setup boxes, which is most of what this app needs to show.
 */
@Composable
fun CandleChart(
    candles: List<Candle>,
    levels: List<LiquidityLevel> = emptyList(),
    modifier: Modifier = Modifier,
    priceDigits: Int = 2,
) {
    if (candles.isEmpty()) return

    val measurer = rememberTextMeasurer()
    val labelStyle = TextStyle(fontSize = 9.sp, color = TextMuted)

    // Give the right edge room for a price axis.
    val axisWidth = 52f

    Canvas(modifier = modifier.fillMaxSize()) {
        val rightPad = axisWidth
        val plotWidth = size.width - rightPad
        if (plotWidth <= 0f) return@Canvas

        val visible = candles.takeLast(120)
        val highs = visible.map { it.high }
        val lows = visible.map { it.low }
        var maxP = highs.maxOrNull() ?: return@Canvas
        var minP = lows.minOrNull() ?: return@Canvas

        // Levels can sit outside the candle range; include them so lines are visible.
        levels.forEach {
            if (it.price > maxP) maxP = it.price
            if (it.price < minP) minP = it.price
        }

        val pad = (maxP - minP) * 0.06
        if (pad > 0) {
            maxP += pad
            minP -= pad
        }
        val span = (maxP - minP).takeIf { it > 0.0 } ?: return@Canvas

        fun yOf(price: Double): Float =
            ((maxP - price) / span * size.height).toFloat()

        val slot = plotWidth / visible.size
        val bodyW = max(1.5f, slot * 0.62f)

        // ---- grid + price axis ------------------------------------------
        val gridLines = 5
        for (g in 0..gridLines) {
            val price = minP + span * g / gridLines
            val y = yOf(price)
            drawLine(
                color = Color(0xFF20262E),
                start = Offset(0f, y),
                end = Offset(plotWidth, y),
                strokeWidth = 1f,
            )
            val text = measurer.measure(
                text = formatPrice(price, priceDigits),
                style = labelStyle,
            )
            drawText(text, topLeft = Offset(plotWidth + 6f, y - text.size.height / 2f))
        }

        // ---- candles ----------------------------------------------------
        visible.forEachIndexed { i, c ->
            val cx = i * slot + slot / 2f
            val bullish = c.close >= c.open
            val color = if (bullish) Bull else Bear

            drawLine(
                color = color,
                start = Offset(cx, yOf(c.high)),
                end = Offset(cx, yOf(c.low)),
                strokeWidth = 1f,
            )

            val yOpen = yOf(c.open)
            val yClose = yOf(c.close)
            val top = min(yOpen, yClose)
            val height = max(1f, kotlin.math.abs(yClose - yOpen))
            drawRect(
                color = color,
                topLeft = Offset(cx - bodyW / 2f, top),
                size = Size(bodyW, height),
            )
        }

        // ---- liquidity levels -------------------------------------------
        // Only draw labels for key levels; swing highs/lows would clutter a phone.
        levels.takeLast(14).forEach { lv ->
            if (lv.price < minP || lv.price > maxP) return@forEach
            val y = yOf(lv.price)
            val color = when (lv.side) {
                LevelSide.BUY_SIDE -> Gold.copy(alpha = 0.55f)
                LevelSide.SELL_SIDE -> Color(0xFF4FC3F7).copy(alpha = 0.55f)
            }
            drawLine(
                color = color,
                start = Offset(0f, y),
                end = Offset(plotWidth, y),
                strokeWidth = if (lv.kind == LevelKind.EQUAL_HIGHS || lv.kind == LevelKind.EQUAL_LOWS) 2f else 1f,
            )
            if (lv.kind.isKey) {
                val t = measurer.measure(text = shortLabel(lv.kind), style = labelStyle)
                drawText(t, topLeft = Offset(2f, y - t.size.height - 1f))
            }
        }

        // ---- last close marker ------------------------------------------
        val lastClose = visible.last().close
        val yLast = yOf(lastClose)
        drawLine(
            color = Gold,
            start = Offset(0f, yLast),
            end = Offset(plotWidth, yLast),
            strokeWidth = 1f,
            pathEffect = androidx.compose.ui.graphics.PathEffect.dashPathEffect(floatArrayOf(8f, 6f)),
        )
        val priceLabel = measurer.measure(
            text = formatPrice(lastClose, priceDigits),
            style = TextStyle(fontSize = 10.sp, color = Color(0xFF1A1405)),
        )
        drawRect(
            color = Gold,
            topLeft = Offset(plotWidth + 2f, yLast - priceLabel.size.height / 2f - 2f),
            size = Size(axisWidth - 4f, priceLabel.size.height + 4f),
        )
        drawText(
            priceLabel,
            topLeft = Offset(plotWidth + 6f, yLast - priceLabel.size.height / 2f),
        )
    }
}

/** Overlay for the most recent setup: entry, stop and target. */
@Composable
fun SetupOverlay(
    entry: Double?,
    stop: Double?,
    target: Double?,
    candles: List<Candle>,
    modifier: Modifier = Modifier,
) {
    if (entry == null || stop == null || target == null || candles.isEmpty()) return

    val visible = candles.takeLast(120)
    val maxP = maxOf(
        visible.maxOf { it.high },
        maxOf(entry, stop, target),
    )
    val minP = minOf(
        visible.minOf { it.low },
        minOf(entry, stop, target),
    )
    val pad = (maxP - minP) * 0.06
    val top = maxP + pad
    val span = (top - (minP - pad)).takeIf { it > 0 } ?: return
    val plotWidth = 0.92f // leave room for the axis

    Canvas(modifier = modifier.fillMaxSize()) {
        fun yOf(p: Double) = ((top - p) / span * size.height).toFloat()
        val x2 = size.width * plotWidth

        fun band(price: Double, color: Color, dashed: Boolean) {
            val y = yOf(price)
            if (y < 0f || y > size.height) return
            drawLine(
                color = color,
                start = Offset(0f, y),
                end = Offset(x2, y),
                strokeWidth = 1.6f,
                pathEffect = if (dashed) {
                    androidx.compose.ui.graphics.PathEffect.dashPathEffect(floatArrayOf(10f, 8f))
                } else null,
            )
        }

        band(entry, Gold, false)
        band(stop, Bear, true)
        band(target, Bull, true)

        // Shade the reward zone so the risk/reward is readable at a glance.
        val yE = yOf(entry)
        val yT = yOf(target)
        val path = Path().apply {
            moveTo(0f, yE)
            lineTo(x2, yE)
            lineTo(x2, yT)
            lineTo(0f, yT)
            close()
        }
        drawPath(path, color = Bull.copy(alpha = 0.10f))
        drawPath(path, color = Bull.copy(alpha = 0.35f), style = Stroke(width = 1f))
    }
}

private fun shortLabel(kind: LevelKind): String = when (kind) {
    LevelKind.PREV_DAY_HIGH -> "PDH"
    LevelKind.PREV_DAY_LOW -> "PDL"
    LevelKind.ASIA_HIGH -> "Asia H"
    LevelKind.ASIA_LOW -> "Asia L"
    LevelKind.EQUAL_HIGHS -> "EQH"
    LevelKind.EQUAL_LOWS -> "EQL"
    LevelKind.SWING_HIGH -> "SH"
    LevelKind.SWING_LOW -> "SL"
}

fun formatPrice(price: Double, digits: Int = 2): String =
    String.format("%,.${digits}f", price)

@Suppress("unused")
private fun TextMeasurer.unused() = Unit
