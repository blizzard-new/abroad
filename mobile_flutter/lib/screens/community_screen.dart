import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import 'account_screen.dart';

enum CommunityMode { posts, chat, messages }

class CommunityScreen extends StatefulWidget {
  const CommunityScreen({
    super.key,
    this.embedded = false,
    this.initialSchool,
    this.lockedToInitialSchool = false,
  });

  final bool embedded;
  final String? initialSchool;
  final bool lockedToInitialSchool;

  @override
  State<CommunityScreen> createState() => _CommunityScreenState();
}

class _CommunityScreenState extends State<CommunityScreen> {
  CommunityMode mode = CommunityMode.posts;
  AnonymousIdentity? identity;
  List<CommunityThread> posts = const [];
  List<ChatMessage> chat = const [];
  List<PrivateConversation> conversations = const [];
  String? schoolName;
  String? error;
  bool loading = true;
  bool initialized = false;
  final chatController = TextEditingController();

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final store = ExchangeStoreScope.of(context);
    if (widget.lockedToInitialSchool) {
      final targetSchool =
          (widget.initialSchool == null ||
              widget.initialSchool == defaultHomeUniversity)
          ? store.selectedUniversity
          : widget.initialSchool!;
      if (!initialized || schoolName != targetSchool) {
        initialized = true;
        schoolName = targetSchool;
        Future<void>.microtask(_loadAll);
      }
      return;
    }
    if (initialized) return;
    initialized = true;
    schoolName =
        widget.initialSchool ??
        (store.dashboard?.partnerUniversities.isNotEmpty == true
            ? store.dashboard!.partnerUniversities.first.schoolName
            : '林肯大學 Lincoln University');
    Future<void>.microtask(_loadAll);
  }

  @override
  void dispose() {
    chatController.dispose();
    super.dispose();
  }

  Future<void> _loadAll() async {
    if (!mounted) return;
    setState(() {
      loading = true;
      error = null;
    });
    final store = ExchangeStoreScope.of(context);
    try {
      final session = store.account == null
          ? null
          : await store.ensureIdentity();
      final results = await Future.wait<dynamic>([
        store.api.posts(schoolName: schoolName!),
        store.api.chat(schoolName!, homeSchool: store.selectedUniversity),
        if (session != null) store.api.conversations(session),
      ]);
      if (!mounted) return;
      setState(() {
        identity = session;
        posts = results[0] as List<CommunityThread>;
        chat = results[1] as List<ChatMessage>;
        conversations = session == null
            ? const []
            : results[2] as List<PrivateConversation>;
      });
    } catch (exception) {
      if (mounted) setState(() => error = exception.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> _selectSchool(String? value) async {
    if (widget.lockedToInitialSchool) return;
    if (value == null || value == schoolName) return;
    setState(() => schoolName = value);
    await _loadAll();
  }

  @override
  Widget build(BuildContext context) {
    final content = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!widget.embedded && !widget.lockedToInitialSchool) ...[
          const StudentSectionTitle('學生社群', icon: Icons.forum_outlined),
          const SizedBox(height: 8),
          Text(
            '公開討論；私訊需先接受邀請。',
            style: Theme.of(
              context,
            ).textTheme.bodyLarge?.copyWith(color: ExchangeColors.secondaryInk),
          ),
          const SizedBox(height: 16),
          _SchoolSelector(value: schoolName, onChanged: _selectSchool),
          const SizedBox(height: 16),
        ] else if (widget.embedded) ...[
          const StudentSectionTitle('學生社群', icon: Icons.forum_outlined),
          const SizedBox(height: 8),
          Text(
            '私訊需先接受邀請，可封鎖或檢舉。',
            style: Theme.of(
              context,
            ).textTheme.bodyLarge?.copyWith(color: ExchangeColors.secondaryInk),
          ),
          const SizedBox(height: 16),
        ],
        if (identity != null) _IdentityCard(identity: identity!),
        const SizedBox(height: 16),
        _ModeSelector(
          selected: mode,
          onSelected: (value) => setState(() => mode = value),
        ),
        const SizedBox(height: 16),
        if (loading)
          const LoadingCards(count: 3)
        else if (error != null)
          InlineError(message: error!, onRetry: _loadAll)
        else if (identity == null)
          _AccountRequiredPanel(posts: posts, chat: chat, onSignedIn: _loadAll)
        else
          switch (mode) {
            CommunityMode.posts => _PostsPanel(
              posts: posts,
              identity: identity!,
              schoolName: schoolName!,
              onRefresh: _loadAll,
            ),
            CommunityMode.chat => _ChatPanel(
              messages: chat,
              identity: identity!,
              schoolName: schoolName!,
              controller: chatController,
              onRefresh: _loadAll,
            ),
            CommunityMode.messages => _MessagesPanel(
              conversations: conversations,
              identity: identity!,
              schoolName: schoolName!,
              onRefresh: _loadAll,
            ),
          },
      ],
    );

    if (widget.embedded) return content;
    return SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: _loadAll,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 110),
          children: [content],
        ),
      ),
    );
  }
}

class _AccountRequiredPanel extends StatelessWidget {
  const _AccountRequiredPanel({
    required this.posts,
    required this.chat,
    required this.onSignedIn,
  });

  final List<CommunityThread> posts;
  final List<ChatMessage> chat;
  final Future<void> Function() onSignedIn;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        GlassCard(
          tint: ExchangeColors.blueSoft.withValues(alpha: .65),
          child: Column(
            children: [
              const ExchangeIconBadge(
                Icons.lock_person_outlined,
                color: ExchangeColors.blue,
                background: ExchangeColors.blueSoft,
              ),
              const SizedBox(height: 12),
              Text('登入後參與校別社群', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text(
                '${posts.length} 篇討論 · ${chat.length} 則訊息\n登入後可發文、聊天與私訊。',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => ExchangePageBackground(
                        child: Scaffold(body: const AccountScreen()),
                      ),
                    ),
                  );
                  await onSignedIn();
                },
                icon: const Icon(Icons.login_rounded),
                label: const Text('登入參與'),
              ),
            ],
          ),
        ),
        if (posts.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text('公開討論預覽', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          ...posts
              .take(3)
              .map(
                (thread) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.forum_outlined),
                  title: Text(thread.post.title),
                  subtitle: Text(
                    thread.post.body,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ),
        ],
      ],
    );
  }
}

class _SchoolSelector extends StatelessWidget {
  const _SchoolSelector({required this.value, required this.onChanged});

  final String? value;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    final partners =
        ExchangeStoreScope.of(context).dashboard?.partnerUniversities ??
        const [];
    final names = partners.map((item) => item.schoolName).toSet().toList();
    if (value != null && !names.contains(value)) names.insert(0, value!);
    return DropdownButtonFormField<String>(
      initialValue: value,
      isExpanded: true,
      decoration: const InputDecoration(
        labelText: '討論哪一間學校',
        prefixIcon: Icon(Icons.school_outlined),
      ),
      items: names
          .map(
            (name) => DropdownMenuItem(
              value: name,
              child: Text(name, maxLines: 1, overflow: TextOverflow.ellipsis),
            ),
          )
          .toList(),
      onChanged: onChanged,
    );
  }
}

class _IdentityCard extends StatelessWidget {
  const _IdentityCard({required this.identity});

  final AnonymousIdentity identity;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      tint: ExchangeColors.blueSoft.withValues(alpha: .72),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const ExchangeIconBadge(
            Icons.shield_outlined,
            color: ExchangeColors.blue,
            background: ExchangeColors.blueSoft,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  identity.displayName,
                  style: Theme.of(
                    context,
                  ).textTheme.titleMedium?.copyWith(color: ExchangeColors.blue),
                ),
                const SizedBox(height: 4),
                Text(
                  '匿名代號只儲存在這個裝置；請勿張貼聯絡方式或個資。',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: SelectableText(
                        '匿名 ID：${identity.id}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: ExchangeColors.ink,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    IconButton(
                      tooltip: '複製匿名 ID',
                      constraints: const BoxConstraints(
                        minWidth: 44,
                        minHeight: 44,
                      ),
                      onPressed: () async {
                        await Clipboard.setData(
                          ClipboardData(text: identity.id),
                        );
                        if (context.mounted) _notice(context, '已複製匿名 ID');
                      },
                      icon: const Icon(Icons.copy_rounded, size: 20),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ModeSelector extends StatelessWidget {
  const _ModeSelector({required this.selected, required this.onSelected});
  final CommunityMode selected;
  final ValueChanged<CommunityMode> onSelected;
  @override
  Widget build(BuildContext context) {
    const modes = <CommunityMode, (IconData, String)>{
      CommunityMode.posts: (Icons.dynamic_feed_outlined, '貼文'),
      CommunityMode.chat: (Icons.forum_outlined, '聊天'),
      CommunityMode.messages: (Icons.mail_outline_rounded, '私訊'),
    };
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: modes.entries
          .map(
            (entry) => ChoiceChip(
              avatar: Icon(entry.value.$1, size: 20),
              label: Text(entry.value.$2),
              selected: selected == entry.key,
              onSelected: (_) => onSelected(entry.key),
            ),
          )
          .toList(),
    );
  }
}

class _PostsPanel extends StatelessWidget {
  const _PostsPanel({
    required this.posts,
    required this.identity,
    required this.schoolName,
    required this.onRefresh,
  });

  final List<CommunityThread> posts;
  final AnonymousIdentity identity;
  final String schoolName;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final api = ExchangeStoreScope.of(context).api;
    return Column(
      children: [
        GlassCard(
          onTap: () => _showPostComposer(
            context: context,
            identity: identity,
            schoolName: schoolName,
            onSubmitted: onRefresh,
          ),
          child: Row(
            children: [
              const ExchangeIconBadge(Icons.edit_note_rounded),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '發一篇匿名貼文',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    Text(
                      '提問、討論或分享交換經驗',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded),
            ],
          ),
        ),
        const SizedBox(height: 12),
        if (posts.isEmpty)
          const EmptyState(
            icon: Icons.chat_bubble_outline_rounded,
            title: '還沒有公開貼文',
            message: '分享申請問題、住宿資訊或實際交換經驗，其他學生就能一起補充。',
          )
        else
          ...posts.map(
            (thread) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const CircleAvatar(
                          radius: 20,
                          backgroundColor: ExchangeColors.tealSoft,
                          child: Icon(
                            Icons.person_outline_rounded,
                            color: ExchangeColors.teal,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                thread.post.displayName,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              Text(
                                _shortTime(thread.post.createdAt),
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ],
                          ),
                        ),
                        PopupMenuButton<String>(
                          tooltip: '貼文操作',
                          onSelected: (value) async {
                            if (value == 'message') {
                              await _showInviteComposer(
                                context: context,
                                identity: identity,
                                schoolName: schoolName,
                                recipientId: thread.post.authorId,
                                onSubmitted: onRefresh,
                              );
                            } else if (value == 'report') {
                              await api.report(
                                identity: identity,
                                resourceType: 'post',
                                resourceId: thread.post.id,
                                reason: '內容需要管理員檢查',
                              );
                              if (context.mounted) _notice(context, '已送出檢舉');
                            } else if (value == 'block') {
                              await api.blockIdentity(
                                identity: identity,
                                targetId: thread.post.authorId,
                              );
                              if (context.mounted) {
                                _notice(context, '已封鎖這位匿名使用者');
                                await onRefresh();
                              }
                            }
                          },
                          itemBuilder: (_) => const [
                            PopupMenuItem(
                              value: 'message',
                              child: Text('傳送私訊邀請'),
                            ),
                            PopupMenuItem(value: 'report', child: Text('檢舉內容')),
                            PopupMenuItem(value: 'block', child: Text('封鎖使用者')),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Text(
                      thread.post.title,
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    Text(thread.post.body),
                    const Divider(height: 24),
                    ExpansionTile(
                      tilePadding: EdgeInsets.zero,
                      childrenPadding: EdgeInsets.zero,
                      shape: const Border(),
                      collapsedShape: const Border(),
                      title: Text('${thread.comments.length} 則留言'),
                      trailing: const Icon(Icons.expand_more_rounded),
                      children: [
                        ...thread.comments.map(
                          (comment) => ListTile(
                            contentPadding: EdgeInsets.zero,
                            leading: const CircleAvatar(
                              radius: 16,
                              backgroundColor: ExchangeColors.blueSoft,
                              child: Icon(
                                Icons.person_outline_rounded,
                                size: 17,
                                color: ExchangeColors.blue,
                              ),
                            ),
                            title: Text(
                              comment.displayName,
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                                fontSize: 12,
                              ),
                            ),
                            subtitle: Text(comment.body),
                          ),
                        ),
                        Align(
                          alignment: Alignment.centerLeft,
                          child: TextButton.icon(
                            onPressed: () => _showCommentComposer(
                              context: context,
                              identity: identity,
                              postId: thread.post.id,
                              onSubmitted: onRefresh,
                            ),
                            icon: const Icon(Icons.reply_rounded),
                            label: const Text('加入留言'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _ChatPanel extends StatelessWidget {
  const _ChatPanel({
    required this.messages,
    required this.identity,
    required this.schoolName,
    required this.controller,
    required this.onRefresh,
  });

  final List<ChatMessage> messages;
  final AnonymousIdentity identity;
  final String schoolName;
  final TextEditingController controller;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        if (messages.isEmpty)
          const EmptyState(
            icon: Icons.forum_outlined,
            title: '聊天室還沒有訊息',
            message: '這裡是所有人都看得到的匿名聊天室，請不要留下聯絡方式。',
          )
        else
          ...messages.map((message) {
            final mine = message.authorId == identity.id;
            return Align(
              alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
              child: Container(
                constraints: const BoxConstraints(maxWidth: 310),
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 12,
                ),
                decoration: BoxDecoration(
                  color: mine
                      ? ExchangeColors.teal
                      : ExchangeColors.surfaceMuted,
                  borderRadius: BorderRadius.only(
                    topLeft: const Radius.circular(16),
                    topRight: const Radius.circular(16),
                    bottomLeft: Radius.circular(mine ? 16 : 4),
                    bottomRight: Radius.circular(mine ? 4 : 16),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      message.displayName,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: mine
                            ? Colors.white70
                            : ExchangeColors.secondaryInk,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      message.body,
                      style: TextStyle(
                        color: mine ? Colors.white : ExchangeColors.ink,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }),
        const SizedBox(height: 12),
        GlassCard(
          padding: const EdgeInsets.all(10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: TextField(
                  controller: controller,
                  minLines: 1,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    hintText: '傳送公開訊息',
                    border: InputBorder.none,
                    enabledBorder: InputBorder.none,
                    focusedBorder: InputBorder.none,
                    filled: false,
                  ),
                ),
              ),
              IconButton.filled(
                tooltip: '送出訊息',
                constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
                onPressed: () async {
                  final body = controller.text.trim();
                  if (body.isEmpty) return;
                  try {
                    final store = ExchangeStoreScope.of(context, listen: false);
                    await store.api.publishChat(
                      identity: identity,
                      schoolName: schoolName,
                      body: body,
                      homeSchool: store.selectedUniversity,
                    );
                    controller.clear();
                    await onRefresh();
                  } catch (exception) {
                    if (context.mounted) _notice(context, exception.toString());
                  }
                },
                icon: const Icon(Icons.arrow_upward_rounded),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _MessagesPanel extends StatelessWidget {
  const _MessagesPanel({
    required this.conversations,
    required this.identity,
    required this.schoolName,
    required this.onRefresh,
  });

  final List<PrivateConversation> conversations;
  final AnonymousIdentity identity;
  final String schoolName;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        GlassCard(
          onTap: () => _showInviteComposer(
            context: context,
            identity: identity,
            schoolName: schoolName,
            onSubmitted: onRefresh,
          ),
          child: Row(
            children: [
              const ExchangeIconBadge(Icons.person_add_alt_1_rounded),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '傳送私訊邀請',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    Text(
                      '對方接受後才能繼續對話',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded),
            ],
          ),
        ),
        const SizedBox(height: 12),
        if (conversations.isEmpty)
          const EmptyState(
            icon: Icons.mark_email_unread_outlined,
            title: '尚無私訊',
            message: '可以輸入其他匿名同學的代號傳送邀請；對方接受前不能持續傳訊。',
          )
        else
          ...conversations.map(
            (conversation) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: GlassCard(
                onTap: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => ConversationScreen(
                        conversation: conversation,
                        identity: identity,
                      ),
                    ),
                  );
                  await onRefresh();
                },
                child: Row(
                  children: [
                    const ExchangeIconBadge(Icons.person_outline_rounded),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            conversation.otherName(identity.id),
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          Text(
                            conversation.status == 'accepted'
                                ? '已接受 · 可以傳送訊息'
                                : '等待接受邀請',
                            style: Theme.of(context).textTheme.bodySmall
                                ?.copyWith(
                                  color: conversation.status == 'accepted'
                                      ? ExchangeColors.success
                                      : ExchangeColors.amber,
                                ),
                          ),
                        ],
                      ),
                    ),
                    const Icon(Icons.chevron_right_rounded),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class ConversationScreen extends StatefulWidget {
  const ConversationScreen({
    required this.conversation,
    required this.identity,
    super.key,
  });

  final PrivateConversation conversation;
  final AnonymousIdentity identity;

  @override
  State<ConversationScreen> createState() => _ConversationScreenState();
}

class _ConversationScreenState extends State<ConversationScreen> {
  final controller = TextEditingController();
  List<PrivateMessage> messages = const [];
  bool loading = true;
  bool initialized = false;
  String? error;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!initialized) {
      initialized = true;
      Future<void>.microtask(_load);
    }
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final data = await ExchangeStoreScope.of(context).api.privateMessages(
        identity: widget.identity,
        conversationId: widget.conversation.id,
      );
      if (mounted) setState(() => messages = data);
    } catch (exception) {
      if (mounted) setState(() => error = exception.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final conversation = widget.conversation;
    final incomingPending =
        conversation.status != 'accepted' &&
        conversation.recipientId == widget.identity.id;
    return ExchangePageBackground(
      child: Scaffold(
        appBar: AppBar(
          title: Text(conversation.otherName(widget.identity.id)),
          backgroundColor: Colors.transparent,
          actions: [
            PopupMenuButton<String>(
              tooltip: '私訊設定',
              onSelected: (value) async {
                final api = ExchangeStoreScope.of(context).api;
                if (value == 'block') {
                  final target = conversation.senderId == widget.identity.id
                      ? conversation.recipientId
                      : conversation.senderId;
                  await api.blockIdentity(
                    identity: widget.identity,
                    targetId: target,
                  );
                  if (context.mounted) Navigator.of(context).pop();
                } else {
                  await api.report(
                    identity: widget.identity,
                    resourceType: 'conversation',
                    resourceId: conversation.id,
                    reason: '私訊內容需要管理員檢查',
                  );
                  if (context.mounted) _notice(context, '已送出檢舉');
                }
              },
              itemBuilder: (_) => const [
                PopupMenuItem(value: 'report', child: Text('檢舉對話')),
                PopupMenuItem(value: 'block', child: Text('封鎖使用者')),
              ],
            ),
          ],
        ),
        body: SafeArea(
          top: false,
          child: Column(
            children: [
              if (incomingPending)
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                  child: GlassCard(
                    tint: ExchangeColors.amberSoft.withValues(alpha: .84),
                    child: Column(
                      children: [
                        const Text('對方邀請你開始私訊。接受後才能繼續對話。'),
                        const SizedBox(height: 8),
                        FilledButton(
                          onPressed: () async {
                            await ExchangeStoreScope.of(
                              context,
                            ).api.acceptConversation(
                              identity: widget.identity,
                              conversationId: conversation.id,
                            );
                            if (mounted) {
                              Navigator.of(this.context).pop();
                            }
                          },
                          child: const Text('接受邀請'),
                        ),
                      ],
                    ),
                  ),
                ),
              Expanded(
                child: loading
                    ? const Center(child: CircularProgressIndicator())
                    : error != null
                    ? Padding(
                        padding: const EdgeInsets.all(20),
                        child: InlineError(message: error!, onRetry: _load),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: messages.length,
                        itemBuilder: (context, index) {
                          final message = messages[index];
                          final mine = message.authorId == widget.identity.id;
                          return Align(
                            alignment: mine
                                ? Alignment.centerRight
                                : Alignment.centerLeft,
                            child: Container(
                              constraints: const BoxConstraints(maxWidth: 300),
                              margin: const EdgeInsets.only(bottom: 10),
                              padding: const EdgeInsets.symmetric(
                                horizontal: 14,
                                vertical: 11,
                              ),
                              decoration: BoxDecoration(
                                color: mine
                                    ? ExchangeColors.teal
                                    : ExchangeColors.surface,
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: Text(
                                message.body,
                                style: TextStyle(
                                  color: mine
                                      ? Colors.white
                                      : ExchangeColors.ink,
                                ),
                              ),
                            ),
                          );
                        },
                      ),
              ),
              if (conversation.status == 'accepted')
                Padding(
                  padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
                  child: GlassCard(
                    padding: const EdgeInsets.all(8),
                    child: Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: controller,
                            decoration: const InputDecoration(
                              hintText: '輸入私訊',
                              border: InputBorder.none,
                              enabledBorder: InputBorder.none,
                              focusedBorder: InputBorder.none,
                              filled: false,
                            ),
                          ),
                        ),
                        IconButton.filled(
                          tooltip: '傳送私訊',
                          constraints: const BoxConstraints(
                            minWidth: 48,
                            minHeight: 48,
                          ),
                          onPressed: () async {
                            final body = controller.text.trim();
                            if (body.isEmpty) return;
                            await ExchangeStoreScope.of(
                              context,
                            ).api.sendPrivateMessage(
                              identity: widget.identity,
                              conversationId: conversation.id,
                              body: body,
                            );
                            controller.clear();
                            await _load();
                          },
                          icon: const Icon(Icons.arrow_upward_rounded),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

Future<void> _showPostComposer({
  required BuildContext context,
  required AnonymousIdentity identity,
  required String schoolName,
  required Future<void> Function() onSubmitted,
}) async {
  final title = TextEditingController();
  final body = TextEditingController();
  await showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (sheetContext) => Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        4,
        20,
        MediaQuery.viewInsetsOf(sheetContext).bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('發一篇匿名貼文', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 16),
          TextField(
            controller: title,
            decoration: const InputDecoration(labelText: '標題'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: body,
            minLines: 4,
            maxLines: 7,
            decoration: const InputDecoration(labelText: '想分享或詢問什麼？'),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: () async {
                if (title.text.trim().isEmpty || body.text.trim().isEmpty) {
                  return;
                }
                try {
                  await ExchangeStoreScope.of(context).api.publishPost(
                    identity: identity,
                    schoolName: schoolName,
                    postType: 'discussion',
                    topic: 'application',
                    country: '',
                    academicYear: '',
                    applicationStage: '',
                    title: title.text.trim(),
                    body: body.text.trim(),
                  );
                  if (sheetContext.mounted) Navigator.of(sheetContext).pop();
                  await onSubmitted();
                } catch (exception) {
                  if (sheetContext.mounted) {
                    _notice(sheetContext, exception.toString());
                  }
                }
              },
              icon: const Icon(Icons.publish_rounded),
              label: const Text('匿名發布'),
            ),
          ),
        ],
      ),
    ),
  );
  title.dispose();
  body.dispose();
}

Future<void> _showCommentComposer({
  required BuildContext context,
  required AnonymousIdentity identity,
  required String postId,
  required Future<void> Function() onSubmitted,
}) async {
  final body = TextEditingController();
  await showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (sheetContext) => Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        4,
        20,
        MediaQuery.viewInsetsOf(sheetContext).bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: body,
            minLines: 3,
            maxLines: 6,
            autofocus: true,
            decoration: const InputDecoration(labelText: '留言內容'),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: () async {
                if (body.text.trim().isEmpty) return;
                await ExchangeStoreScope.of(context).api.publishComment(
                  identity: identity,
                  postId: postId,
                  body: body.text.trim(),
                );
                if (sheetContext.mounted) Navigator.of(sheetContext).pop();
                await onSubmitted();
              },
              child: const Text('送出留言'),
            ),
          ),
        ],
      ),
    ),
  );
  body.dispose();
}

Future<void> _showInviteComposer({
  required BuildContext context,
  required AnonymousIdentity identity,
  required String schoolName,
  required Future<void> Function() onSubmitted,
  String? recipientId,
}) async {
  final recipient = TextEditingController(text: recipientId);
  final message = TextEditingController();
  await showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (sheetContext) => Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        4,
        20,
        MediaQuery.viewInsetsOf(sheetContext).bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('傳送私訊邀請', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          Text(
            '需要對方的匿名 ID；接受前只能傳送一次邀請訊息。',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 16),
          TextField(
            controller: recipient,
            decoration: const InputDecoration(labelText: '對方匿名 ID'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: message,
            minLines: 3,
            maxLines: 5,
            decoration: const InputDecoration(labelText: '邀請訊息'),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: () async {
                if (recipient.text.trim().isEmpty ||
                    message.text.trim().isEmpty) {
                  return;
                }
                try {
                  await ExchangeStoreScope.of(context).api.inviteConversation(
                    identity: identity,
                    schoolName: schoolName,
                    recipientId: recipient.text.trim(),
                    initialMessage: message.text.trim(),
                  );
                  if (sheetContext.mounted) Navigator.of(sheetContext).pop();
                  await onSubmitted();
                } catch (exception) {
                  if (sheetContext.mounted) {
                    _notice(sheetContext, exception.toString());
                  }
                }
              },
              icon: const Icon(Icons.send_rounded),
              label: const Text('傳送邀請'),
            ),
          ),
        ],
      ),
    ),
  );
  recipient.dispose();
  message.dispose();
}

String _shortTime(String value) {
  final date = DateTime.tryParse(value)?.toLocal();
  if (date == null) return '';
  return '${date.month}/${date.day} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
}

void _notice(BuildContext context, String message) {
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
}
