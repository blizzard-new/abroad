package tw.edu.cgu.exchangeguide.ui.components

import android.content.Intent
import androidx.core.net.toUri
import androidx.compose.foundation.background
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.ErrorOutline
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.automirrored.filled.OpenInNew
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.WarningAmber
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import tw.edu.cgu.exchangeguide.data.model.PartnerUniversity
import tw.edu.cgu.exchangeguide.data.model.RuleExplanation
import tw.edu.cgu.exchangeguide.ui.theme.ExchangeSpacing

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PageScaffold(
    title: String,
    modifier: Modifier = Modifier,
    onRefresh: (() -> Unit)? = null,
    onBack: (() -> Unit)? = null,
    content: @Composable (PaddingValues) -> Unit,
) {
    Scaffold(
        modifier = modifier.background(
            Brush.verticalGradient(
                listOf(
                    MaterialTheme.colorScheme.background,
                    MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.22f),
                    MaterialTheme.colorScheme.background,
                ),
            ),
        ),
        containerColor = Color.Transparent,
        topBar = {
            TopAppBar(
                title = { Text(title, style = MaterialTheme.typography.titleLarge) },
                navigationIcon = {
                    if (onBack != null) {
                        IconButton(onClick = onBack, modifier = Modifier.size(ExchangeSpacing.minimumTarget)) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
                        }
                    }
                },
                actions = {
                    if (onRefresh != null) {
                        IconButton(onClick = onRefresh, modifier = Modifier.size(ExchangeSpacing.minimumTarget)) {
                            Icon(Icons.Default.Refresh, contentDescription = "重新整理")
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background.copy(alpha = 0.94f),
                    scrolledContainerColor = MaterialTheme.colorScheme.background.copy(alpha = 0.98f),
                ),
            )
        },
        content = content,
    )
}

@Composable
fun ResponsiveContent(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.(isWide: Boolean) -> Unit,
) {
    BoxWithConstraints(modifier = modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
        val wide = maxWidth >= 840.dp
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .widthIn(max = ExchangeSpacing.contentMax)
                .padding(horizontal = if (wide) ExchangeSpacing.lg else ExchangeSpacing.md),
            verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.xl),
        ) {
            content(wide)
        }
    }
}

@Composable
fun SectionHeader(
    title: String,
    modifier: Modifier = Modifier,
    detail: String? = null,
    eyebrow: String? = null,
) {
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.xxs)) {
        if (!eyebrow.isNullOrBlank()) {
            Text(
                text = eyebrow,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.SemiBold,
            )
        }
        Text(
            text = title,
            style = MaterialTheme.typography.titleLarge,
            color = MaterialTheme.colorScheme.onBackground,
            modifier = Modifier.semantics { heading() },
        )
        if (!detail.isNullOrBlank()) {
            Text(
                text = detail,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
fun ExchangeCard(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit,
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp, pressedElevation = 3.dp),
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm),
            content = content,
        )
    }
}

@Composable
fun MetricTile(value: String, label: String, icon: ImageVector, tint: Color, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier.heightIn(min = 112.dp),
        shape = RoundedCornerShape(22.dp),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 1.dp,
    ) {
        Column(
            modifier = Modifier.padding(ExchangeSpacing.md),
            verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs),
        ) {
            Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.size(24.dp))
            Text(value, style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.onSurface)
            Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
fun TaskButton(
    title: String,
    detail: String,
    icon: ImageVector,
    tint: Color,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 72.dp)
            .clickable(role = Role.Button, onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 1.dp,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = ExchangeSpacing.md, vertical = ExchangeSpacing.sm),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm),
        ) {
            Surface(shape = RoundedCornerShape(12.dp), color = tint.copy(alpha = 0.13f)) {
                Box(Modifier.size(44.dp), contentAlignment = Alignment.Center) {
                    Icon(icon, contentDescription = null, tint = tint)
                }
            }
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Icon(
                Icons.AutoMirrored.Filled.ArrowForward,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f),
            )
        }
    }
}

@Composable
fun SearchField(
    value: String,
    onValueChange: (String) -> Unit,
    placeholder: String,
    modifier: Modifier = Modifier,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = modifier.fillMaxWidth().heightIn(min = ExchangeSpacing.minimumTarget),
        singleLine = true,
        leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
        placeholder = { Text(placeholder) },
        shape = RoundedCornerShape(12.dp),
        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
        keyboardActions = KeyboardActions(onSearch = {}),
    )
}

enum class BannerKind { Info, Warning, Error }

@Composable
fun InlineBanner(title: String, message: String, kind: BannerKind, modifier: Modifier = Modifier) {
    val icon = when (kind) {
        BannerKind.Info -> Icons.Default.Info
        BannerKind.Warning -> Icons.Default.WarningAmber
        BannerKind.Error -> Icons.Default.ErrorOutline
    }
    val tint = when (kind) {
        BannerKind.Info -> MaterialTheme.colorScheme.primary
        BannerKind.Warning -> Color(0xFFB66B00)
        BannerKind.Error -> MaterialTheme.colorScheme.error
    }
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = tint.copy(alpha = 0.09f),
    ) {
        Row(
            Modifier.padding(ExchangeSpacing.md),
            horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm),
            verticalAlignment = Alignment.Top,
        ) {
            Icon(icon, contentDescription = null, tint = tint)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.xxs)) {
                Text(title, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.onSurface)
                Text(message, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@Composable
fun UniversityRow(university: PartnerUniversity, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 76.dp)
            .clickable(role = Role.Button, onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 1.dp,
    ) {
        Row(
            Modifier.padding(ExchangeSpacing.md),
            horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.xxs)) {
                Text(university.schoolName, style = MaterialTheme.typography.titleMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
                Text(
                    listOfNotNull(university.country, university.programType).joinToString(" · ").ifBlank { "交換學校" },
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                if (!university.applicationDeadline.isNullOrBlank()) {
                    Text(
                        university.applicationDeadline,
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.primary,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }
            Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = "查看 ${university.schoolName} 詳情")
        }
    }
}

@Composable
fun ExpandableDocumentCard(document: RuleExplanation, modifier: Modifier = Modifier) {
    var expanded by remember { mutableStateOf(false) }
    ExchangeCard(modifier) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = ExchangeSpacing.minimumTarget)
                .clickable(role = Role.Button) { expanded = !expanded },
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm),
        ) {
            Icon(Icons.Default.Description, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
            Column(Modifier.weight(1f)) {
                Text(document.documentType, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                Text(document.title, style = MaterialTheme.typography.titleMedium)
            }
            Icon(if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore, contentDescription = if (expanded) "收合" else "展開")
        }
        Text(
            document.summary,
            style = MaterialTheme.typography.bodyLarge,
            fontWeight = FontWeight.SemiBold,
            color = MaterialTheme.colorScheme.onSurface,
        )
        AnimatedVisibility(expanded) {
            Column(verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
                if (document.appliesTo.isNotEmpty()) BulletGroup("適用對象", document.appliesTo)
                if (document.keyPoints.isNotEmpty()) BulletGroup("學生最需要知道", document.keyPoints)
                HorizontalDivider(color = MaterialTheme.colorScheme.outline.copy(alpha = 0.5f))
                document.documentUrl?.let { SourceLink("查看完整文件", it) }
                SourceLink("查看官方來源", document.source.sourceUrl)
            }
        }
    }
}

@Composable
fun BulletGroup(title: String, items: List<String>, modifier: Modifier = Modifier) {
    Column(modifier, verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs)) {
        Text(title, style = MaterialTheme.typography.titleSmall)
        items.forEach { item ->
            Row(horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs), verticalAlignment = Alignment.Top) {
                Text("•", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                Text(item, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@Composable
fun SourceLink(title: String, url: String, modifier: Modifier = Modifier) {
    if (url.isBlank()) return
    val context = LocalContext.current
    Row(
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = ExchangeSpacing.minimumTarget)
            .clickable(role = Role.Button) {
                context.startActivity(Intent(Intent.ACTION_VIEW, url.toUri()))
            }
            .padding(vertical = ExchangeSpacing.xs),
        horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(Icons.AutoMirrored.Filled.OpenInNew, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
        Text(title, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary, modifier = Modifier.weight(1f))
    }
}

@Composable
fun LoadingState(message: String, modifier: Modifier = Modifier) {
    val transition = rememberInfiniteTransition(label = "loading")
    val alpha by transition.animateFloat(
        initialValue = 0.35f,
        targetValue = 0.72f,
        animationSpec = infiniteRepeatable(tween(850), RepeatMode.Reverse),
        label = "loading-alpha",
    )
    Column(
        modifier = modifier.fillMaxWidth().padding(ExchangeSpacing.md),
        verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.md),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
            CircularProgressIndicator(Modifier.size(24.dp), strokeWidth = 2.dp)
            Text(message, style = MaterialTheme.typography.bodyLarge)
        }
        repeat(4) { index ->
            Surface(
                modifier = Modifier.fillMaxWidth().height(if (index == 0) 148.dp else 88.dp).alpha(alpha),
                shape = RoundedCornerShape(16.dp),
                color = MaterialTheme.colorScheme.surfaceVariant,
            ) {}
        }
    }
}

@Composable
fun ErrorState(message: String, onRetry: () -> Unit, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxWidth().padding(ExchangeSpacing.lg),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.md),
    ) {
        Icon(Icons.Default.ErrorOutline, contentDescription = null, tint = MaterialTheme.colorScheme.error, modifier = Modifier.size(36.dp))
        Text("無法載入資料", style = MaterialTheme.typography.titleLarge)
        Text(message, style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Button(onClick = onRetry, modifier = Modifier.heightIn(min = ExchangeSpacing.minimumTarget)) {
            Icon(Icons.Default.Refresh, contentDescription = null)
            Spacer(Modifier.width(ExchangeSpacing.xs))
            Text("重新整理")
        }
    }
}
