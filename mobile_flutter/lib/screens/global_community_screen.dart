import 'dart:async';

import 'package:flutter/material.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import 'account_screen.dart';
import 'community_screen.dart';

const publicCommunityBoard = '公共留學板';
const legacyPublicCommunityBoard = '一般留學討論';
const cguCommunityBoard = '長庚大學';

enum CommunityFeed { all, following, publicBoard, cguBoard }

class GlobalCommunityScreen extends StatefulWidget {
  const GlobalCommunityScreen({
    required this.onOpenCguBoard,
    this.initialFeed = CommunityFeed.all,
    this.includeCguFeed = true,
    this.showCguChatShortcut = true,
    this.onFeedChanged,
    super.key,
  });

  final VoidCallback onOpenCguBoard;
  final CommunityFeed initialFeed;
  final bool includeCguFeed;
  final bool showCguChatShortcut;
  final ValueChanged<CommunityFeed>? onFeedChanged;

  @override
  State<GlobalCommunityScreen> createState() => GlobalCommunityScreenState();
}

class GlobalCommunityScreenState extends State<GlobalCommunityScreen> {
  final searchController = TextEditingController();
  List<CommunityThread> posts = const [];
  String topic = '';
  late CommunityFeed feed;
  String? error;
  bool loading = true;
  bool initialized = false;
  Timer? searchTimer;

  @override
  void initState() {
    super.initState();
    feed = widget.initialFeed;
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!initialized) {
      initialized = true;
      Future<void>.microtask(_loadPosts);
    }
  }

  @override
  void dispose() {
    searchTimer?.cancel();
    searchController.dispose();
    super.dispose();
  }

  Future<void> _loadPosts() async {
    if (!mounted) return;
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final store = ExchangeStoreScope.of(context);
      if (feed == CommunityFeed.following && store.account == null) {
        if (mounted) setState(() => posts = const []);
        return;
      }
      final followed =
          store.account?.followedBoards.toSet() ?? const <String>{};
      if (feed == CommunityFeed.following && followed.isEmpty) {
        if (mounted) setState(() => posts = const []);
        return;
      }
      final schoolName = switch (feed) {
        CommunityFeed.publicBoard => publicCommunityBoard,
        CommunityFeed.cguBoard => cguCommunityBoard,
        _ => null,
      };
      var data = await store.api.posts(
        schoolName: schoolName,
        topic: topic.isEmpty ? null : topic,
        query: searchController.text.trim().isEmpty
            ? null
            : searchController.text.trim(),
      );
      if (feed == CommunityFeed.following) {
        data = data
            .where((thread) => followed.contains(thread.post.schoolName))
            .toList();
      }
      if (mounted) setState(() => posts = data);
    } catch (exception) {
      if (mounted) setState(() => error = exception.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> _requireAccount() async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ExchangePageBackground(
          child: Scaffold(body: const AccountScreen()),
        ),
      ),
    );
    if (mounted) setState(() {});
  }

  Future<AnonymousIdentity?> _identityOrLogin() async {
    final store = ExchangeStoreScope.of(context);
    if (store.account == null) {
      await _requireAccount();
      if (!mounted || store.account == null) return null;
    }
    try {
      return await store.ensureIdentity();
    } catch (exception) {
      if (mounted) _notice(context, exception.toString());
      return null;
    }
  }

  Future<void> _openSchoolCommunity() async {
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ExchangePageBackground(
          child: Scaffold(
            body: const CommunityScreen(initialSchool: cguCommunityBoard),
          ),
        ),
      ),
    );
  }

  void selectFeed(CommunityFeed value) {
    if (feed == value) return;
    setState(() => feed = value);
    widget.onFeedChanged?.call(value);
    _loadPosts();
  }

  Future<void> openComposer() async {
    final store = ExchangeStoreScope.of(context);
    await _showPostComposer(store);
  }

  Future<void> _toggleCguFollow() async {
    final store = ExchangeStoreScope.of(context);
    if (store.account == null) {
      await _requireAccount();
      if (!mounted || store.account == null) return;
    }
    try {
      await store.toggleBoardFollow(cguCommunityBoard);
      if (mounted && feed == CommunityFeed.following) await _loadPosts();
    } catch (exception) {
      if (mounted) _notice(context, exception.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    return SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: _loadPosts,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 112),
          children: [
            _CommunityHeader(
              accountName: store.account?.displayName,
              onAccount: _requireAccount,
              onCompose: () => _showPostComposer(store),
            ),
            const SizedBox(height: 12),
            _FeedSelector(
              selected: feed,
              includeCgu: widget.includeCguFeed,
              onSelected: selectFeed,
            ),
            const SizedBox(height: 14),
            _BoardRail(
              followingCgu: store.followsBoard(cguCommunityBoard),
              updatingFollow: store.isUpdatingBoardFollow,
              onOpenPublic: () => selectFeed(CommunityFeed.publicBoard),
              onOpenCgu: widget.onOpenCguBoard,
              onFollowCgu: _toggleCguFollow,
            ),
            const SizedBox(height: 18),
            SizedBox(
              height: 48,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: _topics.length,
                separatorBuilder: (_, _) => const SizedBox(width: 8),
                itemBuilder: (context, index) {
                  final item = _topics[index];
                  return ChoiceChip(
                    label: Text(item.$2),
                    selected: topic == item.$1,
                    onSelected: (_) {
                      setState(() => topic = item.$1);
                      _loadPosts();
                    },
                  );
                },
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: searchController,
              onChanged: (_) {
                searchTimer?.cancel();
                searchTimer = Timer(
                  const Duration(milliseconds: 320),
                  _loadPosts,
                );
              },
              decoration: InputDecoration(
                hintText: '搜尋學校、國家或問題',
                prefixIcon: const Icon(Icons.search_rounded),
                suffixIcon: searchController.text.isEmpty
                    ? null
                    : IconButton(
                        tooltip: '清除搜尋',
                        onPressed: () {
                          searchController.clear();
                          _loadPosts();
                        },
                        icon: const Icon(Icons.close_rounded),
                      ),
              ),
            ),
            const SizedBox(height: 18),
            Row(
              children: [
                Expanded(
                  child: Text(
                    _feedTitle(feed),
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ),
                if (widget.showCguChatShortcut)
                  TextButton.icon(
                    onPressed: _openSchoolCommunity,
                    icon: const Icon(Icons.forum_outlined),
                    label: const Text('長庚聊天室'),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            if (feed == CommunityFeed.following && store.account == null)
              _FollowingGate(onSignIn: _requireAccount)
            else if (feed == CommunityFeed.following &&
                store.account!.followedBoards.isEmpty)
              _FollowingEmpty(onFollow: _toggleCguFollow)
            else if (loading)
              const LoadingCards(count: 3)
            else if (error != null)
              InlineError(message: error!, onRetry: _loadPosts)
            else if (posts.isEmpty)
              _EmptyCommunity(onCompose: () => _showPostComposer(store))
            else
              ...posts.map(
                (thread) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _CommunityPostCard(
                    thread: thread,
                    onComment: () => _showCommentComposer(thread.post.id),
                    onReport: () => _reportPost(thread.post.id),
                    onInvite: thread.post.authorId == store.identity?.id
                        ? null
                        : () => _showInviteComposer(thread.post),
                  ),
                ),
              ),
            const SizedBox(height: 16),
            const _SafetyNote(),
          ],
        ),
      ),
    );
  }

  Future<void> _showPostComposer(ExchangeStore store) async {
    final identity = await _identityOrLogin();
    if (identity == null || !mounted) return;
    final title = TextEditingController();
    final body = TextEditingController();
    final country = TextEditingController();
    final academicYear = TextEditingController();
    var postType = 'discussion';
    var selectedTopic = 'application';
    var schoolName = feed == CommunityFeed.cguBoard
        ? cguCommunityBoard
        : publicCommunityBoard;
    var stage = store.account?.applicationStage ?? 'exploring';
    String? formError;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setSheetState) {
          const schools = [publicCommunityBoard, cguCommunityBoard];
          return SafeArea(
            top: false,
            child: SingleChildScrollView(
              padding: EdgeInsets.fromLTRB(
                20,
                4,
                20,
                MediaQuery.viewInsetsOf(sheetContext).bottom + 24,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '發一篇文章',
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 18),
                  Row(
                    children: [
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          initialValue: postType,
                          decoration: const InputDecoration(labelText: '文章類型'),
                          items: const [
                            DropdownMenuItem(
                              value: 'discussion',
                              child: Text('討論'),
                            ),
                            DropdownMenuItem(
                              value: 'question',
                              child: Text('請益'),
                            ),
                            DropdownMenuItem(
                              value: 'experience',
                              child: Text('經驗分享'),
                            ),
                          ],
                          onChanged: (value) {
                            if (value != null) postType = value;
                          },
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          initialValue: selectedTopic,
                          decoration: const InputDecoration(labelText: '主題'),
                          items: _topics
                              .where((item) => item.$1.isNotEmpty)
                              .map(
                                (item) => DropdownMenuItem(
                                  value: item.$1,
                                  child: Text(item.$2),
                                ),
                              )
                              .toList(),
                          onChanged: (value) {
                            if (value != null) selectedTopic = value;
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: schoolName,
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: '發布看板',
                      prefixIcon: Icon(Icons.dashboard_outlined),
                    ),
                    items: schools
                        .map(
                          (school) => DropdownMenuItem(
                            value: school,
                            child: Text(
                              school,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        )
                        .toList(),
                    onChanged: (value) {
                      if (value != null) schoolName = value;
                    },
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: country,
                          decoration: const InputDecoration(labelText: '國家'),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: TextField(
                          controller: academicYear,
                          decoration: const InputDecoration(
                            labelText: '學年度',
                            hintText: '2026',
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: stage,
                    decoration: const InputDecoration(labelText: '申請階段'),
                    items: _stageLabels.entries
                        .map(
                          (entry) => DropdownMenuItem(
                            value: entry.key,
                            child: Text(entry.value),
                          ),
                        )
                        .toList(),
                    onChanged: (value) {
                      if (value != null) stage = value;
                    },
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: title,
                    decoration: const InputDecoration(labelText: '標題'),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: body,
                    minLines: 5,
                    maxLines: 9,
                    decoration: const InputDecoration(
                      labelText: '內容',
                      hintText: '提供具體背景與真正卡住的地方',
                    ),
                  ),
                  if (formError != null) ...[
                    const SizedBox(height: 10),
                    Text(
                      formError!,
                      style: const TextStyle(
                        color: ExchangeColors.danger,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: () async {
                        if (title.text.trim().length < 4 ||
                            body.text.trim().length < 10) {
                          setSheetState(
                            () => formError = '標題至少 4 個字，內容至少 10 個字。',
                          );
                          return;
                        }
                        try {
                          await store.api.publishPost(
                            identity: identity,
                            schoolName: schoolName,
                            postType: postType,
                            topic: selectedTopic,
                            country: country.text.trim(),
                            academicYear: academicYear.text.trim(),
                            applicationStage: stage,
                            title: title.text.trim(),
                            body: body.text.trim(),
                          );
                          if (sheetContext.mounted) {
                            Navigator.of(sheetContext).pop();
                          }
                          await _loadPosts();
                        } catch (exception) {
                          setSheetState(() => formError = exception.toString());
                        }
                      },
                      icon: const Icon(Icons.publish_rounded),
                      label: const Text('發布文章'),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
    title.dispose();
    body.dispose();
    country.dispose();
    academicYear.dispose();
  }

  Future<void> _showCommentComposer(String postId) async {
    final identity = await _identityOrLogin();
    if (identity == null || !mounted) return;
    final controller = TextEditingController();
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
              controller: controller,
              autofocus: true,
              minLines: 3,
              maxLines: 6,
              decoration: const InputDecoration(labelText: '回覆內容'),
            ),
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () async {
                  if (controller.text.trim().length < 2) return;
                  await ExchangeStoreScope.of(context).api.publishComment(
                    identity: identity,
                    postId: postId,
                    body: controller.text.trim(),
                  );
                  if (sheetContext.mounted) Navigator.of(sheetContext).pop();
                  await _loadPosts();
                },
                child: const Text('送出回覆'),
              ),
            ),
          ],
        ),
      ),
    );
    controller.dispose();
  }

  Future<void> _reportPost(String postId) async {
    final identity = await _identityOrLogin();
    if (identity == null || !mounted) return;
    await ExchangeStoreScope.of(context).api.report(
      identity: identity,
      resourceType: 'post',
      resourceId: postId,
      reason: '內容需要管理員檢查',
    );
    if (mounted) _notice(context, '已送出檢舉');
  }

  Future<void> _showInviteComposer(CommunityPost post) async {
    final identity = await _identityOrLogin();
    if (identity == null || !mounted) return;
    final controller = TextEditingController();
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
            Text(
              '邀請 ${post.displayName} 私訊',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 6),
            Text('對方接受後才能繼續傳訊。', style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 14),
            TextField(
              controller: controller,
              minLines: 3,
              maxLines: 5,
              decoration: const InputDecoration(labelText: '邀請訊息'),
            ),
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: () async {
                  if (controller.text.trim().length < 2) return;
                  await ExchangeStoreScope.of(context).api.inviteConversation(
                    identity: identity,
                    schoolName: post.schoolName,
                    recipientId: post.authorId,
                    initialMessage: controller.text.trim(),
                  );
                  if (sheetContext.mounted) Navigator.of(sheetContext).pop();
                  if (mounted) _notice(context, '私訊邀請已送出');
                },
                icon: const Icon(Icons.mail_outline_rounded),
                label: const Text('傳送邀請'),
              ),
            ),
          ],
        ),
      ),
    );
    controller.dispose();
  }
}

class _CommunityHeader extends StatelessWidget {
  const _CommunityHeader({
    required this.accountName,
    required this.onAccount,
    required this.onCompose,
  });

  final String? accountName;
  final VoidCallback onAccount;
  final VoidCallback onCompose;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Text('留學首頁', style: Theme.of(context).textTheme.displaySmall),
        ),
        const SizedBox(width: 8),
        IconButton.outlined(
          tooltip: accountName == null ? '登入' : '我的帳號',
          onPressed: onAccount,
          constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
          icon: Icon(
            accountName == null
                ? Icons.person_outline_rounded
                : Icons.person_rounded,
          ),
        ),
        const SizedBox(width: 8),
        IconButton.filled(
          tooltip: '發一篇文章',
          onPressed: onCompose,
          constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
          icon: const Icon(Icons.edit_square),
        ),
      ],
    );
  }
}

class _FeedSelector extends StatelessWidget {
  const _FeedSelector({
    required this.selected,
    required this.includeCgu,
    required this.onSelected,
  });

  final CommunityFeed selected;
  final bool includeCgu;
  final ValueChanged<CommunityFeed> onSelected;

  static const _baseItems = [
    (CommunityFeed.all, Icons.auto_awesome_rounded, '全部'),
    (CommunityFeed.following, Icons.rss_feed_rounded, '追蹤'),
    (CommunityFeed.publicBoard, Icons.public_rounded, '公共板'),
  ];

  List<(CommunityFeed, IconData, String)> get items => [
    ..._baseItems,
    if (includeCgu) (CommunityFeed.cguBoard, Icons.school_outlined, '長庚板'),
  ];

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 48,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: items.length,
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final item = items[index];
          return ChoiceChip(
            avatar: Icon(item.$2, size: 18),
            label: Text(item.$3),
            selected: selected == item.$1,
            onSelected: (_) => onSelected(item.$1),
          );
        },
      ),
    );
  }
}

class _BoardRail extends StatelessWidget {
  const _BoardRail({
    required this.followingCgu,
    required this.updatingFollow,
    required this.onOpenPublic,
    required this.onOpenCgu,
    required this.onFollowCgu,
  });

  final bool followingCgu;
  final bool updatingFollow;
  final VoidCallback onOpenPublic;
  final VoidCallback onOpenCgu;
  final VoidCallback onFollowCgu;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 180,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          _BoardCard(
            asset: 'assets/images/community-students.jpg',
            title: '公共留學板',
            description: '跨校申請、簽證與海外生活',
            onOpen: onOpenPublic,
          ),
          const SizedBox(width: 12),
          _BoardCard(
            asset: 'assets/images/cgu-campus.jpg',
            title: '長庚大學板',
            description: '申請資訊、合作校與同學討論',
            following: followingCgu,
            updatingFollow: updatingFollow,
            onFollow: onFollowCgu,
            onOpen: onOpenCgu,
          ),
        ],
      ),
    );
  }
}

class _BoardCard extends StatelessWidget {
  const _BoardCard({
    required this.asset,
    required this.title,
    required this.description,
    required this.onOpen,
    this.following = false,
    this.updatingFollow = false,
    this.onFollow,
  });

  final String asset;
  final String title;
  final String description;
  final VoidCallback onOpen;
  final bool following;
  final bool updatingFollow;
  final VoidCallback? onFollow;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 300,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: Stack(
          fit: StackFit.expand,
          children: [
            Image.asset(asset, fit: BoxFit.cover),
            const DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Color(0x16101820), Color(0xE30A1821)],
                  stops: [.18, 1],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Text(
                    title,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  Text(
                    description,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: const Color(0xDDFFFFFF),
                    ),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      if (onFollow != null) ...[
                        SizedBox(
                          height: 44,
                          child: OutlinedButton.icon(
                            onPressed: updatingFollow ? null : onFollow,
                            style: OutlinedButton.styleFrom(
                              backgroundColor: Colors.white.withValues(
                                alpha: .9,
                              ),
                              foregroundColor: ExchangeColors.ink,
                            ),
                            icon: updatingFollow
                                ? const SizedBox.square(
                                    dimension: 16,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : Icon(
                                    following
                                        ? Icons.check_rounded
                                        : Icons.add_rounded,
                                  ),
                            label: Text(following ? '已追蹤' : '追蹤'),
                          ),
                        ),
                        const SizedBox(width: 8),
                      ],
                      Expanded(
                        child: SizedBox(
                          height: 44,
                          child: FilledButton.icon(
                            onPressed: onOpen,
                            icon: const Icon(Icons.arrow_forward_rounded),
                            label: Text(onFollow == null ? '查看貼文' : '進入看板'),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FollowingGate extends StatelessWidget {
  const _FollowingGate({required this.onSignIn});

  final VoidCallback onSignIn;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        children: [
          const ExchangeIconBadge(Icons.rss_feed_rounded),
          const SizedBox(height: 10),
          Text('登入查看追蹤動態', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 14),
          FilledButton(onPressed: onSignIn, child: const Text('登入或建立帳號')),
        ],
      ),
    );
  }
}

class _FollowingEmpty extends StatelessWidget {
  const _FollowingEmpty({required this.onFollow});

  final VoidCallback onFollow;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        children: [
          const ExchangeIconBadge(Icons.school_outlined),
          const SizedBox(height: 10),
          Text('還沒有追蹤看板', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 14),
          OutlinedButton.icon(
            onPressed: onFollow,
            icon: const Icon(Icons.add_rounded),
            label: const Text('追蹤長庚大學板'),
          ),
        ],
      ),
    );
  }
}

class _CommunityPostCard extends StatelessWidget {
  const _CommunityPostCard({
    required this.thread,
    required this.onComment,
    required this.onReport,
    required this.onInvite,
  });

  final CommunityThread thread;
  final VoidCallback onComment;
  final VoidCallback onReport;
  final VoidCallback? onInvite;

  @override
  Widget build(BuildContext context) {
    final post = thread.post;
    final metadata = [
      _topicLabel(post.topic),
      post.country,
      post.academicYear,
      _stageLabels[post.applicationStage],
    ].where((value) => value != null && value.isNotEmpty).join(' · ');
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const CircleAvatar(
                backgroundColor: ExchangeColors.blueSoft,
                foregroundColor: ExchangeColors.blue,
                child: Icon(Icons.person_outline_rounded),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      post.displayName,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    Text(
                      [
                        metadata,
                        _shortTime(post.createdAt),
                      ].where((value) => value.isNotEmpty).join(' · '),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              PopupMenuButton<String>(
                tooltip: '文章操作',
                onSelected: (value) {
                  if (value == 'invite') onInvite?.call();
                  if (value == 'report') onReport();
                },
                itemBuilder: (_) => [
                  if (onInvite != null)
                    const PopupMenuItem(value: 'invite', child: Text('邀請私訊')),
                  const PopupMenuItem(value: 'report', child: Text('檢舉文章')),
                ],
              ),
            ],
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 7,
            runSpacing: 7,
            children: [
              _MetaChip(text: _displayBoardName(post.schoolName)),
              _MetaChip(text: _postTypeLabel(post.postType)),
            ],
          ),
          const SizedBox(height: 12),
          Text(post.title, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 7),
          Text(post.body),
          const SizedBox(height: 10),
          ExpansionTile(
            tilePadding: EdgeInsets.zero,
            childrenPadding: EdgeInsets.zero,
            shape: const Border(),
            collapsedShape: const Border(),
            title: Text('${thread.comments.length} 則回覆'),
            children: [
              ...thread.comments.map(
                (comment) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const CircleAvatar(
                    radius: 16,
                    backgroundColor: ExchangeColors.tealSoft,
                    child: Icon(
                      Icons.person_outline_rounded,
                      size: 17,
                      color: ExchangeColors.teal,
                    ),
                  ),
                  title: Text(comment.displayName),
                  subtitle: Text(comment.body),
                ),
              ),
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton.icon(
                  onPressed: onComment,
                  icon: const Icon(Icons.reply_rounded),
                  label: const Text('加入回覆'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _MetaChip extends StatelessWidget {
  const _MetaChip({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: ExchangeColors.blueSoft,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: ExchangeColors.blue,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _EmptyCommunity extends StatelessWidget {
  const _EmptyCommunity({required this.onCompose});

  final VoidCallback onCompose;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        children: [
          const ExchangeIconBadge(Icons.forum_outlined),
          const SizedBox(height: 12),
          Text('這個主題還沒有文章', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 14),
          OutlinedButton(onPressed: onCompose, child: const Text('登入後發文')),
        ],
      ),
    );
  }
}

class _SafetyNote extends StatelessWidget {
  const _SafetyNote();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      tint: ExchangeColors.tealSoft.withValues(alpha: .5),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.verified_user_outlined, color: ExchangeColors.success),
          SizedBox(width: 12),
          Expanded(
            child: Text('可用暱稱發文；不要公開電話、Email 或社群帳號。私訊需由對方接受，申請資訊仍以官方來源為準。'),
          ),
        ],
      ),
    );
  }
}

String _shortTime(String value) {
  final date = DateTime.tryParse(value)?.toLocal();
  if (date == null) return '';
  return '${date.month}/${date.day} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
}

String _feedTitle(CommunityFeed feed) => switch (feed) {
  CommunityFeed.all => '最新貼文',
  CommunityFeed.following => '我的追蹤',
  CommunityFeed.publicBoard => '公共留學板',
  CommunityFeed.cguBoard => '長庚大學板貼文',
};

String _displayBoardName(String value) =>
    value == legacyPublicCommunityBoard ? publicCommunityBoard : value;

String _topicLabel(String value) => switch (value) {
  'application' => '申請',
  'scholarship' => '獎學金',
  'housing' => '住宿',
  'cost' => '生活費',
  'visa' => '簽證',
  'academics' => '課程',
  'life' => '生活',
  'career' => '就業',
  'warning' => '避雷',
  _ => value,
};

String _postTypeLabel(String value) =>
    const {'discussion': '討論', 'question': '請益', 'experience': '經驗分享'}[value] ??
    '文章';

void _notice(BuildContext context, String message) {
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
}

const _topics = [
  ('', '全部'),
  ('application', '申請'),
  ('scholarship', '獎學金'),
  ('housing', '住宿'),
  ('cost', '生活費'),
  ('visa', '簽證'),
  ('academics', '課程'),
  ('life', '生活'),
  ('career', '就業'),
  ('warning', '避雷'),
];

const _stageLabels = {
  'exploring': '探索中',
  'eligibility': '確認資格',
  'documents': '準備文件',
  'submitted': '已送件',
  'accepted': '已錄取',
  'abroad': '正在海外',
  'returned': '已返台',
};
