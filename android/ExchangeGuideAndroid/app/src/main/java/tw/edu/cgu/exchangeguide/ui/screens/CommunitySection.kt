package tw.edu.cgu.exchangeguide.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Mail
import androidx.compose.material.icons.filled.Flag
import androidx.compose.material.icons.filled.Block
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.ChatBubble
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Public
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch
import tw.edu.cgu.exchangeguide.data.model.AnonymousIdentityCreate
import tw.edu.cgu.exchangeguide.data.model.AnonymousIdentitySession
import tw.edu.cgu.exchangeguide.data.model.CommunityCommentCreate
import tw.edu.cgu.exchangeguide.data.model.CommunityBlockCreate
import tw.edu.cgu.exchangeguide.data.model.CommunityReportCreate
import tw.edu.cgu.exchangeguide.data.model.CommunityPostCreate
import tw.edu.cgu.exchangeguide.data.model.CommunityPostThread
import tw.edu.cgu.exchangeguide.data.model.PrivateConversation
import tw.edu.cgu.exchangeguide.data.model.PrivateConversationCreate
import tw.edu.cgu.exchangeguide.data.model.PrivateMessage
import tw.edu.cgu.exchangeguide.data.model.PrivateMessageCreate
import tw.edu.cgu.exchangeguide.data.model.PublicChatMessage
import tw.edu.cgu.exchangeguide.data.model.PublicChatMessageCreate
import tw.edu.cgu.exchangeguide.data.network.ApiClient
import tw.edu.cgu.exchangeguide.data.network.ExchangeApi
import tw.edu.cgu.exchangeguide.ui.components.BannerKind
import tw.edu.cgu.exchangeguide.ui.components.ExchangeCard
import tw.edu.cgu.exchangeguide.ui.components.InlineBanner
import tw.edu.cgu.exchangeguide.ui.components.InfoSummaryGrid
import tw.edu.cgu.exchangeguide.ui.components.InfoSummaryItem
import tw.edu.cgu.exchangeguide.ui.components.LoadingState
import tw.edu.cgu.exchangeguide.ui.components.SectionHeader
import tw.edu.cgu.exchangeguide.ui.components.SnapshotMetric
import tw.edu.cgu.exchangeguide.ui.components.SnapshotMetricRail
import tw.edu.cgu.exchangeguide.ui.theme.ExchangeSpacing

private class CommunityController(
    private val schoolName: String,
    private val api: ExchangeApi,
) {
    var identity by mutableStateOf<AnonymousIdentitySession?>(null)
    var posts by mutableStateOf<List<CommunityPostThread>>(emptyList())
    var chat by mutableStateOf<List<PublicChatMessage>>(emptyList())
    var conversations by mutableStateOf<List<PrivateConversation>>(emptyList())
    var messages by mutableStateOf<Map<String, List<PrivateMessage>>>(emptyMap())
    var isLoading by mutableStateOf(false)
    var errorMessage by mutableStateOf<String?>(null)

    suspend fun load() {
        if (isLoading) return
        isLoading = true
        errorMessage = null
        runCatching {
            val activeIdentity = identity ?: api.createIdentity(
                AnonymousIdentityCreate("匿名同學 ${(1000..9999).random()}"),
            ).also { identity = it }
            coroutineScope {
                val loadedPosts = async { api.getCommunityPosts(schoolName) }
                val loadedChat = async { api.getPublicChat(schoolName) }
                val loadedConversations = async {
                    api.getConversations(activeIdentity.id, activeIdentity.accessToken)
                }
                posts = loadedPosts.await()
                chat = loadedChat.await()
                conversations = loadedConversations.await()
            }
            messages = conversations.associate { conversation ->
                conversation.id to api.getPrivateMessages(
                    conversation.id,
                    activeIdentity.id,
                    activeIdentity.accessToken,
                )
            }
        }.onFailure { errorMessage = it.localizedMessage ?: "社群暫時無法載入" }
        isLoading = false
    }

    suspend fun publishPost(type: String, title: String, body: String) = withIdentity { identity ->
        api.publishPost(
            identity.id,
            identity.accessToken,
            CommunityPostCreate(schoolName, type, title, body),
        )
        load()
    }

    suspend fun comment(postId: String, body: String) = withIdentity { identity ->
        api.publishComment(postId, identity.id, identity.accessToken, CommunityCommentCreate(body))
        load()
    }

    suspend fun publishChat(body: String) = withIdentity { identity ->
        api.publishChat(
            identity.id,
            identity.accessToken,
            PublicChatMessageCreate(schoolName, body),
        )
        load()
    }

    suspend fun invite(recipientId: String, message: String) = withIdentity { identity ->
        api.inviteConversation(
            identity.id,
            identity.accessToken,
            PrivateConversationCreate(schoolName, recipientId, message),
        )
        load()
    }

    suspend fun accept(conversationId: String) = withIdentity { identity ->
        api.acceptConversation(conversationId, identity.id, identity.accessToken)
        load()
    }

    suspend fun send(conversationId: String, body: String) = withIdentity { identity ->
        api.sendPrivateMessage(
            conversationId,
            identity.id,
            identity.accessToken,
            PrivateMessageCreate(body),
        )
        load()
    }

    suspend fun report(resourceType: String, resourceId: String) = withIdentity { identity ->
        api.reportContent(
            identity.id,
            identity.accessToken,
            CommunityReportCreate(
                resourceType,
                resourceId,
                "內容可能包含不實、過時或不適合公開的資訊",
            ),
        )
    }

    suspend fun block(targetId: String) = withIdentity { identity ->
        api.blockIdentity(identity.id, identity.accessToken, CommunityBlockCreate(targetId))
        load()
    }

    private suspend fun withIdentity(block: suspend (AnonymousIdentitySession) -> Unit) {
        val activeIdentity = identity ?: return
        runCatching { block(activeIdentity) }
            .onFailure { errorMessage = it.localizedMessage ?: "操作失敗" }
    }
}

private data class CommunityInviteTarget(val id: String, val name: String)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CommunitySection(schoolName: String) {
    val controller = remember(schoolName) { CommunityController(schoolName, ApiClient.api) }
    val scope = rememberCoroutineScope()
    var mode by remember(schoolName) { mutableStateOf(0) }
    var postType by remember { mutableStateOf("discussion") }
    var postTitle by remember { mutableStateOf("") }
    var postBody by remember { mutableStateOf("") }
    var chatBody by remember { mutableStateOf("") }
    val comments = remember { mutableStateMapOf<String, String>() }
    val privateReplies = remember { mutableStateMapOf<String, String>() }
    var inviteTarget by remember { mutableStateOf<CommunityInviteTarget?>(null) }
    var inviteMessage by remember { mutableStateOf("") }

    LaunchedEffect(schoolName) { controller.load() }

    SectionHeader(
        eyebrow = "匿名公開交流",
        title = "學生社群",
        detail = "貼文與聊天室公開可見；私訊必須先由對方接受邀請。",
    )
    controller.identity?.let {
        InlineBanner("你的匿名代號", it.displayName, BannerKind.Info)
    }
    SnapshotMetricRail(
        listOf(
            SnapshotMetric(controller.posts.size.toString(), "貼文", MaterialTheme.colorScheme.primary),
            SnapshotMetric(controller.posts.sumOf { it.comments.size }.toString(), "回覆", MaterialTheme.colorScheme.secondary),
            SnapshotMetric(controller.chat.size.toString(), "公開訊息", Color(0xFF2E8B62)),
            SnapshotMetric(controller.conversations.size.toString(), "私訊", Color(0xFFC98A3D)),
        ),
    )
    SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
        listOf("貼文", "聊天室", "私訊").forEachIndexed { index, label ->
            SegmentedButton(
                selected = mode == index,
                onClick = { mode = index },
                shape = SegmentedButtonDefaults.itemShape(index, 3),
                label = { Text(label) },
            )
        }
    }
    if (controller.isLoading && controller.posts.isEmpty()) {
        LoadingState("正在載入學生社群")
    } else {
        when (mode) {
            0 -> PostsPane(
                controller = controller,
                postType = postType,
                onPostType = { postType = it },
                title = postTitle,
                onTitle = { postTitle = it },
                body = postBody,
                onBody = { postBody = it },
                comments = comments,
                onInvite = { id, name -> inviteTarget = CommunityInviteTarget(id, name) },
                onReport = { id -> scope.launch { controller.report("post", id) } },
                onPublish = {
                    scope.launch {
                        controller.publishPost(postType, postTitle, postBody)
                        postTitle = ""
                        postBody = ""
                    }
                },
                onComment = { postId ->
                    val body = comments[postId].orEmpty()
                    scope.launch {
                        controller.comment(postId, body)
                        comments[postId] = ""
                    }
                },
            )
            1 -> ChatPane(
                controller,
                chatBody,
                { chatBody = it },
                { id, name -> inviteTarget = CommunityInviteTarget(id, name) },
                { id -> scope.launch { controller.report("chat", id) } },
            ) {
                scope.launch {
                    controller.publishChat(chatBody)
                    chatBody = ""
                }
            }
            else -> MessagesPane(controller, privateReplies, scope)
        }
    }
    controller.errorMessage?.let { InlineBanner("社群功能暫時無法使用", it, BannerKind.Warning) }

    inviteTarget?.let { target ->
        ModalBottomSheet(onDismissRequest = { inviteTarget = null }) {
            Column(
                Modifier.fillMaxWidth().heightIn(min = 280.dp),
                verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.md),
            ) {
                Column(
                    Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm),
                ) {
                    Text("私訊邀請給 ${target.name}", style = MaterialTheme.typography.titleLarge)
                    Text("先說明想請教的事情，對方接受後才能繼續私訊。", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    OutlinedTextField(
                        value = inviteMessage,
                        onValueChange = { inviteMessage = it },
                        modifier = Modifier.fillMaxWidth().heightIn(min = 112.dp),
                        label = { Text("邀請訊息") },
                    )
                    Button(
                        onClick = {
                            scope.launch {
                                controller.invite(target.id, inviteMessage)
                                inviteMessage = ""
                                inviteTarget = null
                                mode = 2
                            }
                        },
                        enabled = inviteMessage.length >= 5,
                        modifier = Modifier.fillMaxWidth().heightIn(min = ExchangeSpacing.minimumTarget),
                    ) { Icon(Icons.Default.Mail, contentDescription = null); Text("送出邀請") }
                }
            }
        }
    }
}

@Composable
private fun PostsPane(
    controller: CommunityController,
    postType: String,
    onPostType: (String) -> Unit,
    title: String,
    onTitle: (String) -> Unit,
    body: String,
    onBody: (String) -> Unit,
    comments: MutableMap<String, String>,
    onInvite: (String, String) -> Unit,
    onReport: (String) -> Unit,
    onPublish: () -> Unit,
    onComment: (String) -> Unit,
) {
    ExchangeCard {
        Text("發一篇匿名貼文", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        Row(horizontalArrangement = Arrangement.spacedBy(ExchangeSpacing.xs)) {
            listOf("discussion" to "討論", "question" to "提問", "experience" to "經驗").forEach { (value, label) ->
                FilterChip(selected = postType == value, onClick = { onPostType(value) }, label = { Text(label) })
            }
        }
        OutlinedTextField(title, onTitle, Modifier.fillMaxWidth(), label = { Text("標題") })
        OutlinedTextField(body, onBody, Modifier.fillMaxWidth().heightIn(min = 120.dp), label = { Text("具體內容") })
        Button(onClick = onPublish, enabled = title.length >= 4 && body.length >= 10, modifier = Modifier.fillMaxWidth()) {
            Icon(Icons.Default.Send, contentDescription = null); Text("立即發布")
        }
    }
    if (controller.posts.isEmpty()) InlineBanner("還沒有公開貼文", "分享第一個申請問題或交換經驗。", BannerKind.Info)
    controller.posts.forEach { thread ->
        val typeLabel = when (thread.post.postType) {
            "question" -> "提問"
            "experience" -> "經驗"
            else -> "討論"
        }
        var bodyExpanded by remember(thread.post.id) { mutableStateOf(false) }
        var repliesExpanded by remember("replies-${thread.post.id}") { mutableStateOf(false) }
        ExchangeCard {
            Text(typeLabel, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
            Text(thread.post.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text(
                    "${thread.post.displayName} · ${communityDate(thread.post.createdAt)}",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.weight(1f),
                )
                if (thread.post.authorId != controller.identity?.id) {
                    Button(onClick = { onInvite(thread.post.authorId, thread.post.displayName) }) { Text("邀請") }
                }
                IconButton(onClick = { onReport(thread.post.id) }) {
                    Icon(Icons.Default.Flag, contentDescription = "檢舉這篇貼文")
                }
            }
            InfoSummaryGrid(
                listOf(
                    InfoSummaryItem("內容類型", typeLabel, Icons.Default.Description, MaterialTheme.colorScheme.primary),
                    InfoSummaryItem("回覆", "${thread.comments.size} 則", Icons.Default.ChatBubble, MaterialTheme.colorScheme.secondary),
                    InfoSummaryItem("發布日期", communityDate(thread.post.createdAt), Icons.Default.CalendarMonth, Color(0xFFC98A3D)),
                    InfoSummaryItem("可見範圍", "公開", Icons.Default.Public, Color(0xFF2E8B62)),
                ),
            )
            Text(
                text = thread.post.body,
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = if (bodyExpanded) Int.MAX_VALUE else 4,
                overflow = TextOverflow.Ellipsis,
            )
            if (thread.post.body.length > 120) {
                Text(
                    text = if (bodyExpanded) "收合全文" else "閱讀全文",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.clickable(role = Role.Button) { bodyExpanded = !bodyExpanded },
                )
            }
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text("${thread.comments.size} 則回覆", style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1f))
                IconButton(onClick = { repliesExpanded = !repliesExpanded }) {
                    Icon(
                        if (repliesExpanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                        contentDescription = if (repliesExpanded) "收合回覆" else "展開回覆",
                    )
                }
            }
            androidx.compose.animation.AnimatedVisibility(repliesExpanded) {
                Column(verticalArrangement = Arrangement.spacedBy(ExchangeSpacing.sm)) {
                    thread.comments.forEach { comment ->
                        Text("${comment.displayName}：${comment.body}", style = MaterialTheme.typography.bodyMedium)
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        OutlinedTextField(
                            value = comments[thread.post.id].orEmpty(),
                            onValueChange = { comments[thread.post.id] = it },
                            modifier = Modifier.weight(1f),
                            label = { Text("回覆") },
                        )
                        IconButton(onClick = { onComment(thread.post.id) }, enabled = comments[thread.post.id].orEmpty().length >= 2) {
                            Icon(Icons.Default.Send, contentDescription = "送出回覆")
                        }
                    }
                }
            }
        }
    }
}

private fun communityDate(value: String): String = value.take(10).replace('-', '.')

@Composable
private fun ChatPane(
    controller: CommunityController,
    body: String,
    onBody: (String) -> Unit,
    onInvite: (String, String) -> Unit,
    onReport: (String) -> Unit,
    onSend: () -> Unit,
) {
    ExchangeCard {
        if (controller.chat.isEmpty()) Text("聊天室還沒有訊息，先問問是否有人也在準備同一學期。")
        controller.chat.takeLast(40).forEach { message ->
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(message.displayName, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                    Text(message.body, style = MaterialTheme.typography.bodyLarge)
                }
                if (message.authorId != controller.identity?.id) {
                    IconButton(onClick = { onInvite(message.authorId, message.displayName) }) {
                        Icon(Icons.Default.Mail, contentDescription = "邀請 ${message.displayName} 私訊")
                    }
                }
                IconButton(onClick = { onReport(message.id) }) {
                    Icon(Icons.Default.Flag, contentDescription = "檢舉這則公開訊息")
                }
            }
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(body, onBody, Modifier.weight(1f), label = { Text("公開訊息") })
            IconButton(onClick = onSend, enabled = body.length >= 2) { Icon(Icons.Default.Send, contentDescription = "送出公開訊息") }
        }
    }
}

@Composable
private fun MessagesPane(
    controller: CommunityController,
    replies: MutableMap<String, String>,
    scope: kotlinx.coroutines.CoroutineScope,
) {
    if (controller.conversations.isEmpty()) InlineBanner("目前沒有私訊", "從貼文或聊天室邀請對方，接受後才能對話。", BannerKind.Info)
    controller.conversations.forEach { conversation ->
        val recipient = conversation.recipientId == controller.identity?.id
        val otherName = if (recipient) conversation.senderName else conversation.recipientName
        ExchangeCard {
            Text(otherName, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Text(
                if (conversation.status == "accepted") "私訊中" else if (recipient) "等待你接受邀請" else "等待對方接受",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.primary,
            )
            controller.messages[conversation.id].orEmpty().forEach { message ->
                Text("${message.displayName}：${message.body}", style = MaterialTheme.typography.bodyLarge)
            }
            if (conversation.status == "pending" && recipient) {
                Button(onClick = { scope.launch { controller.accept(conversation.id) } }, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.Check, contentDescription = null); Text("接受私訊邀請")
                }
            } else if (conversation.status == "accepted") {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    OutlinedTextField(
                        value = replies[conversation.id].orEmpty(),
                        onValueChange = { replies[conversation.id] = it },
                        modifier = Modifier.weight(1f),
                        label = { Text("私訊") },
                    )
                    IconButton(
                        onClick = {
                            val body = replies[conversation.id].orEmpty()
                            scope.launch {
                                controller.send(conversation.id, body)
                                replies[conversation.id] = ""
                            }
                        },
                        enabled = replies[conversation.id].orEmpty().length >= 2,
                    ) { Icon(Icons.Default.Send, contentDescription = "傳送私訊") }
                }
            }
            Button(
                onClick = {
                    val otherId = if (recipient) conversation.senderId else conversation.recipientId
                    scope.launch { controller.block(otherId) }
                },
                modifier = Modifier.heightIn(min = ExchangeSpacing.minimumTarget),
            ) {
                Icon(Icons.Default.Block, contentDescription = null)
                Text("封鎖")
            }
        }
    }
}
