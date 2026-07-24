package tw.edu.cgu.exchangeguide.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import tw.edu.cgu.exchangeguide.data.model.StudentDashboard
import tw.edu.cgu.exchangeguide.ui.components.BannerKind
import tw.edu.cgu.exchangeguide.ui.components.ErrorState
import tw.edu.cgu.exchangeguide.ui.components.ExpandableDocumentCard
import tw.edu.cgu.exchangeguide.ui.components.InlineBanner
import tw.edu.cgu.exchangeguide.ui.components.LoadingState
import tw.edu.cgu.exchangeguide.ui.components.PageScaffold
import tw.edu.cgu.exchangeguide.ui.components.ResponsiveContent
import tw.edu.cgu.exchangeguide.ui.components.SearchField
import tw.edu.cgu.exchangeguide.ui.components.SectionHeader
import tw.edu.cgu.exchangeguide.ui.theme.ExchangeSpacing

@Composable
fun SupportScreen(
    dashboard: StudentDashboard?,
    isLoading: Boolean,
    errorMessage: String?,
    onRefresh: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var selectedSegment by remember { mutableIntStateOf(0) }
    var query by remember { mutableStateOf("") }
    val segments = listOf("補助要點", "申請文件")
    PageScaffold(title = "補助與文件", modifier = modifier, onRefresh = onRefresh) { innerPadding ->
        when {
            dashboard != null -> {
                val scholarshipKeywords = listOf("補助", "獎學金", "學海", "領航者", "惜珠", "飛颺")
                val visible = dashboard.documentExplanations.filter { document ->
                    val haystack = "${document.title} ${document.documentType} ${document.summary}"
                    val isScholarship = scholarshipKeywords.any { haystack.contains(it, ignoreCase = true) }
                    (if (selectedSegment == 0) isScholarship else !isScholarship) &&
                        (query.isBlank() || haystack.contains(query.trim(), ignoreCase = true))
                }
                Column(
                    Modifier
                        .fillMaxSize()
                        .padding(innerPadding)
                        .verticalScroll(rememberScrollState()),
                ) {
                    ResponsiveContent(Modifier.padding(top = ExchangeSpacing.md, bottom = ExchangeSpacing.section)) {
                        SectionHeader(
                            eyebrow = "文件先替你讀過",
                            title = "先看摘要與申請重點",
                            detail = "不需要先開 PDF。展開即可看到適用對象、條件與注意事項，完整版本仍保留官方連結。",
                        )
                        SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                            segments.forEachIndexed { index, label ->
                                SegmentedButton(
                                    selected = selectedSegment == index,
                                    onClick = { selectedSegment = index },
                                    shape = SegmentedButtonDefaults.itemShape(index, segments.size),
                                    label = { Text(label) },
                                )
                            }
                        }
                        SearchField(query, { query = it }, "搜尋補助、要點或文件名稱")
                        InlineBanner(
                            title = "摘要不是法律或校務認定",
                            message = "金額、名額與資格可能隨年度調整，正式送件前務必查看當期官方文件。",
                            kind = BannerKind.Info,
                        )
                        Text("${visible.size} 份整理", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        if (visible.isEmpty()) {
                            InlineBanner("這個分類目前沒有文件", "請切換分類或更換搜尋關鍵字。", BannerKind.Warning)
                        } else {
                            visible.forEach { document -> ExpandableDocumentCard(document) }
                        }
                    }
                }
            }
            isLoading -> LoadingState("正在載入補助與文件摘要", Modifier.padding(innerPadding))
            else -> ErrorState(errorMessage ?: "目前無法取得文件摘要", onRefresh, Modifier.padding(innerPadding))
        }
    }
}
