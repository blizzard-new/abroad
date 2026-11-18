import 'package:flutter/material.dart';

import '../core/application_calendar.dart';
import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
import '../core/uniway_brand.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import '../state/workspace_sync.dart';
import 'deadlines_screen.dart';
import 'feature_screens.dart';
import 'notification_screen.dart';
import 'root_shell.dart';
import 'school_detail_screen.dart';
import 'student_plan_screens.dart';

class JourneyScreen extends StatelessWidget {
  const JourneyScreen({super.key, required this.onSelectTab});

  final ValueChanged<int> onSelectTab;

  void _open(BuildContext context, Widget page) =>
      Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final account = store.account;
    final priorityEvents = store.upcomingPriorityCalendarEvents;
    final next = priorityEvents.firstOrNull;
    final schools = store.dashboard?.partnerUniversities ?? const [];
    final savedSchools = schools
        .where((s) => store.favorites.contains(s.schoolName))
        .toList();
    final destinations = (savedSchools.isEmpty ? schools : savedSchools)
        .take(4)
        .toList();

    final hasProfile = store.planProfile != null;
    final hasTarget = store.applicationContext.targetSchool.trim().isNotEmpty;
    final stepTitle = !hasProfile
        ? '設定選校條件'
        : store.favorites.isEmpty
        ? '收藏候選合作校'
        : !hasTarget
        ? '選定申請目標校'
        : '完成校內申請文件';
    final stepDetail = !hasProfile
        ? '填寫學院、學制、平均成績與語檢，找學校頁會自動標示初步資格。'
        : hasTarget
        ? '目前目標校：${store.applicationContext.targetSchool}'
        : store.planProfile!.summaryLabel;
    final primaryCtaLabel = !hasProfile
        ? '設定選校條件'
        : (!hasTarget ? '前往找學校' : '繼續填寫文件');

    void handlePrimaryAction() {
      if (!hasProfile) {
        _open(context, const EligibilityScreen());
      } else if (!hasTarget) {
        onSelectTab(1);
      } else {
        onSelectTab(2);
      }
    }

    final readyDocsLabel = store.applicationTemplates.isEmpty
        ? '${store.applicationFormReadyCount}'
        : '${store.applicationFormReadyCount} / ${store.applicationTemplates.length}';

    return SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: store.refresh,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
          children: [
            Row(
              children: [
                const Expanded(child: UniWayLogo(wordmark: true)),
                IconButton(
                  tooltip: '使用指南',
                  onPressed: () =>
                      showStudentGuide(context, steps: journeyGuide),
                  icon: const Icon(Icons.help_outline_rounded),
                ),
                IconButton(
                  tooltip: '通知與提醒',
                  onPressed: () => _open(context, const NotificationScreen()),
                  icon: const Icon(Icons.notifications_none_rounded),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              '交換準備總覽',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 10),
            Align(
              alignment: Alignment.centerLeft,
              child: ActionChip(
                key: const ValueKey('journey-university-switcher'),
                avatar: const Icon(Icons.school_outlined, size: 16),
                label: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Flexible(
                      child: Text(
                        store.selectedUniversity,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: 4),
                    const Icon(Icons.expand_more_rounded, size: 18),
                  ],
                ),
                tooltip: '切換就讀大學',
                onPressed: () => showUniversityPickerSheet(context),
              ),
            ),
            const SizedBox(height: 16),
            GlassCard(
              tint: ExchangeColors.surfaceMuted,
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      const Icon(
                        Icons.alt_route_rounded,
                        size: 18,
                        color: ExchangeColors.actionBlue,
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          hasProfile ? '目前進度下一步' : '快速開始',
                          style: Theme.of(context).textTheme.labelMedium
                              ?.copyWith(color: ExchangeColors.actionBlue),
                        ),
                      ),
                      if (hasProfile)
                        TextButton(
                          onPressed: () =>
                              _open(context, const EligibilityScreen()),
                          style: TextButton.styleFrom(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 4,
                            ),
                            minimumSize: const Size(48, 36),
                          ),
                          child: const Text('編輯選校條件'),
                        ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    stepTitle,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 6),
                  Text(
                    stepDetail,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: handlePrimaryAction,
                    icon: const Icon(Icons.arrow_forward_rounded, size: 18),
                    label: Text(primaryCtaLabel),
                  ),
                  if (!hasProfile) ...[
                    const SizedBox(height: 8),
                    OutlinedButton(
                      onPressed: () => onSelectTab(1),
                      child: const Text('先瀏覽全部合作校'),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 12),
            LayoutBuilder(
              builder: (context, constraints) {
                final singleColumn =
                    constraints.maxWidth < 280 ||
                    MediaQuery.textScalerOf(context).scale(16) >= 26;
                final cardWidth = singleColumn
                    ? constraints.maxWidth
                    : (constraints.maxWidth - 12) / 2;
                return Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    for (final item in [
                      (
                        icon: Icons.bookmark_outline_rounded,
                        count: '${store.favorites.length}',
                        label: '收藏學校',
                        tab: 1,
                      ),
                      (
                        icon: Icons.task_alt_rounded,
                        count: readyDocsLabel,
                        label: '完成文件',
                        tab: 2,
                      ),
                    ])
                      SizedBox(
                        width: cardWidth,
                        child: GlassCard(
                          padding: const EdgeInsets.all(16),
                          onTap: () => onSelectTab(item.tab),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(
                                item.icon,
                                color: ExchangeColors.actionBlue,
                                size: 22,
                              ),
                              const SizedBox(height: 10),
                              Text(
                                item.count,
                                style: Theme.of(context)
                                    .textTheme
                                    .headlineSmall
                                    ?.copyWith(
                                      fontFeatures:
                                          ExchangeColors.tabularFigures,
                                    ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                item.label,
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ],
                          ),
                        ),
                      ),
                  ],
                );
              },
            ),
            const SizedBox(height: 24),
            ExchangeSectionHeader(
              title: '下一個重要期限',
              action: TextButton(
                onPressed: () => _open(context, const DeadlinesScreen()),
                child: const Text('全部時程'),
              ),
            ),
            const SizedBox(height: 10),
            _NextDeadlineCard(
              event: next,
              onTap: () => _open(context, const DeadlinesScreen()),
            ),
            const SizedBox(height: 24),
            ExchangeSectionHeader(
              title: savedSchools.isEmpty ? '合作學校預覽' : '已收藏合作校',
              action: TextButton(
                onPressed: () => onSelectTab(1),
                child: const Text('查看全部'),
              ),
            ),
            const SizedBox(height: 10),
            if (destinations.isEmpty)
              GlassCard(
                child: StudentActionRow(
                  icon: Icons.travel_explore_rounded,
                  title: '瀏覽合作學校',
                  detail: '依就讀大學查看合作名單、名額與申請期限',
                  onTap: () => onSelectTab(1),
                ),
              )
            else
              ...destinations.map(
                (school) => Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: _CompactPartnerCard(
                    school: school,
                    onTap: () =>
                        _open(context, SchoolDetailScreen(school: school)),
                  ),
                ),
              ),
            const SizedBox(height: 20),
            const ExchangeSectionHeader(title: '常用工具'),
            const SizedBox(height: 10),
            StudentActionGrid([
              StudentAction(
                Icons.event_note_outlined,
                '申請時程',
                () => _open(context, const DeadlinesScreen()),
                color: ExchangeColors.actionBlue,
              ),
              StudentAction(
                Icons.savings_outlined,
                '補助資訊',
                () => _open(context, const ScholarshipsScreen()),
                color: ExchangeColors.success,
              ),
              StudentAction(
                Icons.account_balance_wallet_outlined,
                '交換預算',
                () => _open(context, const BudgetScreen()),
                color: ExchangeColors.amber,
              ),
              StudentAction(
                Icons.forum_outlined,
                '同學論壇',
                () => onSelectTab(3),
                color: ExchangeColors.actionBlue,
              ),
            ]),
            const SizedBox(height: 12),
            GlassCard(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: StudentActionRow(
                icon: Icons.widgets_outlined,
                title: '桌面小工具',
                detail: '將截止日與待辦文件放在手機桌面',
                onTap: () => _open(context, const WidgetSettingsScreen()),
              ),
            ),
            const SizedBox(height: 12),
            if (account == null)
              GlassCard(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 4,
                ),
                child: StudentActionRow(
                  icon: Icons.devices_rounded,
                  title: '登入同步',
                  detail: '跨手機與電腦同步收藏、選校條件與草稿',
                  onTap: () => onSelectTab(4),
                ),
              )
            else
              const WorkspaceSyncCard(),
            if (store.isLoading)
              const Padding(
                padding: EdgeInsets.only(top: 16),
                child: LinearProgressIndicator(),
              ),
            if (store.error != null)
              Padding(
                padding: const EdgeInsets.only(top: 16),
                child: InlineError(message: '暫時無法更新', onRetry: store.refresh),
              ),
          ],
        ),
      ),
    );
  }
}

class _NextDeadlineCard extends StatelessWidget {
  const _NextDeadlineCard({required this.event, required this.onTap});

  final ApplicationCalendarEvent? event;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final next = event;
    if (next == null) {
      return GlassCard(
        padding: const EdgeInsets.all(16),
        onTap: onTap,
        child: Row(
          children: [
            const ExchangeIconBadge(
              Icons.calendar_month_outlined,
              color: ExchangeColors.secondaryInk,
              background: ExchangeColors.surfaceMuted,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '目前尚無近期截止日',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '前往申請時程查看官方公告或新增個人提醒。',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            const Icon(
              Icons.chevron_right_rounded,
              color: ExchangeColors.secondaryInk,
            ),
          ],
        ),
      );
    }

    final (sourceLabel, badgeBg, badgeFg) = switch (next.category) {
      'home' => (
        '校內官方',
        ExchangeColors.tealSoft,
        ExchangeColors.actionBlue,
      ),
      'partner' => ('合作校', ExchangeColors.amberSoft, ExchangeColors.amber),
      _ => ('個人提醒', ExchangeColors.surfaceMuted, ExchangeColors.secondaryInk),
    };
    final dateText =
        '${next.date.year}/${next.date.month.toString().padLeft(2, '0')}/${next.date.day.toString().padLeft(2, '0')}';

    return GlassCard(
      padding: const EdgeInsets.all(16),
      onTap: onTap,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 52,
            padding: const EdgeInsets.symmetric(vertical: 8),
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: ExchangeColors.amberSoft,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: ExchangeColors.amber.withValues(alpha: 0.28),
              ),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '${next.date.month}月',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: ExchangeColors.amber,
                    fontFeatures: ExchangeColors.tabularFigures,
                  ),
                ),
                Text(
                  '${next.date.day}',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: ExchangeColors.amber,
                    fontFeatures: ExchangeColors.tabularFigures,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 3,
                      ),
                      decoration: BoxDecoration(
                        color: badgeBg,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        sourceLabel,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: badgeFg,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    Text(
                      '$dateText · ${countdownLabel(next.date)}',
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: ExchangeColors.amber,
                        fontFeatures: ExchangeColors.tabularFigures,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  next.title,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
          ),
          const SizedBox(width: 4),
          const Icon(
            Icons.chevron_right_rounded,
            color: ExchangeColors.secondaryInk,
          ),
        ],
      ),
    );
  }
}

class _CompactPartnerCard extends StatelessWidget {
  const _CompactPartnerCard({required this.school, required this.onTap});

  final PartnerUniversity school;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final (badgeBg, badgeFg) = _availabilityColors(school);
    return GlassCard(
      padding: const EdgeInsets.all(14),
      onTap: onTap,
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    Text(
                      school.country,
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: ExchangeColors.actionBlue,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 7,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: badgeBg,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        school.availabilityLabel,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: badgeFg,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  school.schoolName,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 4),
                Text(
                  '名額 ${school.displayQuota} · 期限 ${school.displayDeadlineSummary}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontFeatures: ExchangeColors.tabularFigures,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          const Icon(
            Icons.chevron_right_rounded,
            color: ExchangeColors.secondaryInk,
          ),
        ],
      ),
    );
  }
}

(Color, Color) _availabilityColors(PartnerUniversity school) {
  return switch (school.availabilityStatus) {
    'open' => (ExchangeColors.successSoft, ExchangeColors.success),
    'agreement_only' => (
      ExchangeColors.referenceSoft,
      ExchangeColors.referenceInk,
    ),
    'quota_unconfirmed' || 'visiting_fee_paying' => (
      ExchangeColors.amberSoft,
      ExchangeColors.amber,
    ),
    'closed' => (ExchangeColors.coralSoft, ExchangeColors.danger),
    _ => (ExchangeColors.surfaceMuted, ExchangeColors.secondaryInk),
  };
}

class WorkspaceSyncCard extends StatelessWidget {
  const WorkspaceSyncCard({super.key});
  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final sync = store.workspaceSync;
    if (sync == null) return const SizedBox.shrink();
    final message = switch (sync.status) {
      WorkspaceSyncStatus.loading || WorkspaceSyncStatus.syncing => '同步中…',
      WorkspaceSyncStatus.saved => sync.lastSyncedAt == null ? '尚未連上雲端' : '已同步',
      WorkspaceSyncStatus.pending => '已存於手機，等待同步',
      WorkspaceSyncStatus.conflict => '有一項資料需要你確認',
      WorkspaceSyncStatus.expired => '請重新登入以繼續同步',
    };
    return _Surface(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                sync.status == WorkspaceSyncStatus.saved
                    ? Icons.cloud_done_outlined
                    : Icons.cloud_sync_outlined,
                size: 20,
                color: ExchangeColors.teal,
              ),
              const SizedBox(width: 10),
              Expanded(child: Text(message)),
              IconButton(
                tooltip: '重新同步',
                onPressed: sync.status == WorkspaceSyncStatus.syncing
                    ? null
                    : store.synchronizeWorkspace,
                icon: const Icon(Icons.refresh_rounded),
              ),
            ],
          ),
          if (sync.status == WorkspaceSyncStatus.conflict) ...[
            const Text('手機和電腦都修改了同一個欄位。其他沒有衝突的變更會一併保留。'),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              children: [
                OutlinedButton(
                  onPressed: () => _resolve(context, sync, true),
                  child: const Text('保留手機版本'),
                ),
                OutlinedButton(
                  onPressed: () => _resolve(context, sync, false),
                  child: const Text('保留雲端版本'),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _resolve(
    BuildContext context,
    WorkspaceSync sync,
    bool local,
  ) async {
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(local ? '保留手機修改？' : '保留雲端修改？'),
        content: Text(
          '只有衝突的欄位會使用${local ? '手機' : '雲端'}版本。\n${sync.conflicts.join('\n')}',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('確認'),
          ),
        ],
      ),
    );
    if (accepted == true) await sync.resolveConflict(preferLocal: local);
  }
}

class _Surface extends StatelessWidget {
  const _Surface({required this.child});
  final Widget child;
  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
    decoration: BoxDecoration(
      color: ExchangeColors.surfaceMuted,
      borderRadius: BorderRadius.circular(12),
      border: Border.all(color: ExchangeColors.line),
    ),
    child: child,
  );
}
