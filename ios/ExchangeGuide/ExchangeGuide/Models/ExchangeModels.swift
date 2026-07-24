import Foundation

struct SourceReference: Codable, Hashable, Sendable {
    let title: String
    let sourceUrl: String
    let category: String?
}

struct StudentInfoItem: Codable, Hashable, Identifiable, Sendable {
    let title: String
    let details: [String]
    let source: SourceReference?

    var id: String { "\(title)-\(source?.sourceUrl ?? "local")" }
}

struct RuleExplanation: Codable, Hashable, Identifiable, Sendable {
    let title: String
    let summary: String
    let keyPoints: [String]
    let appliesTo: [String]
    let source: SourceReference
    let documentUrl: String?
    let documentType: String
    let fullTextExtracted: Bool

    var id: String { documentUrl ?? source.sourceUrl }
}

struct PartnerUniversity: Codable, Hashable, Identifiable, Sendable {
    let programType: String?
    let country: String?
    let schoolName: String
    let website: String?
    let colleges: String?
    let degreeLevels: String?
    let studyPeriod: String?
    let quota: String?
    let eligibility: String?
    let applicationDeadline: String?
    let applicationInfo: String?
    let tuitionInfo: String?
    let rankingInfo: String?
    let sourceUrl: String

    var id: String { schoolName }
}

struct StudentDashboard: Codable, Sendable {
    let schoolName: String
    let lastChecked: String?
    let applicationPeriods: [StudentInfoItem]
    let programOverview: [StudentInfoItem]
    let eligibility: [StudentInfoItem]
    let languageRequirements: [StudentInfoItem]
    let requiredDocuments: [StudentInfoItem]
    let scholarshipInfo: [StudentInfoItem]
    let documentExplanations: [RuleExplanation]
    let ruleExplanations: [RuleExplanation]
    let partnerUniversities: [PartnerUniversity]
    let sources: [SourceReference]
}

struct ApplicationStep: Codable, Hashable, Identifiable, Sendable {
    let order: Int
    let phase: String
    let title: String
    let responsibleParty: String
    let timing: String?
    let summary: String
    let details: [String]
    let requiredDocuments: [String]
    let actionUrl: String?
    let sourceUrls: [String]
    let needsConfirmation: Bool

    var id: Int { order }
}

struct ApplicationWorkflowSource: Codable, Hashable, Identifiable, Sendable {
    let title: String
    let sourceUrl: String
    let role: String
    let checkedAt: String

    var id: String { sourceUrl }
}

struct UniversityApplicationWorkflow: Codable, Sendable {
    let schoolName: String
    let country: String?
    let programType: String?
    let steps: [ApplicationStep]
    let sources: [ApplicationWorkflowSource]
    let lastChecked: String?
    let coverageStatus: String
    let coverageNote: String
    let disclaimer: String
}

struct ExperienceHighlight: Codable, Hashable, Identifiable, Sendable {
    let theme: String
    let title: String
    let summary: String
    let sourceCount: Int
    let keyPoints: [String]
    let sourceUrls: [String]

    var id: String { theme }
}

struct StudentExperienceSource: Codable, Hashable, Identifiable, Sendable {
    let schoolName: String
    let country: String?
    let title: String
    let sourceUrl: String
    let sourceType: String
    let platform: String
    let language: String
    let summary: String
    let themes: [String]
    let perspective: String
    let publishedAt: String?
    let discoveredAt: String
    let contentHash: String

    var id: String { contentHash }
}

struct StudentExperienceDigest: Codable, Sendable {
    let schoolName: String
    let country: String?
    let totalSources: Int
    let articleCount: Int
    let videoCount: Int
    let communityCount: Int
    let highlights: [ExperienceHighlight]
    let sources: [StudentExperienceSource]
    let lastChecked: String?
    let coverageNote: String
    let disclaimer: String
}

struct AnonymousIdentitySession: Codable, Sendable {
    let id: String
    let displayName: String
    let accessToken: String
}

struct AnonymousIdentityCreate: Codable, Sendable {
    let displayName: String
}

struct CommunityPostCreate: Codable, Sendable {
    let schoolName: String
    let postType: String
    let title: String
    let body: String
}

struct CommunityPost: Codable, Hashable, Identifiable, Sendable {
    let id: String
    let schoolName: String
    let authorId: String
    let displayName: String
    let postType: String
    let title: String
    let body: String
    let status: String
    let commentCount: Int
    let createdAt: String
}

struct CommunityPostComment: Codable, Hashable, Identifiable, Sendable {
    let id: String
    let postId: String
    let authorId: String
    let displayName: String
    let body: String
    let status: String
    let createdAt: String
}

struct CommunityPostThread: Codable, Hashable, Identifiable, Sendable {
    let post: CommunityPost
    let comments: [CommunityPostComment]

    var id: String { post.id }
}

struct CommunityCommentCreate: Codable, Sendable {
    let body: String
}

struct PublicChatMessageCreate: Codable, Sendable {
    let schoolName: String
    let body: String
}

struct PublicChatMessage: Codable, Hashable, Identifiable, Sendable {
    let id: String
    let schoolName: String
    let authorId: String
    let displayName: String
    let body: String
    let status: String
    let createdAt: String
}

struct PrivateConversationCreate: Codable, Sendable {
    let schoolName: String
    let recipientId: String
    let initialMessage: String
}

struct PrivateConversation: Codable, Hashable, Identifiable, Sendable {
    let id: String
    let schoolName: String
    let senderId: String
    let senderName: String
    let recipientId: String
    let recipientName: String
    let status: String
    let createdAt: String
    let updatedAt: String
}

struct PrivateMessageCreate: Codable, Sendable {
    let body: String
}

struct PrivateMessage: Codable, Hashable, Identifiable, Sendable {
    let id: String
    let conversationId: String
    let authorId: String
    let displayName: String
    let body: String
    let createdAt: String
}

struct CommunityBlockCreate: Codable, Sendable {
    let targetId: String
}

struct CommunityBlock: Codable, Sendable {
    let id: String
    let ownerId: String
    let targetId: String
    let createdAt: String
}

struct CommunityReportCreate: Codable, Sendable {
    let resourceType: String
    let resourceId: String
    let reason: String
}

struct CommunityReport: Codable, Sendable {
    let id: String
    let reporterId: String
    let resourceType: String
    let resourceId: String
    let reason: String
    let createdAt: String
}
