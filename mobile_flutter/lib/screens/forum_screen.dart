import 'package:flutter/material.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
import '../data/exchange_api.dart';
import '../data/forum_models.dart';
import '../state/exchange_store.dart';

String _session(ExchangeStore store) =>
    '${store.account?.id}:${store.accessToken}:${store.account?.emailVerified}';

String _message(Object error) =>
    error is ExchangeApiException ? error.message : '暫時無法連線，請稍後再試。';

String _date(String value) {
  final date = DateTime.tryParse(value)?.toLocal();
  return date == null ? '' : '${date.year}/${date.month}/${date.day}';
}

class ForumScreen extends StatelessWidget {
  const ForumScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    // Recreate the complete feed on logout/account changes, including in-flight reads.
    return _ForumFeed(key: ValueKey(_session(store)), store: store);
  }
}

class _ForumFeed extends StatefulWidget {
  const _ForumFeed({required this.store, super.key});
  final ExchangeStore store;
  @override
  State<_ForumFeed> createState() => _ForumFeedState();
}

class _ForumFeedState extends State<_ForumFeed> {
  final search = TextEditingController();
  List<ForumBoard> boards = [];
  List<ForumPost> posts = [];
  String board = '', topic = '', query = '';
  String? next, error;
  bool loading = true;
  int generation = 0;
  late final session = _session(widget.store);

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  Future<void> _load({bool more = false}) async {
    if (more && (loading || next == null)) return;
    final request = ++generation;
    setState(() {
      loading = true;
      error = null;
      if (!more) {
        posts = [];
        next = null;
      }
    });
    final store = widget.store;
    try {
      final results = await Future.wait<Object>([
        store.api.forumBoards(store.accessToken),
        store.api.forumFeed(
          store.accessToken,
          board: board,
          topic: topic,
          query: query,
          cursor: more ? next : null,
        ),
      ]);
      if (!mounted || request != generation || session != _session(store)) {
        return;
      }
      final page = results[1] as ForumPage<ForumPost>;
      setState(() {
        boards = results[0] as List<ForumBoard>;
        final ids = posts.map((p) => p.id).toSet();
        posts = [...posts, ...page.items.where((p) => ids.add(p.id))];
        next = page.next;
      });
    } catch (e) {
      if (mounted && request == generation && session == _session(store)) {
        setState(() => error = _message(e));
      }
    } finally {
      if (mounted && request == generation) setState(() => loading = false);
    }
  }

  Future<void> _compose() async {
    final allowed = boards.where((b) => b.canPost).toList();
    if (allowed.isEmpty) return;
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ForumComposer(
          store: widget.store,
          boards: allowed,
          initialBoard: board,
        ),
      ),
    );
    if (mounted && session == _session(widget.store)) await _load();
  }

  @override
  Widget build(BuildContext context) {
    final store = widget.store;
    final canPost = boards.any((b) => b.canPost);
    final filters = [
      InputDecorator(
        decoration: const InputDecoration(labelText: '看板'),
        child: DropdownButtonHideUnderline(
          child: DropdownButton<String>(
            isExpanded: true,
            isDense: true,
            value: boards.any((b) => b.id == board) ? board : '',
            items: [
              const DropdownMenuItem(value: '', child: Text('全部看板')),
              ...boards.map(
                (b) => DropdownMenuItem(
                  value: b.id,
                  enabled: b.canRead,
                  child: Row(
                    children: [
                      if (!b.canRead) ...[
                        const Icon(Icons.lock_outline_rounded, size: 16),
                        const SizedBox(width: 4),
                      ],
                      Expanded(
                        child: Text(b.label, overflow: TextOverflow.ellipsis),
                      ),
                    ],
                  ),
                ),
              ),
            ],
            onChanged: (value) {
              board = value ?? '';
              _load();
            },
          ),
        ),
      ),
      InputDecorator(
        decoration: const InputDecoration(labelText: '主題'),
        child: DropdownButtonHideUnderline(
          child: DropdownButton<String>(
            isExpanded: true,
            isDense: true,
            value: topic,
            items: [
              const DropdownMenuItem(value: '', child: Text('全部主題')),
              ...forumTopics.entries.map(
                (e) => DropdownMenuItem(
                  value: e.key,
                  child: Text(e.value, overflow: TextOverflow.ellipsis),
                ),
              ),
            ],
            onChanged: (value) {
              topic = value ?? '';
              _load();
            },
          ),
        ),
      ),
    ];
    return SafeArea(
      bottom: false,
      child: Stack(
        children: [
          RefreshIndicator(
            onRefresh: _load,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 200),
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                StudentHeading(
                  '交換生論壇',
                  action: IconButton(
                    tooltip: '論壇指南',
                    icon: const Icon(Icons.help_outline_rounded),
                    onPressed: () => showStudentGuide(
                      context,
                      title: '和同學一起準備',
                      steps: const [
                        (
                          icon: Icons.public_rounded,
                          title: '先逛看板',
                          detail: '訪客可閱讀公共看板。登入並驗證信箱後，可查看校板與發言。',
                        ),
                        (
                          icon: Icons.edit_outlined,
                          title: '分享與提問',
                          detail: '選看板與主題，匿名發文或在文章下回覆。',
                        ),
                        (
                          icon: Icons.shield_outlined,
                          title: '保護個人資料',
                          detail: '不要公開電話、Email 或社群帳號；不當內容可檢舉。',
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                if (store.account == null) ...[
                  Row(
                    children: [
                      const Icon(
                        Icons.lock_outline_rounded,
                        size: 20,
                        color: ExchangeColors.secondaryInk,
                      ),
                      const SizedBox(width: 8),
                      const Expanded(child: Text('訪客瀏覽')),
                      TextButton(
                        onPressed: () => store.selectMainTab(4),
                        child: const Text('登入參與討論'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                ],
                if (store.account != null && !canPost && !loading)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Text(
                      boards
                              .where((b) => b.reason.isNotEmpty)
                              .firstOrNull
                              ?.reason ??
                          '請確認帳號驗證狀態',
                    ),
                  ),
                TextField(
                  controller: search,
                  maxLength: 80,
                  textInputAction: TextInputAction.search,
                  decoration: InputDecoration(
                    hintText: '搜尋討論',
                    counterText: '',
                    suffixIcon: IconButton(
                      tooltip: '搜尋',
                      icon: const Icon(Icons.search_rounded),
                      onPressed: () {
                        query = search.text.trim();
                        _load();
                      },
                    ),
                  ),
                  onSubmitted: (value) {
                    query = value.trim();
                    _load();
                  },
                ),
                const SizedBox(height: 16),
                LayoutBuilder(
                  builder: (context, constraints) =>
                      MediaQuery.textScalerOf(context).scale(16) > 24
                      ? Column(
                          children: [
                            filters[0],
                            const SizedBox(height: 16),
                            filters[1],
                          ],
                        )
                      : Row(
                          children: [
                            Expanded(child: filters[0]),
                            const SizedBox(width: 12),
                            Expanded(child: filters[1]),
                          ],
                        ),
                ),
                const SizedBox(height: 24),
                if (loading) const LinearProgressIndicator(),
                if (error != null)
                  _ForumError(
                    error!,
                    () => _load(more: posts.isNotEmpty && next != null),
                  ),
                if (!loading && error == null && posts.isEmpty)
                  StudentEmptyState(
                    icon: Icons.forum_outlined,
                    title: '還沒有討論',
                    detail: query.isEmpty && board.isEmpty && topic.isEmpty
                        ? '分享經驗，或問一個問題。'
                        : '換個條件找找看。',
                    action: query.isEmpty && board.isEmpty && topic.isEmpty
                        ? null
                        : TextButton(
                            onPressed: () {
                              setState(() {
                                board = '';
                                topic = '';
                                query = '';
                                search.clear();
                              });
                              _load();
                            },
                            child: const Text('清除篩選'),
                          ),
                  ),
                ...posts.map(
                  (post) => GlassCard(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(20),
                    onTap: () async {
                      await Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => ForumPostScreen(
                            store: store,
                            postId: post.id,
                            board: boards
                                .where((b) => b.id == post.boardId)
                                .firstOrNull,
                          ),
                        ),
                      );
                      if (mounted && session == _session(store)) await _load();
                    },
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        StudentIconLabel(
                          Icons.forum_outlined,
                          boards
                                  .where((b) => b.id == post.boardId)
                                  .firstOrNull
                                  ?.label ??
                              post.school,
                          color: ExchangeColors.teal,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          post.title,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          post.body,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 16),
                        Wrap(
                          spacing: 16,
                          runSpacing: 8,
                          children: [
                            StudentIconLabel(
                              Icons.person_outline_rounded,
                              post.author,
                            ),
                            StudentIconLabel(
                              Icons.chat_bubble_outline_rounded,
                              '${post.comments}',
                            ),
                            Text(
                              _date(post.created),
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                if (next != null)
                  OutlinedButton(
                    onPressed: loading ? null : () => _load(more: true),
                    child: const Text('載入更多討論'),
                  ),
              ],
            ),
          ),
          Positioned(
            left: 20,
            right: 20,
            bottom: 116,
            child: FilledButton.icon(
              onPressed: canPost ? _compose : null,
              icon: const Icon(Icons.edit_outlined),
              label: const Text('發起討論'),
            ),
          ),
        ],
      ),
    );
  }
}

class _ForumError extends StatelessWidget {
  const _ForumError(this.message, this.retry);
  final String message;
  final VoidCallback retry;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 16),
    child: Column(
      children: [
        Text(message),
        TextButton(onPressed: retry, child: const Text('重試')),
      ],
    ),
  );
}

class ForumPostScreen extends StatefulWidget {
  const ForumPostScreen({
    required this.store,
    required this.postId,
    this.board,
    super.key,
  });
  final ExchangeStore store;
  final String postId;
  final ForumBoard? board;
  @override
  State<ForumPostScreen> createState() => _ForumPostScreenState();
}

class _ForumPostScreenState extends State<ForumPostScreen> {
  late final session = _session(widget.store);
  ForumPost? post;
  String? error;
  int revision = 0;
  bool loading = true;
  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final result = await widget.store.api.forumPost(
        widget.store.accessToken,
        widget.postId,
      );
      if (mounted && session == _session(widget.store)) {
        setState(() {
          post = result;
          revision++;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          error = _message(e);
          post = null;
        });
      }
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> _reply([String? parentId]) async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ForumComposer(
          store: widget.store,
          boards: const [],
          postId: widget.postId,
          parentId: parentId,
        ),
      ),
    );
    if (mounted && session == _session(widget.store)) await _load();
  }

  Future<void> _delete([String? commentId]) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('刪除這則內容？'),
        content: const Text('刪除後無法復原。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('刪除'),
          ),
        ],
      ),
    );
    if (confirmed != true || session != _session(widget.store)) return;
    try {
      final identity = await widget.store.ensureIdentity();
      if (!mounted || session != _session(widget.store)) return;
      await widget.store.api.deleteForum(
        widget.store.accessToken,
        identity,
        widget.postId,
        commentId: commentId,
      );
      if (!mounted || session != _session(widget.store)) return;
      if (commentId == null) {
        Navigator.pop(context);
      } else {
        await _load();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(_message(e))));
      }
    }
  }

  Future<void> _report(String type, String id) async {
    final reason = await showDialog<String>(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('檢舉原因'),
        children: ['廣告或垃圾內容', '騷擾或不當言論', '公開個人聯絡資料', '其他違反社群規範']
            .map(
              (reason) => SimpleDialogOption(
                onPressed: () => Navigator.pop(context, reason),
                child: Text(reason),
              ),
            )
            .toList(),
      ),
    );
    if (reason == null || session != _session(widget.store)) return;
    try {
      final identity = await widget.store.ensureIdentity();
      if (!mounted || session != _session(widget.store)) return;
      await widget.store.api
          .report(
            identity: identity,
            resourceType: type,
            resourceId: id,
            reason: reason,
          )
          .timeout(const Duration(seconds: 15));
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('已送出檢舉，交由管理員處理。')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(_message(e))));
      }
    }
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: widget.store,
    builder: (context, _) {
      final sameSession = session == _session(widget.store);
      final canReply = sameSession && widget.board?.canComment == true;
      return StudentPage(
        title: '討論內容',
        onRefresh: sameSession ? _load : null,
        bottomBar: !sameSession || post == null
            ? null
            : StudentActionBar(
                primary: FilledButton.icon(
                  onPressed: canReply ? () => _reply() : null,
                  icon: const Icon(Icons.reply_rounded),
                  label: const Text('回覆文章'),
                ),
              ),
        children: !sameSession
            ? [
                const StudentNotice(
                  '登入狀態已改變，請返回論壇重新開啟。',
                  icon: Icons.lock_outline_rounded,
                ),
              ]
            : [
                if (loading) const LinearProgressIndicator(),
                if (error != null) _ForumError(error!, _load),
                if (post != null) ...[
                  GlassCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.board?.label ?? post!.school,
                          style: const TextStyle(color: ExchangeColors.teal),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          post!.title,
                          style: Theme.of(context).textTheme.headlineSmall,
                        ),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 16,
                          runSpacing: 8,
                          children: [
                            StudentIconLabel(
                              Icons.person_outline_rounded,
                              post!.author,
                            ),
                            StudentIconLabel(
                              Icons.schedule_rounded,
                              _date(post!.created),
                            ),
                          ],
                        ),
                        const SizedBox(height: 20),
                        SelectableText(post!.body),
                        Wrap(
                          children: [
                            if (post!.canDelete)
                              TextButton.icon(
                                onPressed: _delete,
                                icon: const Icon(Icons.delete_outline_rounded),
                                label: const Text('刪除文章'),
                              ),
                            if (widget.store.account != null)
                              TextButton.icon(
                                onPressed: () => _report('post', post!.id),
                                icon: const Icon(Icons.flag_outlined),
                                label: const Text('檢舉文章'),
                              ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                  Text('回覆與討論', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 12),
                  if (!canReply)
                    Text(
                      widget.board?.reason.isNotEmpty == true
                          ? widget.board!.reason
                          : '登入並驗證信箱後即可回覆。',
                    ),

                  _ReplyList(
                    key: ValueKey(revision),
                    store: widget.store,
                    postId: widget.postId,
                    onReply: canReply ? _reply : null,
                    onDelete: _delete,
                    onReport: widget.store.account == null
                        ? null
                        : (id) => _report('comment', id),
                  ),
                ],
              ],
      );
    },
  );
}

class _ReplyList extends StatefulWidget {
  const _ReplyList({
    required this.store,
    required this.postId,
    required this.onDelete,
    this.parentId,
    this.onReply,
    this.onReport,
    super.key,
  });
  final ExchangeStore store;
  final String postId;
  final String? parentId;
  final void Function(String)? onReply, onReport;
  final void Function(String) onDelete;
  @override
  State<_ReplyList> createState() => _ReplyListState();
}

class _ReplyListState extends State<_ReplyList> {
  List<ForumReply> replies = [];
  final expanded = <String>{};
  String? next, error;
  bool loading = true;
  late final session = _session(widget.store);
  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final page = await widget.store.api.forumReplies(
        widget.store.accessToken,
        widget.postId,
        parentId: widget.parentId,
        cursor: next,
      );
      if (!mounted || session != _session(widget.store)) return;
      setState(() {
        final ids = replies.map((r) => r.id).toSet();
        replies.addAll(page.items.where((r) => ids.add(r.id)));
        next = page.next;
      });
    } catch (e) {
      if (mounted) setState(() => error = _message(e));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      if (loading) const LinearProgressIndicator(),
      if (error != null) _ForumError(error!, _load),
      if (!loading && error == null && replies.isEmpty)
        const Padding(padding: EdgeInsets.all(16), child: Text('目前還沒有回覆。')),
      ...replies.map(
        (reply) => GlassCard(
          margin: const EdgeInsets.only(top: 12),
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${reply.author} · ${_date(reply.created)}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 8),
              SelectableText(reply.body),
              Wrap(
                children: [
                  if (widget.onReply != null)
                    TextButton(
                      onPressed: () =>
                          widget.onReply!(widget.parentId ?? reply.id),
                      child: const Text('回覆'),
                    ),
                  if (reply.canDelete)
                    TextButton(
                      onPressed: () => widget.onDelete(reply.id),
                      child: const Text('刪除'),
                    ),
                  if (widget.onReport != null)
                    TextButton(
                      onPressed: () => widget.onReport!(reply.id),
                      child: const Text('檢舉'),
                    ),
                  if (widget.parentId == null && reply.replyCount > 0)
                    TextButton(
                      onPressed: () => setState(() {
                        expanded.contains(reply.id)
                            ? expanded.remove(reply.id)
                            : expanded.add(reply.id);
                      }),
                      child: Text(
                        expanded.contains(reply.id)
                            ? '收起回覆'
                            : '查看 ${reply.replyCount} 則回覆',
                      ),
                    ),
                ],
              ),
              if (expanded.contains(reply.id))
                _ReplyList(
                  store: widget.store,
                  postId: widget.postId,
                  parentId: reply.id,
                  onReply: widget.onReply,
                  onDelete: widget.onDelete,
                  onReport: widget.onReport,
                ),
            ],
          ),
        ),
      ),
      if (next != null)
        TextButton(
          onPressed: loading ? null : _load,
          child: const Text('載入更多回覆'),
        ),
    ],
  );
}

class ForumComposer extends StatefulWidget {
  const ForumComposer({
    required this.store,
    required this.boards,
    this.initialBoard = '',
    this.postId,
    this.parentId,
    super.key,
  });
  final ExchangeStore store;
  final List<ForumBoard> boards;
  final String initialBoard;
  final String? postId, parentId;
  @override
  State<ForumComposer> createState() => _ForumComposerState();
}

class _ForumComposerState extends State<ForumComposer> {
  final title = TextEditingController(), body = TextEditingController();
  late final session = _session(widget.store);
  late String board = widget.boards.any((b) => b.id == widget.initialBoard)
      ? widget.initialBoard
      : widget.boards.firstOrNull?.id ?? '';
  String topic = 'application';
  String? error;
  bool sending = false;
  @override
  void dispose() {
    title.dispose();
    body.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final isPost = widget.postId == null;
    final text = body.text.trim();
    if ((isPost && (title.text.trim().length < 4 || board.isEmpty)) ||
        text.length < (isPost ? 10 : 2)) {
      setState(
        () => error = isPost ? '請選擇看板，標題至少 4 字、內容至少 10 字。' : '回覆至少需要 2 個字。',
      );
      return;
    }
    setState(() {
      sending = true;
      error = null;
    });
    try {
      if (session != _session(widget.store)) {
        throw const ExchangeApiException('登入狀態已改變，請重新開啟編輯器。');
      }
      final identity = await widget.store.ensureIdentity();
      if (!mounted || session != _session(widget.store)) return;
      await widget.store.api.writeForum(
        widget.store.accessToken,
        identity,
        body: text,
        title: title.text.trim(),
        boardId: board,
        topic: topic,
        postId: widget.postId,
        parentId: widget.parentId,
      );
      if (!mounted || session != _session(widget.store)) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('已送出，內容將依看板規則顯示。')));
      Navigator.pop(context, true);
    } catch (e) {
      if (mounted) setState(() => error = _message(e));
    } finally {
      if (mounted) setState(() => sending = false);
    }
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: widget.store,
    builder: (context, _) {
      final isPost = widget.postId == null;
      final sameSession = session == _session(widget.store);
      return StudentPage(
        title: isPost ? '發起討論' : '撰寫回覆',
        bottomBar: !sameSession
            ? null
            : StudentActionBar(
                primary: FilledButton.icon(
                  onPressed: sending ? null : _send,
                  icon: const Icon(Icons.send_rounded),
                  label: Text(sending ? '送出中…' : '送出'),
                ),
              ),
        children: !sameSession
            ? [
                const StudentNotice(
                  '登入狀態已改變，請返回論壇重新開啟。',
                  icon: Icons.lock_outline_rounded,
                ),
              ]
            : [
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    StudentIconLabel(Icons.person_outline_rounded, '匿名發表'),
                    SizedBox(height: 8),
                    StudentIconLabel(
                      Icons.shield_outlined,
                      '勿公開電話、Email 或社群帳號',
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                if (isPost) ...[
                  DropdownButtonFormField<String>(
                    initialValue: board,
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: '發文看板',
                      prefixIcon: Icon(Icons.forum_outlined),
                    ),
                    items: widget.boards
                        .map(
                          (b) => DropdownMenuItem(
                            value: b.id,
                            child: Text(
                              b.label,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        )
                        .toList(),
                    onChanged: sending
                        ? null
                        : (value) => setState(() => board = value!),
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    initialValue: topic,
                    decoration: const InputDecoration(
                      labelText: '討論主題',
                      prefixIcon: Icon(Icons.label_outline_rounded),
                    ),
                    items: forumTopics.entries
                        .map(
                          (e) => DropdownMenuItem(
                            value: e.key,
                            child: Text(e.value),
                          ),
                        )
                        .toList(),
                    onChanged: sending
                        ? null
                        : (value) => setState(() => topic = value!),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: title,
                    enabled: !sending,
                    maxLength: 120,
                    decoration: const InputDecoration(
                      labelText: '標題',
                      prefixIcon: Icon(Icons.title_rounded),
                    ),
                  ),
                ],
                TextField(
                  controller: body,
                  enabled: !sending,
                  minLines: 5,
                  maxLines: 14,
                  maxLength: isPost ? 1600 : 800,
                  decoration: InputDecoration(
                    labelText: isPost ? '討論內容' : '回覆內容',
                    alignLabelWithHint: true,
                    prefixIcon: const Icon(Icons.notes_rounded),
                  ),
                ),
                if (error != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Text(
                      error!,
                      style: const TextStyle(color: ExchangeColors.danger),
                    ),
                  ),
              ],
      );
    },
  );
}
