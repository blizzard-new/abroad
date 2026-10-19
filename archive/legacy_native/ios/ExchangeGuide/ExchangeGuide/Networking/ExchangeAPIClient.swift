import Foundation

enum ExchangeAPIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case server(status: Int)
    case decoding(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            "API 網址無效。"
        case .invalidResponse:
            "伺服器沒有回傳有效資料。"
        case .server(let status):
            "伺服器回應錯誤（\(status)）。"
        case .decoding:
            "資料格式已更新，App 暫時無法讀取。"
        }
    }
}

actor ExchangeAPIClient {
    static let shared = ExchangeAPIClient()

    let baseURL: URL
    private let session: URLSession
    private let decoder: JSONDecoder

    init(
        baseURL: URL? = nil,
        session: URLSession = .shared
    ) {
        let configured = ProcessInfo.processInfo.environment["EXCHANGE_API_BASE_URL"]
        self.baseURL = baseURL
            ?? configured.flatMap(URL.init(string:))
            ?? URL(string: "http://127.0.0.1:8000")!
        self.session = session
        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
    }

    func dashboard() async throws -> StudentDashboard {
        try await request(path: "/student-dashboard", query: ["school": "長庚大學"])
    }

    func workflow(for school: String, refresh: Bool = false) async throws -> UniversityApplicationWorkflow {
        try await request(
            path: refresh ? "/application-workflow/refresh" : "/application-workflow",
            query: ["school": school],
            method: refresh ? "POST" : "GET"
        )
    }

    func experiences(for school: String, refresh: Bool = false) async throws -> StudentExperienceDigest {
        try await request(
            path: refresh ? "/student-experiences/refresh" : "/student-experiences",
            query: ["school": school],
            method: refresh ? "POST" : "GET"
        )
    }

    func createAnonymousIdentity(displayName: String) async throws -> AnonymousIdentitySession {
        try await send(
            path: "/community/identities",
            body: AnonymousIdentityCreate(displayName: displayName)
        )
    }

    func communityPosts(for school: String) async throws -> [CommunityPostThread] {
        try await request(path: "/community/posts", query: ["school": school])
    }

    func publishPost(
        _ post: CommunityPostCreate,
        identity: AnonymousIdentitySession
    ) async throws -> CommunityPost {
        try await send(path: "/community/posts", body: post, identity: identity)
    }

    func publishComment(
        postID: String,
        body: String,
        identity: AnonymousIdentitySession
    ) async throws -> CommunityPostComment {
        try await send(
            path: "/community/posts/\(postID)/comments",
            body: CommunityCommentCreate(body: body),
            identity: identity
        )
    }

    func publicChat(for school: String) async throws -> [PublicChatMessage] {
        try await request(path: "/community/chat", query: ["school": school])
    }

    func publishChat(
        school: String,
        body: String,
        identity: AnonymousIdentitySession
    ) async throws -> PublicChatMessage {
        try await send(
            path: "/community/chat",
            body: PublicChatMessageCreate(schoolName: school, body: body),
            identity: identity
        )
    }

    func conversations(identity: AnonymousIdentitySession) async throws -> [PrivateConversation] {
        try await request(path: "/community/conversations", headers: identity.headers)
    }

    func invite(
        school: String,
        recipientID: String,
        message: String,
        identity: AnonymousIdentitySession
    ) async throws -> PrivateConversation {
        try await send(
            path: "/community/conversations",
            body: PrivateConversationCreate(
                schoolName: school,
                recipientId: recipientID,
                initialMessage: message
            ),
            identity: identity
        )
    }

    func acceptConversation(
        id: String,
        identity: AnonymousIdentitySession
    ) async throws -> PrivateConversation {
        try await request(
            path: "/community/conversations/\(id)/accept",
            method: "POST",
            headers: identity.headers
        )
    }

    func privateMessages(
        conversationID: String,
        identity: AnonymousIdentitySession
    ) async throws -> [PrivateMessage] {
        try await request(
            path: "/community/conversations/\(conversationID)/messages",
            headers: identity.headers
        )
    }

    func sendPrivateMessage(
        conversationID: String,
        body: String,
        identity: AnonymousIdentitySession
    ) async throws -> PrivateMessage {
        try await send(
            path: "/community/conversations/\(conversationID)/messages",
            body: PrivateMessageCreate(body: body),
            identity: identity
        )
    }

    func blockIdentity(
        id: String,
        identity: AnonymousIdentitySession
    ) async throws -> CommunityBlock {
        try await send(
            path: "/community/blocks",
            body: CommunityBlockCreate(targetId: id),
            identity: identity
        )
    }

    func report(
        resourceType: String,
        resourceID: String,
        identity: AnonymousIdentitySession
    ) async throws -> CommunityReport {
        try await send(
            path: "/community/reports",
            body: CommunityReportCreate(
                resourceType: resourceType,
                resourceId: resourceID,
                reason: "內容可能包含不實、過時或不適合公開的資訊"
            ),
            identity: identity
        )
    }

    private func send<T: Decodable, Body: Encodable>(
        path: String,
        body: Body,
        identity: AnonymousIdentitySession? = nil
    ) async throws -> T {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        return try await request(
            path: path,
            method: "POST",
            body: try encoder.encode(body),
            headers: identity?.headers ?? [:]
        )
    }

    private func request<T: Decodable>(
        path: String,
        query: [String: String] = [:],
        method: String = "GET",
        body: Data? = nil,
        headers: [String: String] = [:]
    ) async throws -> T {
        guard var components = URLComponents(
            url: baseURL.appendingPathComponent(path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))),
            resolvingAgainstBaseURL: false
        ) else {
            throw ExchangeAPIError.invalidURL
        }
        components.queryItems = query
            .sorted { $0.key < $1.key }
            .map { URLQueryItem(name: $0.key, value: $0.value) }
        guard let url = components.url else {
            throw ExchangeAPIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if body != nil { request.setValue("application/json", forHTTPHeaderField: "Content-Type") }
        headers.forEach { request.setValue($0.value, forHTTPHeaderField: $0.key) }
        request.httpBody = body
        request.timeoutInterval = 30

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw ExchangeAPIError.invalidResponse
        }
        guard 200..<300 ~= http.statusCode else {
            throw ExchangeAPIError.server(status: http.statusCode)
        }
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw ExchangeAPIError.decoding(error)
        }
    }
}

private extension AnonymousIdentitySession {
    var headers: [String: String] {
        ["X-Anonymous-ID": id, "X-Anonymous-Token": accessToken]
    }
}
