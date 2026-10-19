package tw.edu.cgu.exchangeguide.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.automirrored.filled.FactCheck
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.PieChart
import androidx.compose.material.icons.filled.School
import androidx.compose.material.icons.filled.VolunteerActivism
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import tw.edu.cgu.exchangeguide.R
import tw.edu.cgu.exchangeguide.data.model.PartnerUniversity
import tw.edu.cgu.exchangeguide.data.model.StudentDashboard
import tw.edu.cgu.exchangeguide.ui.ExchangeDestination
import tw.edu.cgu.exchangeguide.ui.components.ErrorState
import tw.edu.cgu.exchangeguide.ui.components.LoadingState
import tw.edu.cgu.exchangeguide.ui.components.PageScaffold
import tw.edu.cgu.exchangeguide.ui.components.ResponsiveContent
import tw.edu.cgu.exchangeguide.ui.components.SectionHeader
import tw.edu.cgu.exchangeguide.ui.components.TaskButton
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
    onUniversitySelected: (PartnerUniversity) -> Unit,
    modifier: Modifier = Modifier,
) {
    PageScaffold(title = "交換指南", modifier = modifier, onRefresh = onRefresh) { innerPadding ->
        when {
            dashboard != null -> {
                Column(
                    Modifier
                        .fillMaxSize()
                        .padding(innerPadding)
                        .verticalScroll(rememberScrollState()),
                ) {
                    ResponsiveContent(Modifier.padding(top = ExchangeSpacing.sm, bottom = ExchangeSpacing.section)) { wide ->
                        CampusIdentity(dashboard, wide)
                        QuickActions(wide, onTaskSelected)
                        FocusPanel(dashboard, wide, onUniversitySelected)
                        CoveragePanel(dashboard)
                    }
                }
            }
            isLoading -> LoadingState("正在整理交換資訊", Modifier.padding(innerPadding))
            else -> ErrorState(errorMessage ?: "目前沒有可顯示的資料", onRefresh, Modifier.padding(innerPadding))
        }
    }
}

@Composable
private fun CampusIdentity(dashboard: StudentDashboard, wide: Boolean) {
    val height = if (wide) 190.dp else 150.dp
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(height)
            .clip(RoundedCornerShape(28.dp))
            .semantics { contentDescription = "${dashboard.schoolName}交換資訊" },
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
                        listOf(Color.Transparent, Color.Black.copy(alpha = 0.68f)),
                        startY = 40f,
                    ),
                ),
        )
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(ExchangeSpacing.md),
            verticalAlignment = Alignment.Bottom,
            horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm),
        ) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(dashboard.schoolName, style = MaterialTheme.typography.headlineMedium, color = Color.White)
                Text("交換探索", style = MaterialTheme.typography.bodyMedium, color = Color.White.copy(alpha = 0.82f))
            }
            Surface(shape = CircleShape, color = Color.White.copy(alpha = 0.20f)) {
                Text(
                    text = "${dashboard.partnerUniversities.size}",
                    modifier = Modifier.padding(horizontal = 13.dp, vertical = 8.dp),
                    style = MaterialTheme.typography.titleMedium,
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}

@Composable
private fun QuickActions(
    wide: Boolean,
    onTaskSelected: (ExchangeDestination) -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
        SectionHeader(title = "開始", detail = "選一個圖示，詳細內容會在下一頁展開")
        if (wide) {
            Row(horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
                SchoolAction(onTaskSelected, Modifier.weight(1f))
                DeadlineAction(onTaskSelected, Modifier.weight(1f))
                SupportAction(onTaskSelected, Modifier.weight(1f))
                EligibilityAction(onTaskSelected, Modifier.weight(1f))
            }
        } else {
            Row(horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
                SchoolAction(onTaskSelected, Modifier.weight(1f))
                DeadlineAction(onTaskSelected, Modifier.weight(1f))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
                SupportAction(onTaskSelected, Modifier.weight(1f))
                EligibilityAction(onTaskSelected, Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun SchoolAction(onTaskSelected: (ExchangeDestination) -> Unit, modifier: Modifier) {
    TaskButton("找學校", "依國家、學院與學制篩選", Icons.Default.School, MaterialTheme.colorScheme.primary, modifier) {
        onTaskSelected(ExchangeDestination.Schools)
    }
}

@Composable
private fun DeadlineAction(onTaskSelected: (ExchangeDestination) -> Unit, modifier: Modifier) {
    TaskButton("截止日", "比較校內與合作校時程", Icons.Default.CalendarMonth, Color(0xFFC98A3D), modifier) {
        onTaskSelected(ExchangeDestination.Deadlines)
    }
}

@Composable
private fun SupportAction(onTaskSelected: (ExchangeDestination) -> Unit, modifier: Modifier) {
    TaskButton("補助文件", "閱讀摘要與官方規章", Icons.Default.VolunteerActivism, MaterialTheme.colorScheme.tertiary, modifier) {
        onTaskSelected(ExchangeDestination.Support)
    }
}

@Composable
private fun EligibilityAction(onTaskSelected: (ExchangeDestination) -> Unit, modifier: Modifier) {
    TaskButton("我的資格", "確認成績、語言與可看學校", Icons.AutoMirrored.Filled.FactCheck, MaterialTheme.colorScheme.secondary, modifier) {
        onTaskSelected(ExchangeDestination.Eligibility)
    }
}

@Composable
private fun FocusPanel(
    dashboard: StudentDashboard,
    wide: Boolean,
    onUniversitySelected: (PartnerUniversity) -> Unit,
) {
    val deadline: @Composable () -> Unit = {
        dashboard.applicationPeriods.firstOrNull()?.let { period ->
            ExpandableFocusCard(
                title = "最近截止",
                summary = period.title,
                detail = period.details.firstOrNull() ?: "請開啟官方來源確認日期",
                icon = Icons.Default.CalendarMonth,
                tint = Color(0xFFC98A3D),
            )
        }
    }
    val university: @Composable () -> Unit = {
        dashboard.partnerUniversities.firstOrNull()?.let { school ->
            LinkedFocusCard(
                title = "推薦學校",
                summary = school.schoolName,
                icon = Icons.Default.School,
                tint = MaterialTheme.colorScheme.primary,
            ) { onUniversitySelected(school) }
        }
    }

    Column(verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
        SectionHeader(title = "焦點")
        if (wide) {
            Row(horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
                Box(Modifier.weight(1f)) { deadline() }
                Box(Modifier.weight(1f)) { university() }
            }
        } else {
            deadline()
            university()
        }
    }
}

@Composable
private fun ExpandableFocusCard(
    title: String,
    summary: String,
    detail: String,
    icon: ImageVector,
    tint: Color,
) {
    var expanded by rememberSaveable(title) { mutableStateOf(false) }
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 3.dp,
    ) {
        Column {
            FocusCardHeader(title, summary, icon, tint, expanded = expanded) { expanded = !expanded }
            AnimatedVisibility(visible = expanded) {
                Text(
                    text = detail,
                    modifier = Modifier.padding(start = 68.dp, end = ExchangeSpacing.md, bottom = ExchangeSpacing.md),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun LinkedFocusCard(
    title: String,
    summary: String,
    icon: ImageVector,
    tint: Color,
    onClick: () -> Unit,
) {
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 3.dp,
    ) {
        FocusCardHeader(title, summary, icon, tint, onClick = onClick)
    }
}

@Composable
private fun FocusCardHeader(
    title: String,
    summary: String,
    icon: ImageVector,
    tint: Color,
    expanded: Boolean? = null,
    onClick: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(role = Role.Button, onClick = onClick)
            .padding(ExchangeSpacing.md),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm),
    ) {
        Surface(shape = CircleShape, color = tint.copy(alpha = 0.13f)) {
            Box(Modifier.size(40.dp), contentAlignment = Alignment.Center) {
                Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.size(22.dp))
            }
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(title, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(summary, style = MaterialTheme.typography.titleSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        Icon(
            imageVector = when (expanded) {
                true -> Icons.Default.ExpandLess
                false -> Icons.Default.ExpandMore
                null -> Icons.AutoMirrored.Filled.ArrowForward
            },
            contentDescription = when (expanded) {
                true -> "收合"
                false -> "展開"
                null -> "查看"
            },
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

private data class CoverageItem(val label: String, val value: Int, val color: Color)

@Composable
private fun CoveragePanel(dashboard: StudentDashboard) {
    val items = listOf(
        CoverageItem("學校", dashboard.partnerUniversities.size, ChartBlue),
        CoverageItem("時程", dashboard.applicationPeriods.size, ChartPeach),
        CoverageItem("文件", dashboard.documentExplanations.size, ChartLavender),
        CoverageItem("來源", dashboard.sources.size, ChartMint),
    )
    val total = items.sumOf { it.value }
    var expanded by rememberSaveable { mutableStateOf(false) }

    Surface(
        shape = RoundedCornerShape(24.dp),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 3.dp,
    ) {
        Column {
            FocusCardHeader(
                title = "資料狀態",
                summary = "$total 筆重點",
                icon = Icons.Default.PieChart,
                tint = MaterialTheme.colorScheme.secondary,
                expanded = expanded,
            ) { expanded = !expanded }
            AnimatedVisibility(visible = expanded) {
                CoverageChart(items, total)
            }
        }
    }
}

@Composable
private fun CoverageChart(items: List<CoverageItem>, total: Int) {
    val chartDescription = "資料整理進度：" + items.joinToString("，") { "${it.label} ${it.value} 筆" }
    Row(
        Modifier
            .fillMaxWidth()
            .padding(start = ExchangeSpacing.md, end = ExchangeSpacing.md, bottom = ExchangeSpacing.md)
            .semantics { contentDescription = chartDescription },
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.lg),
    ) {
        Box(Modifier.size(126.dp), contentAlignment = Alignment.Center) {
            Canvas(Modifier.fillMaxSize()) {
                val stroke = 18.dp.toPx()
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
            Text(total.toString(), style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
            items.forEach { item ->
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs)) {
                    Box(Modifier.size(9.dp).clip(CircleShape).background(item.color))
                    Text(item.label, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                    Text(item.value.toString(), style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}
