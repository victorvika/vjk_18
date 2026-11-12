package com.vjk.goldpulse.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// GoldPulse palette — dark by default, tuned for a trading desk at night.
val Gold = Color(0xFFF5C451)
val GoldDim = Color(0xFFB8912F)
val Bull = Color(0xFF26A69A)
val Bear = Color(0xFFEF5350)
val Bg = Color(0xFF0B0E11)
val Surface = Color(0xFF151A21)
val SurfaceHi = Color(0xFF1E252E)
val TextPrimary = Color(0xFFE8EDF2)
val TextMuted = Color(0xFF8A97A6)
val Border = Color(0xFF2A333E)

private val DarkScheme = darkColorScheme(
    primary = Gold,
    onPrimary = Color(0xFF1A1405),
    secondary = GoldDim,
    background = Bg,
    onBackground = TextPrimary,
    surface = Surface,
    onSurface = TextPrimary,
    surfaceVariant = SurfaceHi,
    onSurfaceVariant = TextMuted,
    error = Bear,
)

private val LightScheme = lightColorScheme(
    primary = GoldDim,
    background = Color(0xFFFAFAF7),
    surface = Color.White,
    error = Bear,
)

@Composable
fun GoldPulseTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkScheme else LightScheme,
        content = content,
    )
}
