package tw.edu.cgu.exchangeguide.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import tw.edu.cgu.exchangeguide.data.model.PartnerUniversity
import tw.edu.cgu.exchangeguide.data.model.StudentDashboard
import tw.edu.cgu.exchangeguide.ui.AppearanceMode
import tw.edu.cgu.exchangeguide.ui.components.BannerKind
import tw.edu.cgu.exchangeguide.ui.components.ErrorState
import tw.edu.cgu.exchangeguide.ui.components.ExchangeCard
import tw.edu.cgu.exchangeguide.ui.components.InlineBanner
import tw.edu.cgu.exchangeguide.ui.components.LoadingState
import tw.edu.cgu.exchangeguide.ui.components.PageScaffold
import tw.edu.cgu.exchangeguide.ui.components.ResponsiveContent
import tw.edu.cgu.exchangeguide.ui.components.SectionHeader
import tw.edu.cgu.exchangeguide.ui.components.UniversityRow
import tw.edu.cgu.exchangeguide.ui.theme.ExchangeSpacing

@Composable
fun EligibilityScreen(
    dashboard: StudentDashboard?,
    isLoading: Boolean,
    errorMessage: String?,
    appearanceMode: AppearanceMode,
    onRefresh: () -> Unit,
    onAppearanceModeChanged: (AppearanceMode) -> Unit,
    onUniversitySelected: (PartnerUniversity) -> Unit,
    modifier: Modifier = Modifier,
) {
    var college by remember { mutableStateOf("") }
    var degree by remember { mutableStateOf("大學部") }
    var academicScore by remember { mutableStateOf("") }
    var languageTest by remember { mutableStateOf(LanguageTest.TOEIC) }
    var languageScore by remember { mutableStateOf("") }
    var assessment by remember { mutableStateOf<EligibilityAssessment?>(null) }

    PageScaffold(title = "資格檢查", modifier = modifier, onRefresh = onRefresh) { innerPadding ->
        when {
            dashboard != null -> {
                val colleges = dashboard.partnerUniversities
                    .flatMap { splitValues(it.colleges) }
                    .filterNot { it.contains("全校") || it.contains("不限") }
                    .distinct()
                    .sorted()
                val matching = if (college.isBlank()) emptyList() else dashboard.partnerUniversities.filter { university ->
                    val collegeMatches = university.colleges?.contains(college, ignoreCase = true) == true ||
                        university.colleges?.contains("全校") == true || university.colleges?.contains("不限") == true
                    val degreeMatches = university.degreeLevels?.contains(degree, ignoreCase = true) == true ||
                        university.degreeLevels?.contains("不限") == true
                    collegeMatches && degreeMatches
                }
                val valid = college.isNotBlank() && academicScore.toDoubleOrNull() != null && languageScore.toDoubleOrNull() != null

                Column(
                    Modifier
                        .fillMaxSize()
                        .padding(innerPadding)
                        .verticalScroll(rememberScrollState()),
                ) {
                    ResponsiveContent(Modifier.padding(top = ExchangeSpacing.md, bottom = ExchangeSpacing.section)) {
                        SectionHeader(
                            eyebrow = "初步資格比對",
                            title = "輸入條件，先排除明顯不符合的學校",
                            detail = "結果只用於規劃；正式資格仍由長庚大學與合作校依當期文件認定。",
                        )
                        InlineBanner(
                            "這不是錄取保證",
                            "不同學校可能另看 GPA、年級、語言單科成績與系所名額。",
                            BannerKind.Warning,
                        )
                        ExchangeCard {
                            DropdownField("所屬學院", college.ifBlank { "請選擇" }, colleges) { college = it }
                            Text("學制", style = MaterialTheme.typography.titleSmall)
                            val degrees = listOf("大學部", "研究所")
                            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                                degrees.forEachIndexed { index, item ->
                                    SegmentedButton(
                                        selected = degree == item,
                                        onClick = { degree = item },
                                        shape = SegmentedButtonDefaults.itemShape(index, degrees.size),
                                        label = { Text(item) },
                                    )
                                }
                            }
                            ScoreField("學業平均成績", "例如 82", academicScore) { academicScore = it }
                            DropdownField("語言檢定", languageTest.label, LanguageTest.entries.map { it.label }) { label ->
                                languageTest = LanguageTest.entries.first { it.label == label }
                            }
                            Text(
                                "基本比對門檻：${languageTest.minimum.formatScore()}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                            ScoreField("語言分數", languageTest.scoreHint, languageScore) { languageScore = it }
                        }
                        Button(
                            enabled = valid,
                            onClick = {
                                assessment = EligibilityAssessment(
                                    academicScore.toDouble(), languageTest, languageScore.toDouble(), matching.size,
                                )
                            },
                            modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
                        ) {
                            Icon(Icons.Default.CheckCircle, contentDescription = null)
                            Text("檢查我的資格", Modifier.padding(start = ExchangeSpacing.xs))
                        }
                        assessment?.let { result ->
                            ResultCard(result, matching, onUniversitySelected)
                        }
                        AppearanceSettings(appearanceMode, onAppearanceModeChanged)
                    }
                }
            }
            isLoading -> LoadingState("正在準備資格比對資料", Modifier.padding(innerPadding))
            else -> ErrorState(errorMessage ?: "目前無法進行資格比對", onRefresh, Modifier.padding(innerPadding))
        }
    }
}

@Composable
private fun DropdownField(label: String, value: String, options: List<String>, onSelected: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Column(verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs)) {
        Text(label, style = MaterialTheme.typography.titleSmall)
        androidx.compose.material3.OutlinedCard(
            modifier = Modifier.fillMaxWidth().heightIn(min = ExchangeSpacing.minimumTarget).clickable { expanded = true },
        ) {
            Row(
                Modifier.fillMaxWidth().padding(horizontal = ExchangeSpacing.md, vertical = ExchangeSpacing.sm),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(value, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.weight(1f))
                Icon(Icons.Default.ExpandMore, contentDescription = "展開 $label")
            }
            DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                options.forEach { option ->
                    DropdownMenuItem(
                        text = { Text(option) },
                        onClick = { onSelected(option); expanded = false },
                    )
                }
            }
        }
    }
}

@Composable
private fun ScoreField(label: String, placeholder: String, value: String, onValueChange: (String) -> Unit) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        placeholder = { Text(placeholder) },
        singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
        modifier = Modifier.fillMaxWidth().heightIn(min = ExchangeSpacing.minimumTarget),
    )
}

@Composable
private fun ResultCard(
    result: EligibilityAssessment,
    matching: List<PartnerUniversity>,
    onUniversitySelected: (PartnerUniversity) -> Unit,
) {
    ExchangeCard {
        SectionHeader(
            eyebrow = if (result.isReady) "初步通過" else "需要補強",
            title = result.title,
            detail = result.summary,
        )
        ResultRow("學業平均", result.academicPass, "70")
        ResultRow(result.languageTest.label, result.languagePass, result.languageTest.minimum.formatScore())
        if (result.isReady && matching.isNotEmpty()) {
            Text("可能符合的學校", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            matching.take(8).forEach { university ->
                UniversityRow(university) { onUniversitySelected(university) }
            }
        }
    }
}

@Composable
private fun ResultRow(label: String, pass: Boolean, minimum: String) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
        Icon(
            if (pass) Icons.Default.CheckCircle else Icons.Default.Warning,
            contentDescription = null,
            tint = if (pass) Color(0xFF258456) else MaterialTheme.colorScheme.error,
        )
        Text(label, style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1f))
        Text(if (pass) "達到 $minimum" else "未達 $minimum", style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun AppearanceSettings(mode: AppearanceMode, onChanged: (AppearanceMode) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
        SectionHeader(title = "外觀", detail = "可跟隨系統，或固定使用淺色／深色模式。")
        SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
            AppearanceMode.entries.forEachIndexed { index, item ->
                SegmentedButton(
                    selected = mode == item,
                    onClick = { onChanged(item) },
                    shape = SegmentedButtonDefaults.itemShape(index, AppearanceMode.entries.size),
                    label = { Text(item.label) },
                )
            }
        }
    }
}

private fun splitValues(value: String?): List<String> = value.orEmpty()
    .split(Regex("[、,，;/；\\n]+"))
    .map { it.trim() }
    .filter { it.isNotBlank() }

private fun Double.formatScore(): String = if (this % 1.0 == 0.0) toInt().toString() else toString()
