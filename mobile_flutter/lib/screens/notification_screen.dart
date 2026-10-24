import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
import '../core/remote_push.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import 'account_screen.dart';
import 'deadlines_screen.dart';
import 'feature_screens.dart' show FeaturePageScaffold;

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({super.key, this.initialNotificationId = ''});
  final String initialNotificationId;
  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  List<JsonMap> items = [];
  String? error;
  bool loading = false;
  String? accountId;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final account = ExchangeStoreScope.of(context).account?.id;
    if (accountId != account) {
      accountId = account;
      items = [];
      if (account != null) _load();
    }
  }

  Future<void> _load() async {
    final store = ExchangeStoreScope.of(context, listen: false);
    final expected = store.account?.id;
    if (expected == null) return;
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final result = await store.api.notifications(store.accessToken);
      if (mounted && store.account?.id == expected) {
        setState(() => items = jsonMapList(result['items']));
      }
    } catch (_) {
      if (mounted && store.account?.id == expected) {
        setState(() => error = '暫時無法取得通知，請稍後重試。');
      }
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> _open(JsonMap item) async {
    final store = ExchangeStoreScope.of(context, listen: false);
    try {
      await store.api.readNotification(
        store.accessToken,
        textValue(item['id']),
      );
      if (!mounted) return;
      final action = textValue(item['action_url']);
      final uri = Uri.tryParse(store.api.resolveUrl(action));
      final origin = Uri.parse(store.api.baseUrl);
      if (uri != null &&
          uri.scheme == 'https' &&
          uri.host == origin.host &&
          action.isNotEmpty) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      } else {
        await Navigator.of(
          context,
        ).push(MaterialPageRoute(builder: (_) => const DeadlinesScreen()));
      }
      await _load();
    } catch (_) {
      if (mounted) setState(() => error = '目前無法開啟通知，請重試。');
    }
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final account = store.account;
    return FeaturePageScaffold(
      title: '通知與提醒',
      onRefresh: _load,
      children: [
        if (account == null) ...[
          const StudentEmptyState(
            icon: Icons.notifications_none_rounded,
            title: '登入查看提醒',
            detail: '申請日期與通知，集中在這裡。',
          ),
          FilledButton(
            onPressed: () => Navigator.of(
              context,
            ).push(MaterialPageRoute(builder: (_) => const AccountScreen())),
            child: const Text('登入帳號'),
          ),
        ] else ...[
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('手機提醒', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                const StudentIconLabel(
                  Icons.schedule_rounded,
                  '提醒日 09:00 · 依系統排程',
                ),
                const SizedBox(height: 8),
                Text(
                  !remotePushConfigured
                      ? '規定推播尚未啟用'
                      : store.remotePush.error ??
                            (store.remotePush.registered
                                ? '規定推播已連接'
                                : '開啟提醒以連接規定推播'),
                ),
                const SizedBox(height: 12),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('開啟申請提醒'),
                  value: store.mobileNotifications.enabled,
                  onChanged: (value) async {
                    if (value) {
                      final granted = await store.enableMobileNotifications();
                      if (context.mounted && !granted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('通知尚未開啟，可到手機設定允許 UniWay 通知。'),
                          ),
                        );
                      }
                    } else {
                      await store.disableMobileNotifications();
                    }
                    if (mounted) setState(() {});
                  },
                ),
                OutlinedButton.icon(
                  onPressed: store.mobileNotifications.enabled
                      ? () => store.mobileNotifications.testNotification(
                          account.id,
                          store.selectedUniversity,
                        )
                      : null,
                  icon: const Icon(Icons.notifications_active_outlined),
                  label: const Text('測試通知'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 22),
          Text('我的通知', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          if (loading) const LinearProgressIndicator(),
          if (error != null) InlineError(message: error!, onRetry: _load),
          if (!loading && error == null && items.isEmpty)
            const StudentEmptyState(
              icon: Icons.notifications_none_rounded,
              title: '目前沒有新通知',
            ),
          ...items.map(
            (item) => Card(
              child: ListTile(
                selected: textValue(item['id']) == widget.initialNotificationId,
                leading: Icon(
                  item['read_at'] == null
                      ? Icons.mark_email_unread_outlined
                      : Icons.drafts_outlined,
                ),
                title: Text(textValue(item['title'])),
                subtitle: Text(textValue(item['body'])),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => _open(item),
              ),
            ),
          ),
        ],
      ],
    );
  }
}
