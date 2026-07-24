package tw.edu.cgu.exchangeguide.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import tw.edu.cgu.exchangeguide.data.model.PartnerUniversity
import tw.edu.cgu.exchangeguide.data.model.StudentDashboard
import tw.edu.cgu.exchangeguide.data.model.StudentInfoItem
import tw.edu.cgu.exchangeguide.ui.components.BannerKind
import tw.edu.cgu.exchangeguide.ui.components.ErrorState
import tw.edu.cgu.exchangeguide.ui.components.ExchangeCard
import tw.edu.cgu.exchangeguide.ui.components.InlineBanner
import tw.edu.cgu.exchangeguide.ui.components.LoadingState
import tw.edu.cgu.exchangeguide.ui.components.PageScaffold
import tw.edu.cgu.exchangeguide.ui.components.ResponsiveContent
import tw.edu.cgu.exchangeguide.ui.components.SearchField
import tw.edu.cgu.exchangeguide.ui.components.SectionHeader
import tw.edu.cgu.exchangeguide.ui.components.SourceLink
import tw.edu.cgu.exchangeguide.ui.components.UniversityRow
import tw.edu.cgu.exchangeguide.ui.theme.ExchangeSpacing

@Composable
fun DeadlinesScreen(
    dashboard: StudentDashboard?,
    isLoading: Boolean,
    errorMessage: String?,
    onRefresh: () -> Unit,
    onUniversitySelected: (PartnerUniversity) -> Unit,
    modifier: Modifier = Modifier,
) {
    var query by remember { mutableStateOf("") }
    PageScaffold(title = "截止日期", modifier = modifier, onRefresh = onRefresh) { innerPadding ->
        when {
            dashboard != null -> {
                val partnerDeadlines = dashboard.partnerUniversities.filter { university ->
                    !university.applicationDeadline.isNullOrBlank() && (
                        query.isBlank() || listOfNotNull(
                            university.schoolName,
                            university.country,
                            university.applicationDeadline,
                        ).joinToString(" ").contains(query.trim(), ignoreCase = true)
                    )
                }
                Column(
                    Modifier
                        .fillMaxSize()
                        .padding(innerPadding)
                        .verticalScroll(rememberScrollState()),
                ) {
                    ResponsiveContent(Modifier.padding(top = ExchangeSpacing.md, bottom = ExchangeSpacing.section)) { wide ->
                        SectionHeader(
                            eyebrow = "時間優先",
                            title = "先確認校內送件，再看合作校期限",
                            detail = "日期可能跨越不同時區，送件前請再次開啟官方來源確認。",
                        )
                        InlineBanner(
                            "不要只看最後一天",
                            "文件、推薦信與校內審查都需要時間，建議至少提前兩週完成初稿。",
                            BannerKind.Warning,
                        )
                        if (dashboard.applicationPeriods.isNotEmpty()) {
                            SectionHeader(title = "長庚大學近期公告", detail = "由公告內容擷取的重要申請時間。")
                            if (wide) {
                                dashboard.applicationPeriods.chunked(2).forEach { row ->
                                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.md)) {
                                        row.forEach { period -> DeadlineCard(period, Modifier.weight(1f)) }
                                        if (row.size == 1) androidx.compose.foundation.layout.Spacer(Modifier.weight(1f))
                                    }
                                }
                            } else {
                                dashboard.applicationPeriods.forEach { DeadlineCard(it) }
                            }
                        }
                        SectionHeader(title = "合作學校截止資訊", detail = "搜尋學校或國家，直接查看其申請期限。")
                        SearchField(query, { query = it }, "搜尋學校、國家或日期")
                        Text("${partnerDeadlines.size} 間有截止資訊", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        if (partnerDeadlines.isEmpty()) {
                            InlineBanner("沒有符合的期限", "改用學校或國家名稱搜尋，或先清除關鍵字。", BannerKind.Info)
                        } else {
                            partnerDeadlines.forEach { university ->
                                UniversityRow(university) { onUniversitySelected(university) }
                            }
                        }
                    }
                }
            }
            isLoading -> LoadingState("正在整理截止日期", Modifier.padding(innerPadding))
            else -> ErrorState(errorMessage ?: "目前無法取得截止日期", onRefresh, Modifier.padding(innerPadding))
        }
    }
}

@Composable
private fun DeadlineCard(period: StudentInfoItem, modifier: Modifier = Modifier) {
    ExchangeCard(modifier) {
        Row(horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm), verticalAlignment = Alignment.Top) {
            Icon(Icons.Default.CalendarMonth, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs)) {
                Text(period.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                period.details.take(3).forEach { detail ->
                    Text(detail, style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                period.source?.let { SourceLink("查看官方公告", it.sourceUrl) }
            }
        }
    }
}
