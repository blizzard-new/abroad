package tw.edu.cgu.exchangeguide

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.lifecycle.viewmodel.compose.viewModel
import tw.edu.cgu.exchangeguide.ui.AppearanceMode
import tw.edu.cgu.exchangeguide.ui.ExchangeGuideApp
import tw.edu.cgu.exchangeguide.ui.ExchangeViewModel
import tw.edu.cgu.exchangeguide.ui.theme.ExchangeGuideTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val preferences = getSharedPreferences("exchange_guide", MODE_PRIVATE)

        setContent {
            val exchangeViewModel: ExchangeViewModel = viewModel()
            val state by exchangeViewModel.state.collectAsState()
            val storedMode = preferences.getString("appearance_mode", AppearanceMode.Light.name)
            val initialMode = AppearanceMode.entries.firstOrNull { it.name == storedMode } ?: AppearanceMode.Light
            if (state.appearanceMode == AppearanceMode.Light && initialMode != AppearanceMode.Light) {
                exchangeViewModel.setAppearanceMode(initialMode)
            }

            ExchangeGuideTheme(appearanceMode = state.appearanceMode, dynamicColor = false) {
                ExchangeGuideApp(
                    state = state,
                    onDestinationSelected = exchangeViewModel::selectDestination,
                    onRefresh = exchangeViewModel::loadDashboard,
                    onUniversitySelected = exchangeViewModel::openUniversity,
                    onUniversityClosed = exchangeViewModel::closeUniversity,
                    onSchoolDetailsRefresh = { exchangeViewModel.loadSchoolDetails(forceRefresh = true) },
                    onAppearanceModeChanged = { mode ->
                        preferences.edit().putString("appearance_mode", mode.name).apply()
                        exchangeViewModel.setAppearanceMode(mode)
                    },
                )
            }
        }
    }
}
