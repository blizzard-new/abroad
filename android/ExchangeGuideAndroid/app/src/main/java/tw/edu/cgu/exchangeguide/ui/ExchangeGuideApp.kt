package tw.edu.cgu.exchangeguide.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.School
import androidx.compose.material.icons.filled.VolunteerActivism
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.adaptive.navigationsuite.NavigationSuiteScaffold
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import tw.edu.cgu.exchangeguide.data.model.PartnerUniversity
import tw.edu.cgu.exchangeguide.ui.screens.DeadlinesScreen
import tw.edu.cgu.exchangeguide.ui.screens.EligibilityScreen
import tw.edu.cgu.exchangeguide.ui.screens.HomeScreen
import tw.edu.cgu.exchangeguide.ui.screens.SchoolDetailScreen
import tw.edu.cgu.exchangeguide.ui.screens.SchoolsScreen
import tw.edu.cgu.exchangeguide.ui.screens.SupportScreen

private fun ExchangeDestination.icon(): ImageVector = when (this) {
    ExchangeDestination.Home -> Icons.Default.Home
    ExchangeDestination.Schools -> Icons.Default.School
    ExchangeDestination.Deadlines -> Icons.Default.CalendarMonth
    ExchangeDestination.Support -> Icons.Default.VolunteerActivism
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
    NavigationSuiteScaffold(
        modifier = Modifier.fillMaxSize(),
        navigationSuiteItems = {
            ExchangeDestination.entries.forEach { destination ->
                item(
                    selected = destination == state.destination,
                    onClick = { onDestinationSelected(destination) },
                    icon = { Icon(destination.icon(), contentDescription = null) },
                    label = { Text(destination.compactTitle) },
                )
            }
        },
    ) {
        val contentModifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)

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
    }
}
