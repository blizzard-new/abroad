package tw.edu.cgu.exchangeguide.ui.screens

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import tw.edu.cgu.exchangeguide.data.model.PartnerUniversity
import tw.edu.cgu.exchangeguide.data.model.StudentDashboard
import tw.edu.cgu.exchangeguide.ui.components.ErrorState
import tw.edu.cgu.exchangeguide.ui.components.InlineBanner
import tw.edu.cgu.exchangeguide.ui.components.BannerKind
import tw.edu.cgu.exchangeguide.ui.components.LoadingState
import tw.edu.cgu.exchangeguide.ui.components.PageScaffold
import tw.edu.cgu.exchangeguide.ui.components.ResponsiveContent
import tw.edu.cgu.exchangeguide.ui.components.SearchField
import tw.edu.cgu.exchangeguide.ui.components.SectionHeader
import tw.edu.cgu.exchangeguide.ui.components.UniversityRow
import tw.edu.cgu.exchangeguide.ui.theme.ExchangeSpacing

@Composable
fun SchoolsScreen(
    dashboard: StudentDashboard?,
    isLoading: Boolean,
    errorMessage: String?,
    onRefresh: () -> Unit,
    onUniversitySelected: (PartnerUniversity) -> Unit,
    modifier: Modifier = Modifier,
) {
    var query by remember { mutableStateOf("") }
    var selectedCountry by remember { mutableStateOf("全部") }
    var selectedProgram by remember { mutableStateOf("全部") }

    PageScaffold(title = "找學校", modifier = modifier, onRefresh = onRefresh) { innerPadding ->
        when {
            dashboard != null -> {
                val countries = listOf("全部") + dashboard.partnerUniversities.mapNotNull { it.country?.trim() }.filter { it.isNotBlank() }.distinct().sorted()
                val programs = listOf("全部") + dashboard.partnerUniversities.mapNotNull { it.programType?.trim() }.filter { it.isNotBlank() }.distinct().sorted()
                val normalized = query.trim()
                val visible = dashboard.partnerUniversities.filter { university ->
                    val haystack = listOfNotNull(
                        university.schoolName,
                        university.country,
                        university.colleges,
                        university.degreeLevels,
                        university.programType,
                    ).joinToString(" ")
                    (normalized.isBlank() || haystack.contains(normalized, ignoreCase = true)) &&
                        (selectedCountry == "全部" || university.country == selectedCountry) &&
                        (selectedProgram == "全部" || university.programType == selectedProgram)
                }

                Column(
                    Modifier
                        .fillMaxSize()
                        .padding(innerPadding)
                        .verticalScroll(rememberScrollState()),
                ) {
                    ResponsiveContent(Modifier.padding(top = ExchangeSpacing.md, bottom = ExchangeSpacing.section)) { wide ->
                        SectionHeader(
                            eyebrow = "合作學校",
                            title = "依國家、方案與條件縮小範圍",
                            detail = "點進學校後可查看限制、申請步驟，以及其他學生的文章與影片心得。",
                        )
                        SearchField(query, { query = it }, "搜尋學校、國家、學院或學位")
                        FilterStrip("國家", countries, selectedCountry) { selectedCountry = it }
                        FilterStrip("方案", programs, selectedProgram) { selectedProgram = it }
                        InlineBanner(
                            title = "資格仍以當期公告為準",
                            message = "系統先整理可比較的重點；名額、語言門檻與截止日可能由合作校更新。",
                            kind = BannerKind.Info,
                        )
                        Text("找到 ${visible.size} 間學校", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        if (visible.isEmpty()) {
                            InlineBanner("沒有符合的學校", "請減少篩選條件，或改用其他關鍵字。", BannerKind.Warning)
                        } else if (wide) {
                            visible.chunked(2).forEach { row ->
                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.md)) {
                                    row.forEach { university ->
                                        UniversityRow(university, Modifier.weight(1f)) { onUniversitySelected(university) }
                                    }
                                    if (row.size == 1) androidx.compose.foundation.layout.Spacer(Modifier.weight(1f))
                                }
                            }
                        } else {
                            visible.forEach { university ->
                                UniversityRow(university) { onUniversitySelected(university) }
                            }
                        }
                    }
                }
            }
            isLoading -> LoadingState("正在載入合作學校", Modifier.padding(innerPadding))
            else -> ErrorState(errorMessage ?: "目前無法取得合作學校", onRefresh, Modifier.padding(innerPadding))
        }
    }
}

@Composable
private fun FilterStrip(label: String, options: List<String>, selected: String, onSelected: (String) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs)) {
        Text(label, style = MaterialTheme.typography.titleSmall)
        Row(
            Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs),
        ) {
            options.forEach { option ->
                FilterChip(
                    selected = option == selected,
                    onClick = { onSelected(option) },
                    label = { Text(option) },
                )
            }
        }
    }
}
