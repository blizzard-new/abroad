package tw.edu.cgu.exchange_guide_flutter

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
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
import androidx.glance.layout.*
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import androidx.glance.unit.ColorProvider
import es.antonborri.home_widget.HomeWidgetGlanceState
import es.antonborri.home_widget.HomeWidgetGlanceStateDefinition
import es.antonborri.home_widget.HomeWidgetGlanceWidgetReceiver
import java.time.LocalDate
import java.time.temporal.ChronoUnit

enum class PlanStyle(val title: String, val accent: Long, val background: Int) {
    OVERVIEW("交換總覽", 0xFF9AC9FF, R.drawable.widget_orbit_background),
    COUNTDOWN("星軌倒數", 0xFFD1B7FF, R.drawable.widget_cosmic_background),
    CHECKLIST("極光待辦", 0xFF8BE8CE, R.drawable.widget_aurora_background),
    PROGRESS("軌道進度", 0xFF9AC9FF, R.drawable.widget_orbit_background)
}

/** All styles read the same account-scoped cache, cleared by logout. */
open class PlanGlanceWidget(private val style: PlanStyle) : GlanceAppWidget() {
    override val stateDefinition = HomeWidgetGlanceStateDefinition()
    override val sizeMode = SizeMode.Responsive(setOf(DpSize(140.dp, 140.dp), DpSize(280.dp, 140.dp)))
    override suspend fun provideGlance(context: Context, id: GlanceId) {
        provideContent { Content(context, currentState()) }
    }
    @Composable
    private fun Content(context: Context, state: HomeWidgetGlanceState) {
        val prefs = state.preferences
        val prefix = "home_widget.StudyPlanWidgetDefinition"
        val title = prefs.getString("$prefix.nextTitle", "登入後開始交換計畫") ?: ""
        val date = prefs.getString("$prefix.nextDateLabel", "點一下開啟 UniWay") ?: ""
        val progress = prefs.getString("$prefix.progressLabel", "尚未登入") ?: ""
        val updated = prefs.getString("$prefix.updatedLabel", "") ?: ""
        val percent = Regex("(\\d+)%").find(progress)?.groupValues?.get(1)?.toIntOrNull()?.coerceIn(0, 100) ?: 0
        val tasks = (prefs.getString("$prefix.tasks", "") ?: "").split("\n").filter { it.isNotBlank() }
        val days = runCatching { ChronoUnit.DAYS.between(LocalDate.now(), LocalDate.parse(prefs.getString("$prefix.deadlineIso", ""))) }.getOrNull()
        val wide = LocalSize.current.width >= 280.dp
        val ink = ColorProvider(Color(0xFFF1F4FF))
        val secondary = ColorProvider(Color(0xFFB7C3DB))
        val accent = ColorProvider(Color(style.accent))
        val open = Intent(context, MainActivity::class.java).apply {
            action = Intent.ACTION_VIEW
            data = Uri.parse("tw.uniway.app://journey")
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        Column(modifier = GlanceModifier.fillMaxSize().background(ImageProvider(style.background))
            .padding(16.dp).clickable(actionStartActivity(open))) {
            Text("✦ ${style.title}", maxLines = 1, style = TextStyle(color = accent, fontSize = 12.sp, fontWeight = FontWeight.Bold))
            Spacer(GlanceModifier.height(8.dp))
            Column(modifier = GlanceModifier.defaultWeight()) {
                when {
                    style == PlanStyle.COUNTDOWN && days != null -> {
                        Text(if (days < 0) "期限已過" else if (days == 0L) "今天" else "$days 天後",
                            maxLines = 1, style = TextStyle(color = ink, fontSize = 28.sp, fontWeight = FontWeight.Bold))
                        Text(title, maxLines = if (wide) 1 else 2, style = TextStyle(color = secondary, fontSize = 12.sp))
                    }
                    style == PlanStyle.CHECKLIST && tasks.isNotEmpty() -> {
                        tasks.take(if (wide) 3 else 2).forEach { task ->
                            Text("○ $task", maxLines = 1, style = TextStyle(color = ink, fontSize = 13.sp))
                            Spacer(GlanceModifier.height(5.dp))
                        }
                    }
                    style == PlanStyle.PROGRESS -> {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Image(provider = ImageProvider(progressRing(percent, style.accent.toInt())), contentDescription = "準備進度 $percent%", modifier = GlanceModifier.size(64.dp))
                            if (wide) {
                                Spacer(GlanceModifier.width(16.dp))
                                Text(title, maxLines = 3, style = TextStyle(color = ink, fontSize = 14.sp))
                            }
                        }
                    }
                    else -> {
                        Text(title, maxLines = 2, style = TextStyle(color = ink, fontSize = 16.sp, fontWeight = FontWeight.Bold))
                        Spacer(GlanceModifier.height(5.dp))
                        Text(date, maxLines = 2, style = TextStyle(color = secondary, fontSize = 11.sp))
                    }
                }
            }
            Text(if (updated.isBlank()) progress else updated, maxLines = 1, style = TextStyle(color = accent, fontSize = 10.sp))
        }
    }
    private fun progressRing(percent: Int, accent: Int): Bitmap {
        val bitmap = Bitmap.createBitmap(192, 192, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE; strokeWidth = 14f; color = 0x334C709F; strokeCap = Paint.Cap.ROUND }
        canvas.drawCircle(96f, 96f, 82f, paint)
        paint.color = accent
        canvas.drawArc(14f, 14f, 178f, 178f, -90f, percent * 3.6f, false, paint)
        paint.style = Paint.Style.FILL; paint.textSize = 40f; paint.textAlign = Paint.Align.CENTER; paint.color = 0xFFF1F4FF.toInt()
        canvas.drawText("$percent%", 96f, 96f - (paint.ascent() + paint.descent()) / 2, paint)
        return bitmap
    }
}

class StudyPlanWidgetDefinitionHomeWidget : PlanGlanceWidget(PlanStyle.OVERVIEW)
class CountdownGlanceWidget : PlanGlanceWidget(PlanStyle.COUNTDOWN)
class ChecklistGlanceWidget : PlanGlanceWidget(PlanStyle.CHECKLIST)
class ProgressGlanceWidget : PlanGlanceWidget(PlanStyle.PROGRESS)
class CountdownWidgetReceiver : HomeWidgetGlanceWidgetReceiver<CountdownGlanceWidget>() { override val glanceAppWidget = CountdownGlanceWidget() }
class ChecklistWidgetReceiver : HomeWidgetGlanceWidgetReceiver<ChecklistGlanceWidget>() { override val glanceAppWidget = ChecklistGlanceWidget() }
class ProgressWidgetReceiver : HomeWidgetGlanceWidgetReceiver<ProgressGlanceWidget>() { override val glanceAppWidget = ProgressGlanceWidget() }
