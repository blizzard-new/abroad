package tw.edu.cgu.exchangeguide.ui.screens

enum class LanguageTest(val label: String, val minimum: Double, val scoreHint: String) {
    TOEIC("TOEIC", 700.0, "例如 750"),
    IELTS("IELTS", 5.5, "例如 6.0"),
    TOEFL("TOEFL iBT", 61.0, "例如 80"),
    Duolingo("Duolingo", 105.0, "例如 110"),
}

data class EligibilityAssessment(
    val academicScore: Double,
    val languageTest: LanguageTest,
    val languageScore: Double,
    val matchedSchoolCount: Int,
) {
    val academicPass: Boolean get() = academicScore >= 70.0
    val languagePass: Boolean get() = languageScore >= languageTest.minimum
    val isReady: Boolean get() = academicPass && languagePass
    val title: String get() = if (isReady) "初步符合基本門檻" else "還有條件需要補強"
    val summary: String
        get() = if (isReady) {
            "依目前輸入條件，找到 $matchedSchoolCount 間可能符合的合作學校。請再核對各校當期規定。"
        } else {
            "這是初步比對，不代表正式審查結果。先補足未通過的條件，再查看合作校詳細限制。"
        }
}
