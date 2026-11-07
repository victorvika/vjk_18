package com.rideaccepter.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val BlackBackground = Color(0xFF0A0A0F)
val DarkGreyCard = Color(0xFF14141C)
val BorderGray = Color(0xFF2A2A35)
val NeonRed = Color(0xFFE6002E)
val NeonRedDark = Color(0xFF8F001D)
val NeonGreen = Color(0xFF22C55E)
val AccentGray = Color(0xFF9CA3AF)
val WhiteText = Color(0xFFFFFFFF)

private val DarkColors = darkColorScheme(
    primary = NeonRed,
    onPrimary = WhiteText,
    background = BlackBackground,
    onBackground = WhiteText,
    surface = DarkGreyCard,
    onSurface = WhiteText,
    surfaceVariant = DarkGreyCard,
    outline = BorderGray,
    secondary = NeonGreen
)

@Composable
fun RideAccepterTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = DarkColors, content = content)
}
