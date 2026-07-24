import SwiftUI

private enum CommunityMode: String, CaseIterable, Identifiable {
    case posts, chat, messages

    var id: String { rawValue }
    var title: String {
        switch self {
        case .posts: "貼文"
        case .chat: "聊天室"
        case .messages: "私訊"
        }
    }
}

private struct InviteTarget: Identifiable {
    let id: String
    let name: String
}

@MainActor
final class ExchangeCommunityStore: ObservableObject {
    @Published private(set) var identity: AnonymousIdentitySession?
    @Published private(set) var posts: [CommunityPostThread] = []
    @Published private(set) var chat: [PublicChatMessage] = []
    @Published private(set) var conversations: [PrivateConversation] = []
    @Published private(set) var messages: [String: [PrivateMessage]] = [:]
    @Published private(set) var isLoading = false
    @Published var errorMessage: String?

    let schoolName: String
    private let api = ExchangeAPIClient.shared
    private let storageKey = "anonymousCommunityIdentity"

    init(schoolName: String) {
        self.schoolName = schoolName
        if let data = UserDefaults.standard.data(forKey: storageKey) {
            identity = try? JSONDecoder().decode(AnonymousIdentitySession.self, from: data)
        }
    }

    func load() async {
        if isLoading { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            let identity = try await ensureIdentity()
            async let loadedPosts = api.communityPosts(for: schoolName)
            async let loadedChat = api.publicChat(for: schoolName)
            async let loadedConversations = api.conversations(identity: identity)
            posts = try await loadedPosts
            chat = try await loadedChat
            conversations = try await loadedConversations
            var loadedMessages: [String: [PrivateMessage]] = [:]
            for conversation in conversations {
                loadedMessages[conversation.id] = try await api.privateMessages(
                    conversationID: conversation.id,
                    identity: identity
                )
            }
            messages = loadedMessages
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func publishPost(type: String, title: String, body: String) async -> Bool {
        do {
            let identity = try await ensureIdentity()
            let _: CommunityPost = try await api.publishPost(
                CommunityPostCreate(schoolName: schoolName, postType: type, title: title, body: body),
                identity: identity
            )
            await load()
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    func publishComment(postID: String, body: String) async {
        do {
            let identity = try await ensureIdentity()
            let _: CommunityPostComment = try await api.publishComment(
                postID: postID,
                body: body,
                identity: identity
            )
            await load()
        } catch { errorMessage = error.localizedDescription }
    }

    func publishChat(body: String) async -> Bool {
        do {
            let identity = try await ensureIdentity()
            let _: PublicChatMessage = try await api.publishChat(
                school: schoolName,
                body: body,
                identity: identity
            )
            await load()
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    func invite(recipientID: String, message: String) async -> Bool {
        do {
            let identity = try await ensureIdentity()
            let _: PrivateConversation = try await api.invite(
                school: schoolName,
                recipientID: recipientID,
                message: message,
                identity: identity
            )
            await load()
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    func accept(_ conversation: PrivateConversation) async {
        do {
            let identity = try await ensureIdentity()
            let _: PrivateConversation = try await api.acceptConversation(
                id: conversation.id,
                identity: identity
            )
            await load()
        } catch { errorMessage = error.localizedDescription }
    }

    func send(message: String, to conversation: PrivateConversation) async -> Bool {
        do {
            let identity = try await ensureIdentity()
            let _: PrivateMessage = try await api.sendPrivateMessage(
                conversationID: conversation.id,
                body: message,
                identity: identity
            )
            await load()
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    func report(resourceType: String, resourceID: String) async {
        do {
            let identity = try await ensureIdentity()
            let _: CommunityReport = try await api.report(
                resourceType: resourceType,
                resourceID: resourceID,
                identity: identity
            )
        } catch { errorMessage = error.localizedDescription }
    }

    func block(identityID: String) async {
        do {
            let identity = try await ensureIdentity()
            let _: CommunityBlock = try await api.blockIdentity(id: identityID, identity: identity)
            await load()
        } catch { errorMessage = error.localizedDescription }
    }

    private func ensureIdentity() async throws -> AnonymousIdentitySession {
        if let identity { return identity }
        let created = try await api.createAnonymousIdentity(
            displayName: "匿名同學 \(Int.random(in: 1000...9999))"
        )
        identity = created
        if let data = try? JSONEncoder().encode(created) {
            UserDefaults.standard.set(data, forKey: storageKey)
        }
        return created
    }
}

struct ExchangeCommunityView: View {
    @StateObject private var store: ExchangeCommunityStore
    @State private var mode: CommunityMode = .posts
    @State private var postType = "discussion"
    @State private var postTitle = ""
    @State private var postBody = ""
    @State private var chatBody = ""
    @State private var replies: [String: String] = [:]
    @State private var privateReplies: [String: String] = [:]
    @State private var inviteTarget: InviteTarget?

    init(schoolName: String) {
        _store = StateObject(wrappedValue: ExchangeCommunityStore(schoolName: schoolName))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.md) {
            ExchangeSectionHeader(
                eyebrow: "匿名公開交流",
                title: "學生社群",
                detail: "貼文與聊天室公開可見；私訊需先由對方接受邀請。"
            )

            if let identity = store.identity {
                Label(identity.displayName, systemImage: "shield.checkered")
                    .font(ExchangeTypography.subheadline)
                    .foregroundStyle(ExchangeColor.accent)
                    .frame(minHeight: ExchangeLayout.minimumTarget)
            }

            Picker("社群功能", selection: $mode) {
                ForEach(CommunityMode.allCases) { item in
                    Text(item.title).tag(item)
                }
            }
            .pickerStyle(.segmented)

            if store.isLoading && store.posts.isEmpty {
                ExchangeLoadingState(message: "正在載入學生社群")
            } else {
                switch mode {
                case .posts: posts
                case .chat: chat
                case .messages: messages
                }
            }

            if let error = store.errorMessage {
                ExchangeInlineBanner(title: "社群功能暫時無法使用", message: error, kind: .warning)
            }
        }
        .task { await store.load() }
        .refreshable { await store.load() }
        .sheet(item: $inviteTarget) { target in
            InviteSheet(target: target) { message in
                let sent = await store.invite(recipientID: target.id, message: message)
                if sent {
                    inviteTarget = nil
                    mode = .messages
                }
                return sent
            }
            .presentationDetents([.medium])
        }
    }

    private var posts: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.md) {
            DisclosureGroup {
                VStack(spacing: ExchangeSpacing.sm) {
                    Picker("貼文類型", selection: $postType) {
                        Text("討論").tag("discussion")
                        Text("提問").tag("question")
                        Text("經驗").tag("experience")
                    }
                    TextField("貼文標題", text: $postTitle)
                        .textFieldStyle(.roundedBorder)
                        .frame(minHeight: ExchangeLayout.fieldHeight)
                    TextField("具體說明年份、學期或情境", text: $postBody, axis: .vertical)
                        .lineLimit(4...8)
                        .textFieldStyle(.roundedBorder)
                    Button {
                        Task {
                            if await store.publishPost(type: postType, title: postTitle, body: postBody) {
                                postTitle = ""
                                postBody = ""
                            }
                        }
                    } label: {
                        Label("立即發布", systemImage: "paperplane.fill")
                    }
                    .exchangeProminentButtonStyle()
                    .disabled(postTitle.count < 4 || postBody.count < 10)
                }
                .padding(.top, ExchangeSpacing.sm)
            } label: {
                Label("發一篇匿名貼文", systemImage: "square.and.pencil")
                    .font(ExchangeTypography.headline)
            }
            .exchangeCard()

            if store.posts.isEmpty {
                ExchangeEmptyState(title: "還沒有公開貼文", message: "分享第一個問題或交換經驗。", symbol: "text.bubble")
            }

            ForEach(store.posts) { thread in
                VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
                    Text(thread.post.postType == "question" ? "提問" : thread.post.postType == "experience" ? "經驗" : "討論")
                        .font(ExchangeTypography.caption)
                        .foregroundStyle(ExchangeColor.accent)
                    Text(thread.post.title).font(ExchangeTypography.title3)
                    Text(thread.post.body)
                        .font(ExchangeTypography.body)
                        .foregroundStyle(ExchangeColor.labelSecondary)
                    HStack {
                        Text(thread.post.displayName).font(ExchangeTypography.caption)
                        Spacer()
                        if thread.post.authorId != store.identity?.id {
                            Button("邀請私訊", systemImage: "envelope.badge") {
                                inviteTarget = InviteTarget(id: thread.post.authorId, name: thread.post.displayName)
                            }
                            .buttonStyle(ExchangeSecondaryButtonStyle())
                        }
                        Button {
                            Task { await store.report(resourceType: "post", resourceID: thread.post.id) }
                        } label: {
                            Image(systemName: "flag")
                                .frame(width: 44, height: 44)
                        }
                        .accessibilityLabel("檢舉這篇貼文")
                    }
                    DisclosureGroup("\(thread.comments.count) 則回覆") {
                        VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
                            ForEach(thread.comments) { comment in
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(comment.displayName).font(ExchangeTypography.caption)
                                    Text(comment.body).font(ExchangeTypography.body)
                                }
                                Divider()
                            }
                            HStack {
                                TextField("補充具體資訊", text: Binding(
                                    get: { replies[thread.id, default: ""] },
                                    set: { replies[thread.id] = $0 }
                                ))
                                .textFieldStyle(.roundedBorder)
                                Button("回覆") {
                                    let body = replies[thread.id, default: ""]
                                    Task {
                                        await store.publishComment(postID: thread.id, body: body)
                                        replies[thread.id] = ""
                                    }
                                }
                                .buttonStyle(ExchangeSecondaryButtonStyle())
                                .disabled(replies[thread.id, default: ""].count < 2)
                            }
                        }
                        .padding(.top, ExchangeSpacing.xs)
                    }
                }
                .exchangeCard()
            }
        }
    }

    private var chat: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
            if store.chat.isEmpty {
                ExchangeEmptyState(title: "聊天室還沒有訊息", message: "先問問是否有人也在準備同一學期。", symbol: "message")
            }
            ForEach(store.chat.suffix(40)) { message in
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(message.displayName).font(ExchangeTypography.caption)
                        Spacer()
                        if message.authorId != store.identity?.id {
                            Button {
                                inviteTarget = InviteTarget(id: message.authorId, name: message.displayName)
                            } label: {
                                Image(systemName: "envelope.badge")
                                    .frame(width: 44, height: 44)
                            }
                            .accessibilityLabel("邀請 \(message.displayName) 私訊")
                        }
                        Button {
                            Task { await store.report(resourceType: "chat", resourceID: message.id) }
                        } label: {
                            Image(systemName: "flag")
                                .frame(width: 44, height: 44)
                        }
                        .accessibilityLabel("檢舉這則公開訊息")
                    }
                    Text(message.body).font(ExchangeTypography.body)
                }
                .padding(.vertical, ExchangeSpacing.xs)
                Divider()
            }
            HStack {
                TextField("公開詢問申請或生活問題", text: $chatBody)
                    .textFieldStyle(.roundedBorder)
                    .frame(minHeight: ExchangeLayout.fieldHeight)
                Button {
                    let body = chatBody
                    Task {
                        if await store.publishChat(body: body) { chatBody = "" }
                    }
                } label: {
                    Image(systemName: "paperplane.fill")
                        .frame(width: 44, height: 44)
                }
                .buttonStyle(ExchangeIconButtonStyle())
                .disabled(chatBody.count < 2)
                .accessibilityLabel("送出公開訊息")
            }
        }
        .exchangeCard()
    }

    private var messages: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.md) {
            if store.conversations.isEmpty {
                ExchangeEmptyState(title: "目前沒有私訊", message: "從貼文或聊天室發送邀請，對方接受後才能對話。", symbol: "envelope")
            }
            ForEach(store.conversations) { conversation in
                let isRecipient = conversation.recipientId == store.identity?.id
                let otherName = isRecipient ? conversation.senderName : conversation.recipientName
                DisclosureGroup {
                    VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
                        ForEach(store.messages[conversation.id] ?? []) { message in
                            Text("\(message.displayName)：\(message.body)")
                                .font(ExchangeTypography.body)
                                .frame(maxWidth: .infinity, alignment: message.authorId == store.identity?.id ? .trailing : .leading)
                        }
                        if conversation.status == "pending" && isRecipient {
                            Button("接受私訊邀請", systemImage: "checkmark") {
                                Task { await store.accept(conversation) }
                            }
                            .exchangeProminentButtonStyle()
                        } else if conversation.status == "accepted" {
                            HStack {
                                TextField("輸入私訊", text: Binding(
                                    get: { privateReplies[conversation.id, default: ""] },
                                    set: { privateReplies[conversation.id] = $0 }
                                ))
                                .textFieldStyle(.roundedBorder)
                                Button("傳送") {
                                    let body = privateReplies[conversation.id, default: ""]
                                    Task {
                                        if await store.send(message: body, to: conversation) {
                                            privateReplies[conversation.id] = ""
                                        }
                                    }
                                }
                                .buttonStyle(ExchangeSecondaryButtonStyle())
                                .disabled(privateReplies[conversation.id, default: ""].count < 2)
                            }
                        }
                        Button(role: .destructive) {
                            let otherID = isRecipient ? conversation.senderId : conversation.recipientId
                            Task { await store.block(identityID: otherID) }
                        } label: {
                            Label("封鎖", systemImage: "nosign")
                        }
                        .frame(minHeight: ExchangeLayout.minimumTarget)
                    }
                    .padding(.top, ExchangeSpacing.sm)
                } label: {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(otherName).font(ExchangeTypography.headline)
                        Text(conversation.status == "accepted" ? "私訊中" : isRecipient ? "等待你接受" : "等待對方接受")
                            .font(ExchangeTypography.caption)
                            .foregroundStyle(ExchangeColor.labelSecondary)
                    }
                }
                .exchangeCard()
            }
        }
    }
}

private struct InviteSheet: View {
    let target: InviteTarget
    let send: (String) async -> Bool
    @State private var message = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("先向 \(target.name) 說明想請教的事") {
                    TextField("對方接受後才能繼續私訊", text: $message, axis: .vertical)
                        .lineLimit(4...8)
                }
                Section {
                    Button("送出邀請", systemImage: "envelope.badge") {
                        Task { _ = await send(message) }
                    }
                    .disabled(message.count < 5)
                } footer: {
                    Text("請勿傳送 Email、電話、社群帳號或其他個資。")
                }
            }
            .navigationTitle("私訊邀請")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}
