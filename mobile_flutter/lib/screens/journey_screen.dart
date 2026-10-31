import 'package:flutter/material.dart';

import '../core/application_calendar.dart';
import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
import '../core/journey_illustration.dart';
import '../state/exchange_store.dart';
import '../state/workspace_sync.dart';
import 'deadlines_screen.dart';
import 'feature_screens.dart';
import 'notification_screen.dart';
import 'root_shell.dart';
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
          padding: const EdgeInsets.fromLTRB(24, 12, 24, 128),
          children: [
            Row(
              children: [
                const Icon(
                  Icons.explore_rounded,
                  color: ExchangeColors.teal,
                  size: 28,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'UniWay',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ),
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
            Text(
              account == null ? '下一站，世界。' : '一步步，準備出發。',
              style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                fontSize: 28,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              '從選校到出發，把準備留在這裡。',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerLeft,
              child: ActionChip(
                avatar: const Icon(Icons.school_outlined, size: 18),
                label: Text(store.selectedUniversity),
                tooltip: '切換就讀大學',
                onPressed: () => showUniversityPickerSheet(context),
              ),
            ),
            const SizedBox(height: 20),
            GlassCard(
              tint: ExchangeColors.tealSoft,
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const StudentIconLabel(
                              Icons.flight_takeoff_rounded,
                              '你的下一步',
                              color: ExchangeColors.teal,
                            ),
                            const SizedBox(height: 12),
                            Text(
                              account == null ? '從一所心動的\n學校開始' : nextTitle,
                              style: Theme.of(context).textTheme.headlineMedium,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              account == null ? '探索適合你的交換學校' : '今天，完成一件事就好。',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ),
                      if (MediaQuery.sizeOf(context).width >= 360 &&
                          MediaQuery.textScalerOf(context).scale(16) < 24) ...[
                        const SizedBox(width: 8),
                        const JourneyIllustration(),
                      ],
                    ],
                  ),
                  const SizedBox(height: 20),
                  FilledButton.icon(
                    onPressed: continueJourney,
                    icon: Icon(
                      account == null
                          ? Icons.travel_explore_rounded
                          : Icons.arrow_forward_rounded,
                    ),
                    label: Text(account == null ? '探索學校' : '繼續準備'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            StudentHeading(
              '我的準備',
              action: IconButton(
                tooltip: '查看申請時程',
                onPressed: () => _open(context, const DeadlinesScreen()),
                icon: const Icon(Icons.calendar_month_outlined),
              ),
            ),
            const SizedBox(height: 12),
            GlassCard(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Column(
                children: [
                  StudentActionRow(
                    icon: Icons.bookmark_border_rounded,
                    title: '學校清單',
                    detail: store.favorites.isEmpty
                        ? '先收藏，再比較'
                        : '${store.favorites.length} 所收藏',
                    onTap: () => onSelectTab(1),
                  ),
                  const Divider(indent: 56),
                  StudentActionRow(
                    icon: Icons.task_alt_rounded,
                    title: '申請文件',
                    detail: '${store.applicationFormReadyCount} 份完成',
                    onTap: () => onSelectTab(2),
                  ),
                  const Divider(indent: 56),
                  StudentActionRow(
                    icon: Icons.event_outlined,
                    title: next == null ? '加入下一個期限' : next.title,
                    detail: next == null
                        ? '把重要日期留在這裡'
                        : '${dateKey(next.date)} · ${countdownLabel(next.date)}',
                    onTap: () => _open(context, const DeadlinesScreen()),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            const StudentHeading('出發工具箱'),
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
            const SizedBox(height: 20),
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
