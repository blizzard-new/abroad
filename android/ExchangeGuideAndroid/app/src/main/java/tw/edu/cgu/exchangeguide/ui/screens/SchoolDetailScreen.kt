package tw.edu.cgu.exchangeguide.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Article
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.PlayCircle
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.WarningAmber
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import tw.edu.cgu.exchangeguide.data.model.ApplicationStep
import tw.edu.cgu.exchangeguide.data.model.PartnerUniversity
import tw.edu.cgu.exchangeguide.data.model.StudentExperienceDigest
import tw.edu.cgu.exchangeguide.data.model.StudentExperienceSource
import tw.edu.cgu.exchangeguide.data.model.UniversityApplicationWorkflow
import tw.edu.cgu.exchangeguide.ui.components.BannerKind
import tw.edu.cgu.exchangeguide.ui.components.BulletGroup
import tw.edu.cgu.exchangeguide.ui.components.ErrorState
import tw.edu.cgu.exchangeguide.ui.components.ExchangeCard
import tw.edu.cgu.exchangeguide.ui.components.InlineBanner
import tw.edu.cgu.exchangeguide.ui.components.LoadingState
import tw.edu.cgu.exchangeguide.ui.components.PageScaffold
import tw.edu.cgu.exchangeguide.ui.components.ResponsiveContent
import tw.edu.cgu.exchangeguide.ui.components.SectionHeader
import tw.edu.cgu.exchangeguide.ui.components.SourceLink
import tw.edu.cgu.exchangeguide.ui.theme.ExchangeSpacing

@Composable
fun SchoolDetailScreen(
    university: PartnerUniversity,
    workflow: UniversityApplicationWorkflow?,
    experiences: StudentExperienceDigest?,
    isLoading: Boolean,
    errorMessage: String?,
    onBack: () -> Unit,
    onRefresh: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var selectedSection by remember(university.schoolName) { mutableIntStateOf(0) }
    val sections = listOf("條件", "申請流程", "生活情報", "學生心得", "學生社群")
    PageScaffold(
        title = university.schoolName,
        modifier = modifier,
        onRefresh = onRefresh,
        onBack = onBack,
    ) { innerPadding ->
        Column(
            Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(rememberScrollState()),
        ) {
            ResponsiveContent(Modifier.padding(top = ExchangeSpacing.md, bottom = ExchangeSpacing.section)) { wide ->
                SchoolIdentity(university)
                Row(
                    Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs),
                ) {
                    sections.forEachIndexed { index, label ->
                        FilterChip(
                            selected = selectedSection == index,
                            onClick = { selectedSection = index },
                            label = { Text(label) },
                        )
                    }
                }
                when (selectedSection) {
                    0 -> RequirementsSection(university, wide)
                    1 -> WorkflowSection(workflow, isLoading, errorMessage, onRefresh)
                    2 -> LifeInformationSection(experiences, isLoading, errorMessage, onRefresh)
                    3 -> ExperiencesSection(experiences, isLoading, errorMessage, onRefresh, wide)
                    else -> CommunitySection(university.schoolName)
                }
            }
        }
    }
}

@Composable
private fun LifeInformationSection(
    experiences: StudentExperienceDigest?,
    isLoading: Boolean,
    errorMessage: String?,
    onRefresh: () -> Unit,
) {
    SectionHeader(
        eyebrow = "有資料的面向優先",
        title = "生活情報重點",
        detail = "只列出文章或影片中可具體整理的內容，完整版本保留原始連結。",
    )
    when {
        experiences != null -> experiences.highlights.sortedWith(
            compareByDescending<tw.edu.cgu.exchangeguide.data.model.ExperienceHighlight> { it.sourceCount }
                .thenBy { it.title },
        ).forEach { highlight ->
            ExchangeCard {
                Text(highlight.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Text("${highlight.sourceCount} 個來源已整理", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                if (highlight.keyPoints.isEmpty()) {
                    InlineBanner("已有來源，具體內容待補充", "摘要尚未擷取到足以驗證的細節，因此不以分類句充當重點。", BannerKind.Warning)
                } else {
                    BulletGroup("學生最需要知道", highlight.keyPoints)
                }
                highlight.sourceUrls.take(4).forEachIndexed { index, url -> SourceLink("查看學生來源 ${index + 1}", url) }
            }
        }
        isLoading -> LoadingState("正在整理生活情報")
        errorMessage != null -> ErrorState(errorMessage, onRefresh)
        else -> InlineBanner("尚無生活情報", "找到可驗證的公開來源後才會列入。", BannerKind.Info)
    }
}

@Composable
private fun SchoolIdentity(university: PartnerUniversity) {
    Column(verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs)) {
        Text(
            listOfNotNull(university.country, university.programType).joinToString(" · "),
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.primary,
        )
        Text(university.schoolName, style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Bold)
        university.applicationDeadline?.takeIf { it.isNotBlank() }?.let {
            InlineBanner("申請截止資訊", it, BannerKind.Warning)
        }
    }
}

@Composable
private fun RequirementsSection(university: PartnerUniversity, wide: Boolean) {
    SectionHeader(
        eyebrow = "申請前先確認",
        title = "限制與條件",
        detail = "將合作校表格內容整理成可直接比較的欄位；空白欄位代表官方資料目前未提供。",
    )
    val items = listOfNotNull(
        university.colleges?.takeIf { it.isNotBlank() }?.let { "可申請學院" to it },
        university.degreeLevels?.takeIf { it.isNotBlank() }?.let { "學制" to it },
        university.studyPeriod?.takeIf { it.isNotBlank() }?.let { "研修期間" to it },
        university.quota?.takeIf { it.isNotBlank() }?.let { "名額" to it },
        university.eligibility?.takeIf { it.isNotBlank() }?.let { "資格與語言條件" to it },
        university.applicationInfo?.takeIf { it.isNotBlank() }?.let { "申請方式" to it },
        university.tuitionInfo?.takeIf { it.isNotBlank() }?.let { "學費資訊" to it },
        university.rankingInfo?.takeIf { it.isNotBlank() }?.let { "其他資訊" to it },
    )
    if (items.isEmpty()) {
        InlineBanner("尚無完整條件", "可先查看官方來源，系統會在下次資料更新時補齊。", BannerKind.Info)
    } else if (wide) {
        items.chunked(2).forEach { row ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.md)) {
                row.forEach { (label, value) -> InfoCard(label, value, Modifier.weight(1f)) }
                if (row.size == 1) androidx.compose.foundation.layout.Spacer(Modifier.weight(1f))
            }
        }
    } else {
        items.forEach { (label, value) -> InfoCard(label, value) }
    }
    if (!university.website.isNullOrBlank()) SourceLink("前往合作校網站", university.website)
    SourceLink("查看長庚大學官方資料", university.sourceUrl)
}

@Composable
private fun InfoCard(label: String, value: String, modifier: Modifier = Modifier) {
    ExchangeCard(modifier) {
        Text(label, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
        Text(value, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun WorkflowSection(
    workflow: UniversityApplicationWorkflow?,
    isLoading: Boolean,
    errorMessage: String?,
    onRefresh: () -> Unit,
) {
    SectionHeader(
        eyebrow = "依官方資料整理",
        title = "詳細申請流程",
        detail = "從校內推薦、對方學校申請到簽證與出發準備，依順序逐步完成。",
    )
    when {
        workflow != null -> {
            if (workflow.coverageNote.isNotBlank()) {
                InlineBanner("資料涵蓋狀態", workflow.coverageNote, BannerKind.Info)
            }
            workflow.steps.sortedBy { it.order }.forEach { step -> WorkflowStepCard(step) }
            if (workflow.disclaimer.isNotBlank()) {
                InlineBanner("送件前再次確認", workflow.disclaimer, BannerKind.Warning)
            }
            if (workflow.sources.isNotEmpty()) {
                SectionHeader(title = "流程資料來源", detail = "以下連結用於核對最新規定。")
                workflow.sources.forEach { source -> SourceLink(source.title.ifBlank { "官方申請說明" }, source.sourceUrl) }
            }
        }
        isLoading -> LoadingState("正在整理這間學校的最新申請流程")
        errorMessage != null -> ErrorState(errorMessage, onRefresh)
        else -> InlineBanner("流程尚未整理", "重新整理後，系統會嘗試從官方網站建立流程。", BannerKind.Info)
    }
}

@Composable
private fun WorkflowStepCard(step: ApplicationStep) {
    var expanded by remember(step.order) { mutableStateOf(step.order <= 2) }
    ExchangeCard {
        Row(
            Modifier
                .fillMaxWidth()
                .heightIn(min = ExchangeSpacing.minimumTarget)
                .clickable(role = Role.Button) { expanded = !expanded },
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm),
        ) {
            Text(
                step.order.toString(),
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold,
            )
            Column(Modifier.weight(1f)) {
                Text(step.phase, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                Text(step.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            }
            Icon(if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore, contentDescription = if (expanded) "收合步驟" else "展開步驟")
        }
        Text(step.summary, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.SemiBold)
        AnimatedVisibility(expanded) {
            Column(verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
                if (step.responsibleParty.isNotBlank()) DetailLabel("負責單位", step.responsibleParty)
                step.timing?.takeIf { it.isNotBlank() }?.let { DetailLabel("時間", it) }
                if (step.details.isNotEmpty()) BulletGroup("這一步要做", step.details)
                if (step.requiredDocuments.isNotEmpty()) BulletGroup("這一步要準備", step.requiredDocuments)
                if (step.needsConfirmation) {
                    InlineBanner("需要再次確認", "此步驟可能依年度或個人身分不同，請核對官方說明。", BannerKind.Warning)
                }
                step.actionUrl?.let { SourceLink("開啟申請頁面", it) }
                step.sourceUrls.distinct().forEachIndexed { index, url -> SourceLink("步驟來源 ${index + 1}", url) }
            }
        }
    }
}

@Composable
private fun DetailLabel(label: String, value: String) {
    Row(horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm), verticalAlignment = Alignment.Top) {
        Icon(Icons.Default.Schedule, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
        Column(Modifier.weight(1f)) {
            Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(value, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.SemiBold)
        }
    }
}

@Composable
private fun ExperiencesSection(
    experiences: StudentExperienceDigest?,
    isLoading: Boolean,
    errorMessage: String?,
    onRefresh: () -> Unit,
    wide: Boolean,
) {
    SectionHeader(
        eyebrow = "文章與影片交叉整理",
        title = "其他學生去過的心得",
        detail = "先看重複出現的生活、課業與文化觀察，再開啟原始文章或影片了解完整脈絡。",
    )
    when {
        experiences != null -> {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs)) {
                MiniMetric("來源", experiences.totalSources, Modifier.weight(1f))
                MiniMetric("文章", experiences.articleCount, Modifier.weight(1f))
                MiniMetric("影片", experiences.videoCount, Modifier.weight(1f))
            }
            if (experiences.coverageNote.isNotBlank()) {
                InlineBanner("資料涵蓋說明", experiences.coverageNote, BannerKind.Info)
            }
            if (experiences.highlights.isNotEmpty()) {
                SectionHeader(title = "跨來源重點", detail = "同一主題由多個來源交叉整理。")
                if (wide) {
                    experiences.highlights.chunked(2).forEach { row ->
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.md)) {
                            row.forEach { highlight ->
                                ExchangeCard(Modifier.weight(1f)) {
                                    Text(highlight.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                                    Text(highlight.summary, style = MaterialTheme.typography.bodyLarge)
                                    Text("${highlight.sourceCount} 個來源", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                                }
                            }
                            if (row.size == 1) androidx.compose.foundation.layout.Spacer(Modifier.weight(1f))
                        }
                    }
                } else {
                    experiences.highlights.forEach { highlight ->
                        ExchangeCard {
                            Text(highlight.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                            Text(highlight.summary, style = MaterialTheme.typography.bodyLarge)
                            Text("${highlight.sourceCount} 個來源", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                        }
                    }
                }
            }
            SectionHeader(title = "原始心得來源", detail = "可開啟文章或影片閱讀完整內容。")
            if (experiences.sources.isEmpty()) {
                InlineBanner("目前沒有可驗證的心得來源", "系統不會用無法核對的內容填補空缺。", BannerKind.Warning)
            } else {
                experiences.sources.forEach { ExperienceSourceCard(it) }
            }
            if (experiences.disclaimer.isNotBlank()) {
                InlineBanner("閱讀提醒", experiences.disclaimer, BannerKind.Warning)
            }
        }
        isLoading -> LoadingState("正在載入學生文章與影片心得")
        errorMessage != null -> ErrorState(errorMessage, onRefresh)
        else -> InlineBanner("心得尚未整理", "重新整理後，系統會嘗試尋找可驗證的公開文章與影片。", BannerKind.Info)
    }
}

@Composable
private fun MiniMetric(label: String, value: Int, modifier: Modifier = Modifier) {
    ExchangeCard(modifier) {
        Text(value.toString(), style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.primary)
        Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun ExperienceSourceCard(source: StudentExperienceSource) {
    var expanded by remember(source.contentHash) { mutableStateOf(false) }
    ExchangeCard {
        Row(
            Modifier
                .fillMaxWidth()
                .heightIn(min = ExchangeSpacing.minimumTarget)
                .clickable(role = Role.Button) { expanded = !expanded },
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm),
        ) {
            Icon(
                if (source.sourceType.contains("video", true)) Icons.Default.PlayCircle else Icons.AutoMirrored.Filled.Article,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
            )
            Column(Modifier.weight(1f)) {
                Text(source.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Text(
                    listOf(source.platform, source.language, source.perspective).filter { it.isNotBlank() }.joinToString(" · "),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Icon(if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore, contentDescription = if (expanded) "收合心得" else "展開心得")
        }
        Text(source.summary, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.SemiBold)
        AnimatedVisibility(expanded) {
            Column(verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
                if (source.themes.isNotEmpty()) BulletGroup("內容主題", source.themes)
                SourceLink(if (source.sourceType.contains("video", true)) "觀看完整影片" else "閱讀完整文章", source.sourceUrl)
            }
        }
    }
}
