// Generated with home_widget, then customized for the exchange plan experience.
package tw.edu.cgu.exchange_guide_flutter

import androidx.compose.runtime.Composable
import android.content.Context
import android.content.Intent
import androidx.compose.ui.graphics.Color
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.provideContent
import androidx.glance.background
import androidx.glance.currentState
import androidx.glance.layout.Box
import androidx.glance.layout.fillMaxSize
import androidx.glance.text.Text
import es.antonborri.home_widget.HomeWidgetGlanceState
import es.antonborri.home_widget.HomeWidgetGlanceStateDefinition
import androidx.glance.layout.Column
import androidx.glance.layout.Alignment
import androidx.glance.layout.Spacer
import androidx.glance.text.TextStyle
import androidx.glance.color.ColorProvider
import androidx.compose.ui.unit.sp
import androidx.glance.text.FontWeight
import androidx.glance.GlanceTheme
import androidx.glance.action.clickable
import androidx.glance.appwidget.action.actionStartActivity
import androidx.compose.ui.unit.dp
import androidx.glance.layout.padding

class StudyPlanWidgetDefinitionHomeWidget : GlanceAppWidget() {
  override val stateDefinition = HomeWidgetGlanceStateDefinition()

  override suspend fun provideGlance(context: Context, id: GlanceId) {
    provideContent { WidgetContent(context, currentState()) }
  }

  @Composable
  private fun WidgetContent(context: Context, currentState: HomeWidgetGlanceState) {
    val prefs = currentState.preferences
    val widgetData = StudyPlanWidgetDefinitionData.fromPreferences(prefs)
    GlanceTheme {
            Box(modifier = GlanceModifier.background(ColorProvider(day = Color(0xFFF7FAFB), night = Color(0xFF17232C))).padding(16.dp).fillMaxSize().clickable(actionStartActivity(Intent(context, MainActivity::class.java))), contentAlignment = Alignment.Center) {
                Column(modifier = GlanceModifier.fillMaxSize(), horizontalAlignment = Alignment.Start) {
                    Text(text = "交換計畫", style = TextStyle(color = ColorProvider(day = Color(0xFF087C8C), night = Color(0xFF74D6DE)), fontSize = 12.sp, fontWeight = FontWeight.Bold))
                    Spacer(modifier = GlanceModifier.defaultWeight())
                    Text(text = widgetData.nextTitle ?: "", style = TextStyle(color = ColorProvider(day = Color(0xFF15212C), night = Color(0xFFF6FAFC)), fontSize = 18.sp, fontWeight = FontWeight.Bold))
                    Spacer(modifier = GlanceModifier.defaultWeight())
                    Text(text = widgetData.nextDateLabel ?: "", style = TextStyle(color = ColorProvider(day = Color(0xFF596875), night = Color(0xFFB8C7D0)), fontSize = 12.sp, fontWeight = FontWeight.Normal))
                    Spacer(modifier = GlanceModifier.defaultWeight())
                    Text(text = widgetData.progressLabel ?: "", style = TextStyle(color = ColorProvider(day = Color(0xFF087C8C), night = Color(0xFF74D6DE)), fontSize = 11.sp, fontWeight = FontWeight.Bold))
                }
            }
    }

  }
}

data class StudyPlanWidgetDefinitionData(
    val nextTitle: String? = null,
    val nextDateLabel: String? = null,
    val progressLabel: String? = null,
) {
    companion object {
        private const val PREFERENCES_PREFIX = "home_widget.StudyPlanWidgetDefinition"

        fun fromPreferences(prefs: android.content.SharedPreferences): StudyPlanWidgetDefinitionData {
            return StudyPlanWidgetDefinitionData(
                nextTitle = prefs.getString("${PREFERENCES_PREFIX}.nextTitle", "設定你的交換目標"),
                nextDateLabel = prefs.getString("${PREFERENCES_PREFIX}.nextDateLabel", "開啟 App 開始規劃"),
                progressLabel = prefs.getString("${PREFERENCES_PREFIX}.progressLabel", "準備進度 0%"),
            )
        }
    }
}
