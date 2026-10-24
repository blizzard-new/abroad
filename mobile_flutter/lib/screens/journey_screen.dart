import 'package:flutter/material.dart';

import '../core/application_calendar.dart';
import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
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
    return SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: store.refresh,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 128),
          children: [
            Row(
              children: [
                const Icon(
                  Icons.blur_on_rounded,
                  color: ExchangeColors.teal,
                  size: 32,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'UniWay',
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
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
            const SizedBox(height: 24),
            GlassCard(
              tint: ExchangeColors.tealSoft,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      const Icon(
                        Icons.flight_takeoff_rounded,
                        color: ExchangeColors.teal,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          account == null ? '準備出發' : '下一步',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    account == null ? '開始你的交換' : nextTitle,
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 16),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: ActionChip(
                      avatar: const Icon(Icons.school_outlined, size: 20),
                      label: Text(store.selectedUniversity),
                      tooltip: '切換就讀大學',
                      onPressed: () => showUniversityPickerSheet(context),
                    ),
                  ),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    icon: const Icon(Icons.arrow_forward_rounded),
                    label: Text(account == null ? '探索學校' : '繼續準備'),
                    onPressed: () {
                      if (account == null ||
                          (store.planProfile != null &&
                              store.favorites.isEmpty)) {
                        onSelectTab(1);
                      } else if (store.planProfile == null) {
                        _open(context, const EligibilityScreen());
                      } else {
                        onSelectTab(2);
                      }
                    },
                  ),
                ],
              ),
            ),
            if (account == null) ...[
              const SizedBox(height: 12),
              StudentActionRow(
                icon: Icons.devices_rounded,
                title: '登入同步',
                detail: '沿用電腦版 Google 帳號',
                onTap: () => onSelectTab(4),
              ),
            ] else ...[
              const SizedBox(height: 12),
              const WorkspaceSyncCard(),
            ],
            const SizedBox(height: 24),
            const StudentHeading('準備路線'),
            const SizedBox(height: 12),
            GlassCard(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Column(
                children: [
                  StudentActionRow(
                    icon: Icons.travel_explore_rounded,
                    title: '1  找學校',
                    detail: '${store.favorites.length} 所收藏',
                    onTap: () => onSelectTab(1),
                  ),
                  const Divider(),
                  StudentActionRow(
                    icon: Icons.assignment_outlined,
                    title: '2  備文件',
                    detail: '${store.applicationFormReadyCount} 份完成',
                    onTap: () => onSelectTab(2),
                  ),
                  const Divider(),
                  StudentActionRow(
                    icon: Icons.event_available_outlined,
                    title: '3  排時程',
                    detail: next == null
                        ? '加入申請日期'
                        : '${dateKey(next.date)} · ${countdownLabel(next.date)}',
                    onTap: () => _open(context, const DeadlinesScreen()),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            const StudentHeading('常用工具'),
            const SizedBox(height: 12),
            StudentActionGrid([
              StudentAction(
                Icons.account_balance_wallet_outlined,
                '交換預算',
                () => _open(context, const BudgetScreen()),
              ),
              StudentAction(
                Icons.notifications_none_rounded,
                '通知提醒',
                () => _open(context, const NotificationScreen()),
                color: ExchangeColors.blue,
              ),
              StudentAction(
                Icons.widgets_outlined,
                '桌面小工具',
                () => _open(context, const WidgetSettingsScreen()),
                color: ExchangeColors.blue,
              ),
              StudentAction(Icons.forum_outlined, '同學論壇', () => onSelectTab(3)),
            ]),
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
      color: Colors.white,
      borderRadius: BorderRadius.circular(26),
      border: Border.all(color: const Color(0xFFE3ECEC)),
    ),
    child: child,
  );
}
