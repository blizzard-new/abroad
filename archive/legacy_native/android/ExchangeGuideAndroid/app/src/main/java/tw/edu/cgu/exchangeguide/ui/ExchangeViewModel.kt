package tw.edu.cgu.exchangeguide.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import tw.edu.cgu.exchangeguide.data.ExchangeRepository
import tw.edu.cgu.exchangeguide.data.model.PartnerUniversity
import tw.edu.cgu.exchangeguide.data.model.StudentDashboard
import tw.edu.cgu.exchangeguide.data.model.StudentExperienceDigest
import tw.edu.cgu.exchangeguide.data.model.UniversityApplicationWorkflow
import tw.edu.cgu.exchangeguide.data.network.ApiClient

enum class ExchangeDestination(val title: String, val compactTitle: String) {
    Home("總覽", "總覽"),
    Schools("找學校", "學校"),
    Deadlines("截止日期", "截止"),
    Support("補助與文件", "補助"),
    Eligibility("資格檢查", "資格"),
}

enum class AppearanceMode(val label: String) {
    System("跟隨系統"),
    Light("淺色"),
    Dark("深色"),
}

data class ExchangeUiState(
    val dashboard: StudentDashboard? = null,
    val isLoading: Boolean = true,
    val errorMessage: String? = null,
    val destination: ExchangeDestination = ExchangeDestination.Home,
    val selectedUniversity: PartnerUniversity? = null,
    val workflow: UniversityApplicationWorkflow? = null,
    val experiences: StudentExperienceDigest? = null,
    val isSchoolDetailLoading: Boolean = false,
    val schoolDetailError: String? = null,
    val appearanceMode: AppearanceMode = AppearanceMode.Light,
)

class ExchangeViewModel(
    private val repository: ExchangeRepository = ExchangeRepository(ApiClient.api),
) : ViewModel() {
    private val _state = MutableStateFlow(ExchangeUiState())
    val state: StateFlow<ExchangeUiState> = _state.asStateFlow()

    init {
        loadDashboard()
    }

    fun loadDashboard() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, errorMessage = null) }
            runCatching { repository.dashboard() }
                .onSuccess { dashboard ->
                    _state.update { it.copy(dashboard = dashboard, isLoading = false) }
                }
                .onFailure { error ->
                    _state.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = error.localizedMessage ?: "目前無法取得交換資訊",
                        )
                    }
                }
        }
    }

    fun selectDestination(destination: ExchangeDestination) {
        _state.update {
            it.copy(
                destination = destination,
                selectedUniversity = null,
                workflow = null,
                experiences = null,
                schoolDetailError = null,
            )
        }
    }

    fun openUniversity(university: PartnerUniversity) {
        _state.update {
            it.copy(
                selectedUniversity = university,
                workflow = null,
                experiences = null,
                schoolDetailError = null,
            )
        }
        loadSchoolDetails(forceRefresh = false)
    }

    fun closeUniversity() {
        _state.update {
            it.copy(
                selectedUniversity = null,
                workflow = null,
                experiences = null,
                schoolDetailError = null,
            )
        }
    }

    fun loadSchoolDetails(forceRefresh: Boolean) {
        val school = _state.value.selectedUniversity?.schoolName ?: return
        viewModelScope.launch {
            _state.update { it.copy(isSchoolDetailLoading = true, schoolDetailError = null) }
            runCatching { repository.schoolDetails(school, forceRefresh) }
                .onSuccess { (workflow, experiences) ->
                    _state.update {
                        it.copy(
                            workflow = workflow,
                            experiences = experiences,
                            isSchoolDetailLoading = false,
                        )
                    }
                }
                .onFailure { error ->
                    _state.update {
                        it.copy(
                            isSchoolDetailLoading = false,
                            schoolDetailError = error.localizedMessage ?: "無法載入學校申請流程與學生心得",
                        )
                    }
                }
        }
    }

    fun setAppearanceMode(mode: AppearanceMode) {
        _state.update { it.copy(appearanceMode = mode) }
    }
}
