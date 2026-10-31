import 'package:flutter/material.dart';
import '../core/application_calendar.dart';
import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
import '../core/uniway_brand.dart';
import '../core/school_visuals.dart';
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
    final events =
        store.personalCalendarEvents
            .where((e) => !dateOnly(e.date).isBefore(dateOnly(DateTime.now())))
            .toList()
          ..sort((a, b) => a.date.compareTo(b.date));
    final next = events.firstOrNull;
    final schools = store.dashboard?.partnerUniversities ?? [];
    final savedSchools = schools
        .where((s) => store.favorites.contains(s.schoolName))
        .toList();
    final destinations = (savedSchools.isEmpty ? schools : savedSchools)
        .take(5)
        .toList();
    final nextTitle = store.planProfile == null
        ? '設定交換條件'
        : store.favorites.isEmpty
        ? '收藏第一所學校'
        : '準備申請文件';
    void continueJourney() {
      if (account == null ||
          (store.planProfile != null && store.favorites.isEmpty)) {
        onSelectTab(1);
      } else if (store.planProfile == null) {
        _open(context, const EligibilityScreen());
      } else {
        onSelectTab(2);
      }
    }

    return SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: store.refresh,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(24, 12, 24, 112),
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
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: Text(
                    account == null ? '把下一站，\n變成你的日常。' : '你的交換旅程，\n正在成形。',
                    style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                      height: 1.25,
                      letterSpacing: -.8,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerLeft,
              child: ActionChip(
                avatar: const Icon(Icons.school_outlined, size: 16),
                label: Text(store.selectedUniversity),
                tooltip: '切換就讀大學',
                onPressed: () => showUniversityPickerSheet(context),
              ),
            ),
            const SizedBox(height: 24),
            GlassCard(
              tint: ExchangeColors.tealSoft,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final compact =
                          constraints.maxWidth < 280 ||
                          MediaQuery.textScalerOf(context).scale(16) >= 24;
                      final content = Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const UniWayPill(
                            '交換準備中',
                            icon: Icons.flight_takeoff_rounded,
                            background: Colors.white,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            account == null ? '世界很大，\n從心動開始。' : nextTitle,
                            style: Theme.of(
                              context,
                            ).textTheme.headlineMedium?.copyWith(height: 1.28),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            account == null ? '找到你的第一所交換學校' : '你的下一步',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      );
                      return compact
                          ? Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Align(
                                  alignment: Alignment.centerRight,
                                  child: UniWayMascot(size: 88),
                                ),
                                content,
                              ],
                            )
                          : Row(
                              children: [
                                Expanded(child: content),
                                const SizedBox(width: 8),
                                const UniWayMascot(size: 112),
                              ],
                            );
                    },
                  ),
                  const SizedBox(height: 20),
                  FilledButton(
                    onPressed: continueJourney,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Flexible(
                          child: Text(account == null ? '探索學校' : '繼續準備'),
                        ),
                        const SizedBox(width: 12),
                        const Icon(Icons.arrow_forward_rounded, size: 20),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            LayoutBuilder(
              builder: (context, constraints) => Wrap(
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
                      count: '${store.applicationFormReadyCount}',
                      label: '完成文件',
                      tab: 2,
                    ),
                  ])
                    SizedBox(
                      width: (constraints.maxWidth - 12) / 2,
                      child: GlassCard(
                        padding: const EdgeInsets.all(20),
                        onTap: () => onSelectTab(item.tab),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(
                              item.icon,
                              color: ExchangeColors.teal,
                              size: 24,
                            ),
                            const SizedBox(height: 12),
                            Text(
                              item.count,
                              style: Theme.of(context).textTheme.headlineMedium,
                            ),
                            Text(
                              item.label,
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 28),
            ExchangeSectionHeader(
              title: savedSchools.isEmpty ? '下一站，想去哪裡？' : '你的心動清單',
              action: TextButton(
                onPressed: () => onSelectTab(1),
                child: const Text('查看全部'),
              ),
            ),
            const SizedBox(height: 12),
            if (destinations.isNotEmpty)
              SizedBox(
                height:
                    264 +
                    (MediaQuery.textScalerOf(context).scale(16) - 16).clamp(
                          0,
                          30,
                        ) *
                        3,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: destinations.length,
                  separatorBuilder: (_, _) => const SizedBox(width: 16),
                  itemBuilder: (context, i) {
                    final school = destinations[i];
                    return SizedBox(
                      width: 240,
                      child: GlassCard(
                        padding: EdgeInsets.zero,
                        onTap: () =>
                            _open(context, SchoolDetailScreen(school: school)),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SizedBox(
                              height: 148,
                              width: double.infinity,
                              child: SchoolPhoto(school: school),
                            ),
                            Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    school.country,
                                    style: Theme.of(context)
                                        .textTheme
                                        .labelMedium
                                        ?.copyWith(color: ExchangeColors.teal),
                                  ),
                                  const SizedBox(height: 6),
                                  Text(
                                    school.schoolName,
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                    style: Theme.of(
                                      context,
                                    ).textTheme.titleMedium,
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
            if (destinations.isEmpty)
              GlassCard(
                child: StudentActionRow(
                  icon: Icons.travel_explore_rounded,
                  title: '尋找交換學校',
                  detail: '依你的母校查看合作學校',
                  onTap: () => onSelectTab(1),
                ),
              ),
            const SizedBox(height: 28),
            const ExchangeSectionHeader(title: '重要的事，幫你記著'),
            const SizedBox(height: 12),
            GlassCard(
              padding: const EdgeInsets.all(20),
              onTap: () => _open(context, const DeadlinesScreen()),
              child: Row(
                children: [
                  Container(
                    width: 52,
                    height: 60,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: ExchangeColors.coralSoft,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: next == null
                        ? const Icon(
                            Icons.calendar_month_rounded,
                            color: ExchangeColors.coral,
                          )
                        : Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                '${next.date.month} 月',
                                style: Theme.of(context).textTheme.labelMedium
                                    ?.copyWith(color: ExchangeColors.coral),
                              ),
                              Text(
                                '${next.date.day}',
                                style: Theme.of(context).textTheme.titleLarge
                                    ?.copyWith(color: ExchangeColors.coral),
                              ),
                            ],
                          ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          next?.title ?? '加入下一個期限',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          next == null ? '行事曆與到期提醒' : countdownLabel(next.date),
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
            ),
            const SizedBox(height: 28),
            const ExchangeSectionHeader(title: '出發工具箱'),
            const SizedBox(height: 12),
            StudentActionGrid([
              StudentAction(
                Icons.account_balance_wallet_outlined,
                '交換預算',
                () => _open(context, const BudgetScreen()),
                color: ExchangeColors.coral,
              ),
              StudentAction(
                Icons.forum_outlined,
                '同學論壇',
                () => onSelectTab(3),
                color: ExchangeColors.blue,
              ),
              StudentAction(
                Icons.widgets_outlined,
                '桌面小工具',
                () => _open(context, const WidgetSettingsScreen()),
              ),
              StudentAction(
                Icons.notifications_none_rounded,
                '通知提醒',
                () => _open(context, const NotificationScreen()),
                color: ExchangeColors.amber,
              ),
            ]),
            const SizedBox(height: 24),
            if (account == null)
              StudentActionRow(
                icon: Icons.devices_rounded,
                title: '登入同步',
                detail: '手機、電腦接著準備',
                onTap: () => onSelectTab(4),
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
      borderRadius: BorderRadius.circular(26),
      border: Border.all(color: ExchangeColors.line),
    ),
    child: child,
  );
}
