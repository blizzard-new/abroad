package tw.edu.cgu.exchangeguide.data

import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import tw.edu.cgu.exchangeguide.data.model.StudentDashboard
import tw.edu.cgu.exchangeguide.data.model.StudentExperienceDigest
import tw.edu.cgu.exchangeguide.data.model.UniversityApplicationWorkflow
import tw.edu.cgu.exchangeguide.data.network.ExchangeApi

class ExchangeRepository(private val api: ExchangeApi) {
    suspend fun dashboard(school: String = "長庚大學"): StudentDashboard = api.getDashboard(school)

    suspend fun schoolDetails(
        school: String,
        forceRefresh: Boolean = false,
    ): Pair<UniversityApplicationWorkflow, StudentExperienceDigest> = coroutineScope {
        val workflow = async {
            if (forceRefresh) api.refreshApplicationWorkflow(school)
            else api.getApplicationWorkflow(school)
        }
        val experiences = async {
            if (forceRefresh) api.refreshStudentExperiences(school)
            else api.getStudentExperiences(school)
        }
        workflow.await() to experiences.await()
    }
}
