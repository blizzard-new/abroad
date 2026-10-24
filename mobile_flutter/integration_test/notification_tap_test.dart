// Manual Android system-UI acceptance. Opt in with NATIVE_TAP_ACCEPTANCE=true.
// Start tests/fixtures/mobile_preview_server.py and adb reverse tcp:18765 tcp:18765.
// Grant the test APK's notification permission, then tap each posted notification
// in Android's notification shade when prompted. Uses an isolated synthetic account.
import 'dart:async';
import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:exchange_guide_flutter/app.dart';
import 'package:exchange_guide_flutter/core/account_session_storage.dart';
import 'package:exchange_guide_flutter/core/mobile_notifications.dart';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/screens/deadlines_screen.dart';
import 'package:exchange_guide_flutter/screens/root_shell.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets(
    'system notification tap opens the calendar only for its account',
    (tester) async {
      const apiBase = String.fromEnvironment('API_BASE_URL');
      expect(apiBase, 'http://127.0.0.1:18765/');
      final api = ExchangeApi(baseUrl: apiBase);
      const verifier =
          'vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv';
      final response = await http.post(
        Uri.parse('${apiBase}__fixture__/handoff'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'challenge': base64Url
              .encode(sha256.convert(ascii.encode(verifier)).bytes)
              .replaceAll('=', ''),
          'state': 'sssssssssssssssssssssssssssssssssssssssssss',
        }),
      );
      expect(response.statusCode, 200);
      final handoff = Uri.parse(jsonDecode(response.body)['url'] as String);
      final login = await api.exchangeMobileCode(
        handoff.queryParameters['code']!,
        verifier,
      );
      await AccountSessionStorage(
        apiBase,
      ).save(login.accessToken, login.profile);
      await tester.pumpWidget(const ExchangeGuideApp());
      final store = ExchangeStoreScope.of(
        tester.element(find.byType(RootShell)),
        listen: false,
      );
      for (var attempt = 0; attempt < 120 && store.isLoading; attempt++) {
        await tester.pump(const Duration(milliseconds: 500));
      }
      expect(store.isLoading, isFalse);
      expect(store.account?.id, login.profile.id);
      expect(await store.enableMobileNotifications(), isTrue);

      Future<void> tapAndWait(String account) async {
        final tapped = Completer<void>();
        void targetChanged() {
          if (store.mobileNotifications.target.value?.accountId == account &&
              !tapped.isCompleted) {
            tapped.complete();
          }
        }

        store.mobileNotifications.target.addListener(targetChanged);
        try {
          await tester.runAsync(
            () => tapped.future.timeout(const Duration(minutes: 2)),
          );
        } finally {
          store.mobileNotifications.target.removeListener(targetChanged);
        }
        await tester.pumpAndSettle();
      }

      await store.mobileNotifications.testNotification(
        store.account!.id,
        store.selectedUniversity,
      );
      debugPrint('SYSTEM_TAP_READY: UniWay 通知已開啟');
      await tapAndWait(store.account!.id);
      expect(find.byType(DeadlinesScreen), findsOneWidget);
      expect(find.widgetWithText(AppBar, '申請時程'), findsOneWidget);
      expect(tester.takeException(), isNull);
      debugPrint('SYSTEM_TAP_OPENED_CALENDAR');
      Navigator.of(tester.element(find.byType(DeadlinesScreen))).pop();
      await tester.pumpAndSettle();

      await store.mobileNotifications.plugin.show(
        id: 2147483645,
        title: 'UniWay 帳號隔離測試',
        body: '點一下，確認不會開啟其他帳號的頁面。',
        notificationDetails: MobileNotifications.details,
        payload: MobileNotificationTarget(
          accountId: 'other-account',
          homeSchool: store.selectedUniversity,
        ).encode(),
      );
      debugPrint('SYSTEM_TAP_READY: UniWay 帳號隔離測試');
      await tapAndWait('other-account');
      expect(find.byType(DeadlinesScreen), findsNothing);
      expect(store.account?.id, login.profile.id);
      debugPrint('SYSTEM_TAP_ACCOUNT_ISOLATION_PASSED');
      await store.logout();
      await tester.pumpWidget(const SizedBox());
    },
    skip: !const bool.fromEnvironment('NATIVE_TAP_ACCEPTANCE'),
  );
}
