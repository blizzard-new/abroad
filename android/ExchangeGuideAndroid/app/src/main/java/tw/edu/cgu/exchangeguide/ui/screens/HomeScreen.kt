package tw.edu.cgu.exchangeguide.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.FactCheck
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.School
import androidx.compose.material.icons.filled.VolunteerActivism
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import tw.edu.cgu.exchangeguide.R
import tw.edu.cgu.exchangeguide.data.model.StudentDashboard
import tw.edu.cgu.exchangeguide.ui.ExchangeDestination
import tw.edu.cgu.exchangeguide.ui.components.ErrorState
import tw.edu.cgu.exchangeguide.ui.components.ExchangeCard
import tw.edu.cgu.exchangeguide.ui.components.LoadingState
import tw.edu.cgu.exchangeguide.ui.components.PageScaffold
import tw.edu.cgu.exchangeguide.ui.components.ResponsiveContent
import tw.edu.cgu.exchangeguide.ui.components.SectionHeader
import tw.edu.cgu.exchangeguide.ui.components.TaskButton
import tw.edu.cgu.exchangeguide.ui.components.UniversityRow
import tw.edu.cgu.exchangeguide.ui.theme.ChartBlue
import tw.edu.cgu.exchangeguide.ui.theme.ChartLavender
import tw.edu.cgu.exchangeguide.ui.theme.ChartMint
import tw.edu.cgu.exchangeguide.ui.theme.ChartPeach
import tw.edu.cgu.exchangeguide.ui.theme.ExchangeSpacing

@Composable
fun HomeScreen(
    dashboard: StudentDashboard?,
    isLoading: Boolean,
    errorMessage: String?,
    onRefresh: () -> Unit,
    onTaskSelected: (ExchangeDestination) -> Unit,
    onUniversitySelected: (tw.edu.cgu.exchangeguide.data.model.PartnerUniversity) -> Unit,
    modifier: Modifier = Modifier,
) {
    PageScaffold(title = "交換留學資訊", modifier = modifier, onRefresh = onRefresh) { innerPadding ->
        when {
            dashboard != null -> {
                Column(
                    Modifier
                        .fillMaxSize()
                        .padding(innerPadding)
                        .verticalScroll(rememberScrollState()),
                ) {
                    ResponsiveContent(Modifier.padding(top = ExchangeSpacing.md, bottom = ExchangeSpacing.section)) { wide ->
                        GreetingHeader()
                        CampusIdentity(dashboard, wide)
                        if (wide) {
                            Row(horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.md)) {
                                TaskPanel(onTaskSelected, Modifier.weight(1f))
                                CoveragePanel(dashboard, Modifier.weight(1f))
                            }
                        } else {
                            TaskPanel(onTaskSelected)
                            CoveragePanel(dashboard)
                        }
                        LatestInformation(dashboard, wide, onUniversitySelected)
                    }
                }
            }
            isLoading -> LoadingState("正在整理長庚大學交換資訊", Modifier.padding(innerPadding))
            else -> ErrorState(errorMessage ?: "目前沒有可顯示的資料", onRefresh, Modifier.padding(innerPadding))
        }
    }
}

@Composable
private fun GreetingHeader() {
    Row(
        Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.md),
    ) {
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.xxs)) {
            Text("你好，準備交換的同學", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
            Text("先完成今天最重要的一件事", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Icon(
            Icons.Default.AccountCircle,
            contentDescription = "匿名學生個人資料",
            tint = MaterialTheme.colorScheme.primary,
            modifier = Modifier.size(52.dp),
        )
    }
}

@Composable
private fun CampusIdentity(dashboard: StudentDashboard, wide: Boolean) {
    val height = if (wide) 240.dp else 190.dp
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(height)
            .clip(RoundedCornerShape(16.dp))
            .semantics { contentDescription = "長庚大學校園" },
        contentAlignment = Alignment.BottomStart,
    ) {
        Image(
            painter = painterResource(R.drawable.cgu_campus),
            contentDescription = null,
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize(),
        )
        Box(
            Modifier
                .fillMaxSize()
                .background(
                    Brush.verticalGradient(
                        listOf(Color.Transparent, Color.Black.copy(alpha = 0.55f)),
                        startY = 80f,
                    ),
                ),
        )
        Column(Modifier.padding(ExchangeSpacing.md), verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.xxs)) {
            Text(dashboard.schoolName, style = MaterialTheme.typography.headlineMedium, color = Color.White)
            Text("交換 · 研修 · 補助", style = MaterialTheme.typography.bodyMedium, color = Color.White.copy(alpha = 0.84f))
        }
    }
}

@Composable
private fun TaskPanel(onTaskSelected: (ExchangeDestination) -> Unit, modifier: Modifier = Modifier) {
    Column(modifier, verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
        SectionHeader(title = "今天想先做什麼？", modifier = Modifier.padding(bottom = ExchangeSpacing.xxs))
        TaskButton("找可申請學校", "依國家、學院與學制篩選", Icons.Default.School, MaterialTheme.colorScheme.primary) {
            onTaskSelected(ExchangeDestination.Schools)
        }
        TaskButton("掌握截止日期", "比較校內與合作校時程", Icons.Default.CalendarMonth, Color(0xFFC98A3D)) {
            onTaskSelected(ExchangeDestination.Deadlines)
        }
        TaskButton("查看補助與文件", "先讀重點，再開官方規章", Icons.Default.VolunteerActivism, MaterialTheme.colorScheme.tertiary) {
            onTaskSelected(ExchangeDestination.Support)
        }
        TaskButton("資格初步檢查", "確認成績、語言與可看學校", Icons.AutoMirrored.Filled.FactCheck, MaterialTheme.colorScheme.secondary) {
            onTaskSelected(ExchangeDestination.Eligibility)
        }
    }
}

private data class CoverageItem(val label: String, val value: Int, val color: Color)

@Composable
private fun CoveragePanel(dashboard: StudentDashboard, modifier: Modifier = Modifier) {
    val items = listOf(
        CoverageItem("學校", dashboard.partnerUniversities.size, ChartBlue),
        CoverageItem("時程", dashboard.applicationPeriods.size, ChartPeach),
        CoverageItem("文件", dashboard.documentExplanations.size, ChartLavender),
        CoverageItem("來源", dashboard.sources.size, ChartMint),
    )
    val total = items.sumOf { it.value }
    val chartDescription = "資料整理進度：" + items.joinToString("，") { "${it.label} ${it.value} 筆" }
    ExchangeCard(modifier) {
        SectionHeader(title = "整理進度")
        Row(
            Modifier
                .fillMaxWidth()
                .padding(top = ExchangeSpacing.xs)
                .semantics { contentDescription = chartDescription },
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.lg),
        ) {
            Box(Modifier.size(148.dp), contentAlignment = Alignment.Center) {
                Canvas(Modifier.fillMaxSize()) {
                    val stroke = 20.dp.toPx()
                    val gapDegrees = 8f
                    val safeTotal = total.coerceAtLeast(1)
                    var start = -90f
                    items.forEach { item ->
                        val sweep = item.value.toFloat() / safeTotal * 360f
                        if (sweep > 0f) {
                            drawArc(
                                color = item.color,
                                startAngle = start + gapDegrees / 2,
                                sweepAngle = (sweep - gapDegrees).coerceAtLeast(2f),
                                useCenter = false,
                                style = Stroke(width = stroke, cap = StrokeCap.Round),
                                topLeft = Offset(stroke / 2, stroke / 2),
                                size = Size(size.width - stroke, size.height - stroke),
                            )
                        }
                        start += sweep
                    }
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(total.toString(), style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                    Text("筆重點", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
                items.forEach { item ->
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs)) {
                        Box(Modifier.size(10.dp).clip(CircleShape).background(item.color))
                        Text(item.label, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                        Text(item.value.toString(), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}

@Composable
private fun LatestInformation(
    dashboard: StudentDashboard,
    wide: Boolean,
    onUniversitySelected: (tw.edu.cgu.exchangeguide.data.model.PartnerUniversity) -> Unit,
) {
    val deadline: @Composable () -> Unit = {
        dashboard.applicationPeriods.firstOrNull()?.let { period ->
            ExchangeCard {
                SectionHeader(title = "最近申請資訊", detail = period.title)
                period.details.firstOrNull()?.let {
                    Text(it, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }
    val university: @Composable () -> Unit = {
        dashboard.partnerUniversities.firstOrNull()?.let { school ->
            Column(verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
                SectionHeader(title = "先從這所學校開始")
                UniversityRow(school) { onUniversitySelected(school) }
            }
        }
    }
    if (wide) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.md)) {
            Box(Modifier.weight(1f)) { deadline() }
            Box(Modifier.weight(1f)) { university() }
        }
    } else {
        deadline()
        university()
    }
}
