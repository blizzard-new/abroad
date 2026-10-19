package tw.edu.cgu.exchangeguide.data.network

import retrofit2.http.GET
import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.Path
import retrofit2.http.POST
import retrofit2.http.Query
import tw.edu.cgu.exchangeguide.data.model.SearchResult
import tw.edu.cgu.exchangeguide.data.model.StudentDashboard
import tw.edu.cgu.exchangeguide.data.model.StudentExperienceDigest
import tw.edu.cgu.exchangeguide.data.model.UniversityApplicationWorkflow
import tw.edu.cgu.exchangeguide.data.model.*

interface ExchangeApi {
    @GET("student-dashboard")
    suspend fun getDashboard(@Query("school") school: String): StudentDashboard

    @GET("application-workflow")
    suspend fun getApplicationWorkflow(@Query("school") school: String): UniversityApplicationWorkflow

    @POST("application-workflow/refresh")
    suspend fun refreshApplicationWorkflow(@Query("school") school: String): UniversityApplicationWorkflow

    @GET("student-experiences")
    suspend fun getStudentExperiences(@Query("school") school: String): StudentExperienceDigest

    @POST("student-experiences/refresh")
    suspend fun refreshStudentExperiences(@Query("school") school: String): StudentExperienceDigest

    @GET("search")
    suspend fun search(@Query("q") query: String, @Query("limit") limit: Int = 20): List<SearchResult>

    @POST("community/identities")
    suspend fun createIdentity(@Body body: AnonymousIdentityCreate): AnonymousIdentitySession

    @GET("community/posts")
    suspend fun getCommunityPosts(@Query("school") school: String): List<CommunityPostThread>

    @POST("community/posts")
    suspend fun publishPost(
        @Header("X-Anonymous-ID") identityId: String,
        @Header("X-Anonymous-Token") token: String,
        @Body body: CommunityPostCreate,
    ): CommunityPost

    @POST("community/posts/{postId}/comments")
    suspend fun publishComment(
        @Path("postId") postId: String,
        @Header("X-Anonymous-ID") identityId: String,
        @Header("X-Anonymous-Token") token: String,
        @Body body: CommunityCommentCreate,
    ): CommunityPostComment

    @GET("community/chat")
    suspend fun getPublicChat(@Query("school") school: String): List<PublicChatMessage>

    @POST("community/chat")
    suspend fun publishChat(
        @Header("X-Anonymous-ID") identityId: String,
        @Header("X-Anonymous-Token") token: String,
        @Body body: PublicChatMessageCreate,
    ): PublicChatMessage

    @GET("community/conversations")
    suspend fun getConversations(
        @Header("X-Anonymous-ID") identityId: String,
        @Header("X-Anonymous-Token") token: String,
    ): List<PrivateConversation>

    @POST("community/conversations")
    suspend fun inviteConversation(
        @Header("X-Anonymous-ID") identityId: String,
        @Header("X-Anonymous-Token") token: String,
        @Body body: PrivateConversationCreate,
    ): PrivateConversation

    @POST("community/conversations/{conversationId}/accept")
    suspend fun acceptConversation(
        @Path("conversationId") conversationId: String,
        @Header("X-Anonymous-ID") identityId: String,
        @Header("X-Anonymous-Token") token: String,
    ): PrivateConversation

    @GET("community/conversations/{conversationId}/messages")
    suspend fun getPrivateMessages(
        @Path("conversationId") conversationId: String,
        @Header("X-Anonymous-ID") identityId: String,
        @Header("X-Anonymous-Token") token: String,
    ): List<PrivateMessage>

    @POST("community/conversations/{conversationId}/messages")
    suspend fun sendPrivateMessage(
        @Path("conversationId") conversationId: String,
        @Header("X-Anonymous-ID") identityId: String,
        @Header("X-Anonymous-Token") token: String,
        @Body body: PrivateMessageCreate,
    ): PrivateMessage

    @POST("community/blocks")
    suspend fun blockIdentity(
        @Header("X-Anonymous-ID") identityId: String,
        @Header("X-Anonymous-Token") token: String,
        @Body body: CommunityBlockCreate,
    ): CommunityBlock

    @POST("community/reports")
    suspend fun reportContent(
        @Header("X-Anonymous-ID") identityId: String,
        @Header("X-Anonymous-Token") token: String,
        @Body body: CommunityReportCreate,
    ): CommunityReport
}
