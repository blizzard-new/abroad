import 'package:flutter/material.dart';

import '../core/application_calendar.dart';
import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../state/exchange_store.dart';
import '../state/workspace_sync.dart';
import 'deadlines_screen.dart';
import 'feature_screens.dart';
import 'global_community_screen.dart';
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
    return SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: store.refresh,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(22, 16, 22, 132),
          children: [
            Row(
              children: [
                const Icon(
                  Icons.blur_on_rounded,
                  color: ExchangeColors.teal,
                  size: 32,
                ),
                const SizedBox(width: 9),
                Text(
                  'UniWay',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const Spacer(),
                IconButton(
                  tooltip: '通知與提醒',
                  onPressed: () => _open(context, const NotificationScreen()),
                  icon: const Icon(Icons.notifications_none_rounded),
                ),
              ],
            ),
            const SizedBox(height: 22),
            Text(
              account == null
                  ? '你的下一站，\n從這裡開始。'
                  : '${account.displayName}，\n一步步走向交換。',
              style: Theme.of(context).textTheme.displaySmall?.copyWith(
                fontWeight: FontWeight.w800,
                height: 1.25,
                letterSpacing: -1,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              account == null
                  ? '選一個想去的地方，把準備變成每天做得到的小事。'
                  : '下一步、截止日與文件進度，都在這裡。',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: ExchangeColors.secondaryInk,
              ),
            ),
            const SizedBox(height: 18),
            Align(
              alignment: Alignment.centerLeft,
              child: ActionChip(
                avatar: const Icon(Icons.school_outlined, size: 18),
                label: Text(store.selectedUniversity),
                onPressed: () => showUniversityPickerSheet(context),
              ),
            ),
            const SizedBox(height: 14),
            if (store.error != null)
              InlineError(message: '部分內容暫時載入失敗，請重試。', onRetry: store.refresh),
            if (account != null) const WorkspaceSyncCard(),
            if (account == null) ...[
              _Surface(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(
                      Icons.devices_rounded,
                      color: ExchangeColors.teal,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      '在電腦開始，在手機接著做',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    const Text('使用原本的 Google 帳號，帶上你的收藏與申請進度。'),
                    const SizedBox(height: 18),
                    FilledButton.icon(
                      onPressed: () => onSelectTab(3),
                      icon: const Icon(Icons.arrow_forward_rounded),
                      label: const Text('登入我的交換計畫'),
                    ),
                  ],
                ),
              ),
            ] else ...[
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(22),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF087C8C), Color(0xFF16576C)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(28),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(
                          Icons.near_me_outlined,
                          color: Colors.white,
                          size: 18,
                        ),
                        SizedBox(width: 8),
                        Text('我的下一步', style: TextStyle(color: Colors.white70)),
                      ],
                    ),
                    const SizedBox(height: 18),
                    Text(
                      store.nextPlanAction,
                      style: Theme.of(context).textTheme.headlineSmall
                          ?.copyWith(
                            color: Colors.white,
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      next == null
                          ? '先建立一個確認過的日期，再開啟提醒。'
                          : '${next.title}\n${dateKey(next.date)} · ${countdownLabel(next.date)}',
                      style: const TextStyle(color: Colors.white, height: 1.6),
                    ),
                    const SizedBox(height: 20),
                    FilledButton.tonal(
                      onPressed: () {
                        if (store.planProfile == null) {
                          _open(context, const EligibilityScreen());
                        } else if (store.favorites.isEmpty) {
                          onSelectTab(1);
                        } else {
                          onSelectTab(2);
                        }
                      },
                      child: const Text('繼續準備  →'),
                    ),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 22),
            Text('把旅程慢慢準備好', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            _Surface(
              child: Column(
                children: [
                  _JourneyAction(
                    icon: Icons.travel_explore,
                    title: '找到適合我的學校',
                    subtitle: '${store.favorites.length} 所收藏 · 看條件與官方來源',
                    onTap: () => onSelectTab(1),
                  ),
                  const Divider(height: 24),
                  _JourneyAction(
                    icon: Icons.fact_check_outlined,
                    title: '準備申請文件',
                    subtitle: '檢查缺件、填寫與記錄進度',
                    onTap: () => onSelectTab(2),
                  ),
                  const Divider(height: 24),
                  _JourneyAction(
                    icon: Icons.event_available_outlined,
                    title: '安排我的申請時程',
                    subtitle: next == null ? '加入個人日期與提醒' : '下一項：${next.title}',
                    onTap: () => _open(context, const DeadlinesScreen()),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),
            _Surface(
              child: Column(
                children: [
                  _JourneyAction(
                    icon: Icons.account_balance_wallet_outlined,
                    title: '交換預算',
                    subtitle: '生活費、一次性支出與補助',
                    onTap: () => _open(context, const BudgetScreen()),
                  ),
                  const Divider(height: 24),
                  _JourneyAction(
                    icon: Icons.widgets_outlined,
                    title: '把計畫放到手機桌面',
                    subtitle: '不用打開 App，也能看到下一步',
                    onTap: () => _open(context, const WidgetSettingsScreen()),
                  ),
                  const Divider(height: 24),
                  _JourneyAction(
                    icon: Icons.forum_outlined,
                    title: '看看同學的交換經驗',
                    subtitle: '向走過這段路的人提問',
                    onTap: () => _open(
                      context,
                      GlobalCommunityScreen(
                        onOpenCguBoard: () =>
                            _open(context, const CguBoardShell()),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            if (store.isLoading)
              const Padding(
                padding: EdgeInsets.only(top: 16),
                child: LinearProgressIndicator(),
              ),
            if (store.error != null)
              Padding(
                padding: const EdgeInsets.only(top: 16),
                child: InlineError(
                  message: '目前無法更新學校資訊，請稍後重試。',
                  onRetry: store.refresh,
                ),
              ),
            const SizedBox(height: 22),
            Text(
              '學校規定以當期官方公告為準。個人進度是你的準備紀錄。',
              style: Theme.of(context).textTheme.bodySmall,
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
      WorkspaceSyncStatus.loading || WorkspaceSyncStatus.syncing => '正在與電腦同步…',
      WorkspaceSyncStatus.saved =>
        sync.lastSyncedAt == null ? '尚未連上雲端' : '已同步到同一個帳號',
      WorkspaceSyncStatus.pending => '手機變更已保留，等待同步',
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
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(26),
      border: Border.all(color: const Color(0xFFE3ECEC)),
    ),
    child: child,
  );
}

class _JourneyAction extends StatelessWidget {
  const _JourneyAction({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => InkWell(
    onTap: onTap,
    borderRadius: BorderRadius.circular(12),
    child: Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, color: ExchangeColors.teal),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 4),
                Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
          const SizedBox(width: 6),
          const Icon(Icons.chevron_right_rounded, size: 20),
        ],
      ),
    ),
  );
}
