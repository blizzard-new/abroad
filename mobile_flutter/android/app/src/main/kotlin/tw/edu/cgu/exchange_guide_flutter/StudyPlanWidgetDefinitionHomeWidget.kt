package tw.edu.cgu.exchange_guide_flutter

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.DpSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.glance.*
import androidx.glance.action.clickable
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.SizeMode
import androidx.glance.appwidget.action.actionStartActivity
import androidx.glance.appwidget.provideContent
import androidx.glance.color.ColorProvider
import androidx.glance.layout.*
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import es.antonborri.home_widget.HomeWidgetGlanceState
import es.antonborri.home_widget.HomeWidgetGlanceStateDefinition

/** Cached, account-scoped snapshot; opening the app refreshes cloud state. */
class StudyPlanWidgetDefinitionHomeWidget : GlanceAppWidget() {
    override val stateDefinition = HomeWidgetGlanceStateDefinition()
    override val sizeMode = SizeMode.Responsive(setOf(DpSize(140.dp, 140.dp), DpSize(280.dp, 140.dp)))

    override suspend fun provideGlance(context: Context, id: GlanceId) {
        provideContent { WidgetContent(context, currentState()) }
    }

    @Composable
    private fun WidgetContent(context: Context, state: HomeWidgetGlanceState) {
        val prefs = state.preferences
        val prefix = "home_widget.StudyPlanWidgetDefinition"
        val wide = LocalSize.current.width >= 280.dp
        val tasks = (prefs.getString("$prefix.tasks", "") ?: "").split("\n").filter { it.isNotBlank() }.take(3)
        val ink = ColorProvider(day = Color(0xFF15212C), night = Color(0xFFF6FAFC))
        val secondary = ColorProvider(day = Color(0xFF596875), night = Color(0xFFB8C7D0))
        val accent = ColorProvider(day = Color(0xFF087C8C), night = Color(0xFF74D6DE))
        val open = Intent(context, MainActivity::class.java).apply {
            action = Intent.ACTION_VIEW
            data = Uri.parse("tw.uniway.app://journey")
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        GlanceTheme {
            Column(modifier = GlanceModifier.fillMaxSize()
                .background(ColorProvider(day = Color(0xFFF1F9F8), night = Color(0xFF17232C)))
                .padding(16.dp).clickable(actionStartActivity(open))) {
                Text("UniWay · 我的交換", style = TextStyle(color = accent, fontSize = 12.sp, fontWeight = FontWeight.Bold))
                Spacer(GlanceModifier.height(10.dp))
                Row(modifier = GlanceModifier.defaultWeight()) {
                    Column(modifier = GlanceModifier.defaultWeight()) {
                        Text(prefs.getString("$prefix.nextTitle", "登入後帶上你的交換計畫") ?: "", maxLines = 2,
                            style = TextStyle(color = ink, fontSize = 16.sp, fontWeight = FontWeight.Bold))
                        Spacer(GlanceModifier.height(6.dp))
                        Text(prefs.getString("$prefix.nextDateLabel", "點一下開始") ?: "", maxLines = 2,
                            style = TextStyle(color = secondary, fontSize = 11.sp))
                    }
                    if (wide && tasks.isNotEmpty()) {
                        Spacer(GlanceModifier.width(16.dp))
                        Column(modifier = GlanceModifier.defaultWeight()) {
                            tasks.forEach { task ->
                                Text("○ $task", maxLines = 1, style = TextStyle(color = ink, fontSize = 11.sp))
                                Spacer(GlanceModifier.height(5.dp))
                            }
                        }
                    }
                }
                Text(listOf(prefs.getString("$prefix.progressLabel", "尚未登入"), prefs.getString("$prefix.updatedLabel", ""))
                    .filter { !it.isNullOrBlank() }.joinToString(" · "), maxLines = 1,
                    style = TextStyle(color = accent, fontSize = 10.sp))
            }
        }
    }
}
