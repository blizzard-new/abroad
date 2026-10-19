package tw.edu.cgu.exchangeguide.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import tw.edu.cgu.exchangeguide.ui.AppearanceMode

private val ColorOnBlueLight = androidx.compose.ui.graphics.Color(0xFF001D35)

private val LightColors = lightColorScheme(
    primary = BlueLight,
    onPrimary = SurfaceLight,
    primaryContainer = BlueContainerLight,
    onPrimaryContainer = ColorOnBlueLight,
    secondary = IndigoLight,
    tertiary = GreenLight,
    background = BackgroundLight,
    onBackground = TextLight,
    surface = SurfaceLight,
    onSurface = TextLight,
    surfaceVariant = SurfaceSecondaryLight,
    onSurfaceVariant = TextSecondaryLight,
    outline = OutlineLight,
    error = androidx.compose.ui.graphics.Color(0xFFBA1A1A),
)

private val DarkColors = darkColorScheme(
    primary = BlueDark,
    onPrimary = androidx.compose.ui.graphics.Color(0xFF003258),
    primaryContainer = BlueContainerDark,
    onPrimaryContainer = androidx.compose.ui.graphics.Color(0xFFD6E8FF),
    secondary = IndigoDark,
    tertiary = GreenDark,
    background = BackgroundDark,
    onBackground = TextDark,
    surface = SurfaceDark,
    onSurface = TextDark,
    surfaceVariant = SurfaceSecondaryDark,
    onSurfaceVariant = TextSecondaryDark,
    outline = OutlineDark,
    error = androidx.compose.ui.graphics.Color(0xFFFFB4AB),
)

@Composable
fun ExchangeGuideTheme(
    appearanceMode: AppearanceMode,
    // 關閉動態色彩，讓自訂的乳白粉彩主題在 Android 12+ 也生效
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit,
) {
    val darkTheme = when (appearanceMode) {
        AppearanceMode.System -> isSystemInDarkTheme()
        AppearanceMode.Light -> false
        AppearanceMode.Dark -> true
    }
    val context = LocalContext.current
    val colors = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && darkTheme -> dynamicDarkColorScheme(context)
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> dynamicLightColorScheme(context)
        darkTheme -> DarkColors
        else -> LightColors
    }

    MaterialTheme(
        colorScheme = colors,
        typography = ExchangeTypography,
        shapes = ExchangeShapes,
        content = content,
    )
}
