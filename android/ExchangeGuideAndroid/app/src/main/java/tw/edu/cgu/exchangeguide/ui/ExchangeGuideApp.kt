package tw.edu.cgu.exchangeguide.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Badge
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import tw.edu.cgu.exchangeguide.data.model.PartnerUniversity
import tw.edu.cgu.exchangeguide.ui.screens.DeadlinesScreen
import tw.edu.cgu.exchangeguide.ui.screens.EligibilityScreen
import tw.edu.cgu.exchangeguide.ui.screens.HomeScreen
import tw.edu.cgu.exchangeguide.ui.screens.SchoolDetailScreen
import tw.edu.cgu.exchangeguide.ui.screens.SchoolsScreen
import tw.edu.cgu.exchangeguide.ui.screens.SupportScreen

private val liquidDestinationOrder = listOf(
    ExchangeDestination.Home,
    ExchangeDestination.Deadlines,
    ExchangeDestination.Schools,
    ExchangeDestination.Support,
    ExchangeDestination.Eligibility,
)

private fun ExchangeDestination.icon(): ImageVector = when (this) {
    ExchangeDestination.Home -> Icons.Default.Home
    ExchangeDestination.Schools -> Icons.Default.Search
    ExchangeDestination.Deadlines -> Icons.Default.CalendarMonth
    ExchangeDestination.Support -> Icons.Default.Description
    ExchangeDestination.Eligibility -> Icons.Default.AccountCircle
}

@Composable
fun ExchangeGuideApp(
    state: ExchangeUiState,
    onDestinationSelected: (ExchangeDestination) -> Unit,
    onRefresh: () -> Unit,
    onUniversitySelected: (PartnerUniversity) -> Unit,
    onUniversityClosed: () -> Unit,
    onSchoolDetailsRefresh: () -> Unit,
    onAppearanceModeChanged: (AppearanceMode) -> Unit,
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
    ) {
        val contentModifier = Modifier
            .fillMaxSize()
            .padding(bottom = 94.dp)

        if (state.selectedUniversity != null) {
            SchoolDetailScreen(
                university = state.selectedUniversity,
                workflow = state.workflow,
                experiences = state.experiences,
                isLoading = state.isSchoolDetailLoading,
                errorMessage = state.schoolDetailError,
                onBack = onUniversityClosed,
                onRefresh = onSchoolDetailsRefresh,
                modifier = contentModifier,
            )
        } else {
            when (state.destination) {
                ExchangeDestination.Home -> HomeScreen(
                    dashboard = state.dashboard,
                    isLoading = state.isLoading,
                    errorMessage = state.errorMessage,
                    onRefresh = onRefresh,
                    onTaskSelected = onDestinationSelected,
                    onUniversitySelected = onUniversitySelected,
                    modifier = contentModifier,
                )
                ExchangeDestination.Schools -> SchoolsScreen(
                    dashboard = state.dashboard,
                    isLoading = state.isLoading,
                    errorMessage = state.errorMessage,
                    onRefresh = onRefresh,
                    onUniversitySelected = onUniversitySelected,
                    modifier = contentModifier,
                )
                ExchangeDestination.Deadlines -> DeadlinesScreen(
                    dashboard = state.dashboard,
                    isLoading = state.isLoading,
                    errorMessage = state.errorMessage,
                    onRefresh = onRefresh,
                    onUniversitySelected = onUniversitySelected,
                    modifier = contentModifier,
                )
                ExchangeDestination.Support -> SupportScreen(
                    dashboard = state.dashboard,
                    isLoading = state.isLoading,
                    errorMessage = state.errorMessage,
                    onRefresh = onRefresh,
                    modifier = contentModifier,
                )
                ExchangeDestination.Eligibility -> EligibilityScreen(
                    dashboard = state.dashboard,
                    isLoading = state.isLoading,
                    errorMessage = state.errorMessage,
                    appearanceMode = state.appearanceMode,
                    onRefresh = onRefresh,
                    onAppearanceModeChanged = onAppearanceModeChanged,
                    onUniversitySelected = onUniversitySelected,
                    modifier = contentModifier,
                )
            }
        }

        LiquidNavigationBar(
            selected = state.destination,
            supportCount = state.dashboard?.documentExplanations?.size ?: 0,
            onSelected = onDestinationSelected,
            modifier = Modifier.align(Alignment.BottomCenter),
        )
    }
}

@Composable
private fun LiquidNavigationBar(
    selected: ExchangeDestination,
    supportCount: Int,
    onSelected: (ExchangeDestination) -> Unit,
    modifier: Modifier = Modifier,
) {
    BoxWithConstraints(
        modifier = modifier
            .fillMaxWidth()
            .navigationBarsPadding(),
        contentAlignment = Alignment.Center,
    ) {
        val compact = maxWidth < 380.dp
        val circleSize = if (compact) 52.dp else 58.dp
        val searchWidth = if (compact) 96.dp else 116.dp
        val gap = if (compact) 4.dp else 6.dp

        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.spacedBy(gap),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            liquidDestinationOrder.forEach { destination ->
                LiquidNavigationButton(
                    destination = destination,
                    selected = selected == destination,
                    size = circleSize,
                    searchWidth = searchWidth,
                    badgeCount = if (destination == ExchangeDestination.Support) supportCount else 0,
                    onClick = { onSelected(destination) },
                )
            }
        }
    }
}

@Composable
private fun LiquidNavigationButton(
    destination: ExchangeDestination,
    selected: Boolean,
    size: Dp,
    searchWidth: Dp,
    badgeCount: Int,
    onClick: () -> Unit,
) {
    val isSearch = destination == ExchangeDestination.Schools
    val shape = if (isSearch) RoundedCornerShape(percent = 50) else CircleShape
    val modifier = if (isSearch) {
        Modifier.width(searchWidth).height(size)
    } else {
        Modifier.size(size)
    }
    val foreground = when {
        selected -> MaterialTheme.colorScheme.onSurface
        isSearch -> MaterialTheme.colorScheme.onSurface.copy(alpha = 0.70f)
        else -> MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.72f)
    }

    Box(modifier = modifier) {
        Surface(
            modifier = Modifier.fillMaxSize().clickable(role = Role.Tab, onClick = onClick),
            shape = shape,
            color = MaterialTheme.colorScheme.surface,
            tonalElevation = 0.dp,
            shadowElevation = if (selected) 13.dp else 9.dp,
            border = BorderStroke(
                width = 1.dp,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = if (selected) 0.14f else 0.08f),
            ),
        ) {
            Row(
                modifier = Modifier.fillMaxSize(),
                horizontalArrangement = Arrangement.spacedBy(
                    space = 9.dp,
                    alignment = Alignment.CenterHorizontally,
                ),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    imageVector = destination.icon(),
                    contentDescription = destination.title,
                    tint = foreground,
                    modifier = Modifier.size(if (isSearch) 25.dp else 27.dp),
                )
                if (isSearch) {
                    Text(
                        text = "搜尋",
                        color = foreground,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                    )
                }
            }

        }

        if (badgeCount > 0) {
            Badge(
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .offset(x = 2.dp, y = (-3).dp),
                containerColor = Color(0xFF168A52),
                contentColor = Color.White,
            ) {
                Text("1")
            }
        }
    }
}
