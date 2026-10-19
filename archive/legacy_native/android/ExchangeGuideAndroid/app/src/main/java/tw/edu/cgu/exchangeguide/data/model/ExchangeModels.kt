package tw.edu.cgu.exchangeguide.data.model

import com.google.gson.annotations.SerializedName

data class SourceReference(
    val title: String = "官方來源",
    @SerializedName("source_url") val sourceUrl: String = "",
    val category: String? = null,
)

data class StudentInfoItem(
    val title: String = "",
    val details: List<String> = emptyList(),
    val source: SourceReference? = null,
)

data class RuleExplanation(
    val title: String = "",
    val summary: String = "",
    @SerializedName("key_points") val keyPoints: List<String> = emptyList(),
    @SerializedName("applies_to") val appliesTo: List<String> = emptyList(),
    val source: SourceReference = SourceReference(),
    @SerializedName("document_url") val documentUrl: String? = null,
    @SerializedName("document_type") val documentType: String = "文件",
    @SerializedName("full_text_extracted") val fullTextExtracted: Boolean = false,
)

data class PartnerUniversity(
    @SerializedName("program_type") val programType: String? = null,
    val country: String? = null,
    @SerializedName("school_name") val schoolName: String = "",
    val website: String? = null,
    val colleges: String? = null,
    @SerializedName("degree_levels") val degreeLevels: String? = null,
    @SerializedName("study_period") val studyPeriod: String? = null,
    val quota: String? = null,
    val eligibility: String? = null,
    @SerializedName("application_deadline") val applicationDeadline: String? = null,
    @SerializedName("application_info") val applicationInfo: String? = null,
    @SerializedName("tuition_info") val tuitionInfo: String? = null,
    @SerializedName("ranking_info") val rankingInfo: String? = null,
    @SerializedName("source_url") val sourceUrl: String = "",
)

data class StudentDashboard(
    @SerializedName("school_name") val schoolName: String = "長庚大學",
    @SerializedName("last_checked") val lastChecked: String? = null,
    @SerializedName("application_periods") val applicationPeriods: List<StudentInfoItem> = emptyList(),
    @SerializedName("program_overview") val programOverview: List<StudentInfoItem> = emptyList(),
    val eligibility: List<StudentInfoItem> = emptyList(),
    @SerializedName("language_requirements") val languageRequirements: List<StudentInfoItem> = emptyList(),
    @SerializedName("required_documents") val requiredDocuments: List<StudentInfoItem> = emptyList(),
    @SerializedName("scholarship_info") val scholarshipInfo: List<StudentInfoItem> = emptyList(),
    @SerializedName("document_explanations") val documentExplanations: List<RuleExplanation> = emptyList(),
    @SerializedName("rule_explanations") val ruleExplanations: List<RuleExplanation> = emptyList(),
    @SerializedName("partner_universities") val partnerUniversities: List<PartnerUniversity> = emptyList(),
    val sources: List<SourceReference> = emptyList(),
)

data class ApplicationStep(
    val order: Int = 0,
    val phase: String = "",
    val title: String = "",
    @SerializedName("responsible_party") val responsibleParty: String = "",
    val timing: String? = null,
    val summary: String = "",
    val details: List<String> = emptyList(),
    @SerializedName("required_documents") val requiredDocuments: List<String> = emptyList(),
    @SerializedName("action_url") val actionUrl: String? = null,
    @SerializedName("source_urls") val sourceUrls: List<String> = emptyList(),
    @SerializedName("needs_confirmation") val needsConfirmation: Boolean = false,
)

data class ApplicationWorkflowSource(
    val title: String = "",
    @SerializedName("source_url") val sourceUrl: String = "",
    val role: String = "",
    @SerializedName("checked_at") val checkedAt: String = "",
)

data class UniversityApplicationWorkflow(
    @SerializedName("school_name") val schoolName: String = "",
    val country: String? = null,
    @SerializedName("program_type") val programType: String? = null,
    val steps: List<ApplicationStep> = emptyList(),
    val sources: List<ApplicationWorkflowSource> = emptyList(),
    @SerializedName("last_checked") val lastChecked: String? = null,
    @SerializedName("coverage_status") val coverageStatus: String = "",
    @SerializedName("coverage_note") val coverageNote: String = "",
    val disclaimer: String = "",
)

data class ExperienceHighlight(
    val theme: String = "",
    val title: String = "",
    val summary: String = "",
    @SerializedName("source_count") val sourceCount: Int = 0,
    @SerializedName("key_points") val keyPoints: List<String> = emptyList(),
    @SerializedName("source_urls") val sourceUrls: List<String> = emptyList(),
)

data class StudentExperienceSource(
    @SerializedName("school_name") val schoolName: String = "",
    val country: String? = null,
    val title: String = "",
    @SerializedName("source_url") val sourceUrl: String = "",
    @SerializedName("source_type") val sourceType: String = "article",
    val platform: String = "",
    val language: String = "",
    val summary: String = "",
    val themes: List<String> = emptyList(),
    val perspective: String = "",
    @SerializedName("published_at") val publishedAt: String? = null,
    @SerializedName("discovered_at") val discoveredAt: String = "",
    @SerializedName("content_hash") val contentHash: String = "",
)

data class StudentExperienceDigest(
    @SerializedName("school_name") val schoolName: String = "",
    val country: String? = null,
    @SerializedName("total_sources") val totalSources: Int = 0,
    @SerializedName("article_count") val articleCount: Int = 0,
    @SerializedName("video_count") val videoCount: Int = 0,
    @SerializedName("community_count") val communityCount: Int = 0,
    val highlights: List<ExperienceHighlight> = emptyList(),
    val sources: List<StudentExperienceSource> = emptyList(),
    @SerializedName("last_checked") val lastChecked: String? = null,
    @SerializedName("coverage_note") val coverageNote: String = "",
    val disclaimer: String = "",
)

data class SearchResult(
    val title: String = "",
    val snippet: String = "",
    @SerializedName("source_url") val sourceUrl: String = "",
    val category: String? = null,
)

data class AnonymousIdentityCreate(@SerializedName("display_name") val displayName: String)

data class AnonymousIdentitySession(
    val id: String = "",
    @SerializedName("display_name") val displayName: String = "",
    @SerializedName("access_token") val accessToken: String = "",
)

data class CommunityPostCreate(
    @SerializedName("school_name") val schoolName: String,
    @SerializedName("post_type") val postType: String,
    val title: String,
    val body: String,
)

data class CommunityPost(
    val id: String = "",
    @SerializedName("school_name") val schoolName: String = "",
    @SerializedName("author_id") val authorId: String = "",
    @SerializedName("display_name") val displayName: String = "",
    @SerializedName("post_type") val postType: String = "discussion",
    val title: String = "",
    val body: String = "",
    val status: String = "approved",
    @SerializedName("comment_count") val commentCount: Int = 0,
    @SerializedName("created_at") val createdAt: String = "",
)

data class CommunityPostComment(
    val id: String = "",
    @SerializedName("post_id") val postId: String = "",
    @SerializedName("author_id") val authorId: String = "",
    @SerializedName("display_name") val displayName: String = "",
    val body: String = "",
    val status: String = "approved",
    @SerializedName("created_at") val createdAt: String = "",
)

data class CommunityPostThread(
    val post: CommunityPost = CommunityPost(),
    val comments: List<CommunityPostComment> = emptyList(),
)

data class CommunityCommentCreate(val body: String)

data class PublicChatMessageCreate(
    @SerializedName("school_name") val schoolName: String,
    val body: String,
)

data class PublicChatMessage(
    val id: String = "",
    @SerializedName("school_name") val schoolName: String = "",
    @SerializedName("author_id") val authorId: String = "",
    @SerializedName("display_name") val displayName: String = "",
    val body: String = "",
    val status: String = "approved",
    @SerializedName("created_at") val createdAt: String = "",
)

data class PrivateConversationCreate(
    @SerializedName("school_name") val schoolName: String,
    @SerializedName("recipient_id") val recipientId: String,
    @SerializedName("initial_message") val initialMessage: String,
)

data class PrivateConversation(
    val id: String = "",
    @SerializedName("school_name") val schoolName: String = "",
    @SerializedName("sender_id") val senderId: String = "",
    @SerializedName("sender_name") val senderName: String = "",
    @SerializedName("recipient_id") val recipientId: String = "",
    @SerializedName("recipient_name") val recipientName: String = "",
    val status: String = "pending",
    @SerializedName("created_at") val createdAt: String = "",
    @SerializedName("updated_at") val updatedAt: String = "",
)

data class PrivateMessageCreate(val body: String)

data class PrivateMessage(
    val id: String = "",
    @SerializedName("conversation_id") val conversationId: String = "",
    @SerializedName("author_id") val authorId: String = "",
    @SerializedName("display_name") val displayName: String = "",
    val body: String = "",
    @SerializedName("created_at") val createdAt: String = "",
)

data class CommunityBlockCreate(@SerializedName("target_id") val targetId: String)
data class CommunityBlock(val id: String = "")

data class CommunityReportCreate(
    @SerializedName("resource_type") val resourceType: String,
    @SerializedName("resource_id") val resourceId: String,
    val reason: String,
)
data class CommunityReport(val id: String = "")
