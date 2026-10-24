import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:exchange_guide_flutter/core/app_updates.dart';
import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/core/mobile_login.dart';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/screens/app_update_prompt.dart';
import 'package:exchange_guide_flutter/screens/forum_screen.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:integration_test/integration_test.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:path_provider/path_provider.dart';

Future<void> waitForComposerClose(WidgetTester tester) async {
  for (
    var i = 0;
    i < 100 && find.byType(ForumComposer).evaluate().isNotEmpty;
    i++
  ) {
    await tester.pump(const Duration(milliseconds: 200));
  }
  expect(
    find.byType(ForumComposer),
    findsNothing,
    reason: tester
        .widgetList<Text>(find.byType(Text))
        .map((t) => t.data)
        .join(' | '),
  );
  await tester.pumpAndSettle();
}

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets(
    'native forum writes share the Web API and native update prompt opens APK',
    (tester) async {
      const base = 'http://127.0.0.1:18765/';
      const verifier =
          'vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv';
      const state = 'sssssssssssssssssssssssssssssssssssssssssss';
      await const FlutterSecureStorage().write(
        key: 'mobile_login:${Uri.encodeComponent(base)}',
        value: jsonEncode({
          'verifier': verifier,
          'state': state,
          'expires_at': DateTime.now()
              .add(const Duration(minutes: 5))
              .toIso8601String(),
        }),
      );
      final handoff = await http.post(
        Uri.parse('${base}__fixture__/handoff'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'challenge': base64Url
              .encode(sha256.convert(ascii.encode(verifier)).bytes)
              .replaceAll('=', ''),
          'state': state,
        }),
      );
      expect(handoff.statusCode, 200);
      final api = ExchangeApi(baseUrl: base);
      final login = await MobileLogin(
        api,
      ).complete(Uri.parse(jsonDecode(handoff.body)['url'] as String));
      final store = ExchangeStore(api: api)
        ..account = login!.profile
        ..accessToken = login.accessToken;
      addTearDown(store.dispose);
      expect(store.account!.emailVerified, true);
      await tester.pumpWidget(
        ExchangeStoreScope(
          store: store,
          child: MaterialApp(
            theme: buildExchangeTheme(),
            home: const Scaffold(body: ForumScreen()),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('發起討論'));
      await tester.pumpAndSettle();
      final suffix = DateTime.now().millisecondsSinceEpoch
          .toString()
          .split('')
          .map((digit) => '零一二三四五六七八九'[int.parse(digit)])
          .join();
      final title = '交換住宿測試$suffix';
      await tester.enterText(find.widgetWithText(TextField, '標題'), title);
      await tester.enterText(
        find.widgetWithText(TextField, '討論內容'),
        '這是隔離測試服務的住宿申請經驗，沒有寫入正式站。',
      );
      FocusManager.instance.primaryFocus?.unfocus();
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('送出'));
      await tester.tap(find.text('送出'));
      await waitForComposerClose(tester);
      final web = ExchangeApi(baseUrl: base);
      final feed = await web.forumFeed(login.accessToken, query: title);
      expect(feed.items.single.title, title);
      await binding.convertFlutterSurfaceToImage();
      await tester.pumpAndSettle();
      final folder = await getApplicationDocumentsDirectory();
      await File(
        '${folder.path}/forum-preview.png',
      ).writeAsBytes(await binding.takeScreenshot('forum-preview'));
      await tester.ensureVisible(find.text(title));
      await tester.tap(find.text(title));
      await tester.pumpAndSettle();
      await tester.tap(find.text('回覆文章'));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.widgetWithText(TextField, '回覆內容'),
        '同學你好，我也正在準備宿舍申請。',
      );
      FocusManager.instance.primaryFocus?.unfocus();
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('送出'));
      await tester.tap(find.text('送出'));
      await waitForComposerClose(tester);
      final comments = await web.forumReplies(
        login.accessToken,
        feed.items.single.id,
      );
      expect(comments.items.single.body, contains('宿舍申請'));
      final info = await PackageInfo.fromPlatform();
      expect(info.version, '2.1.3');
      expect(info.buildNumber, '17');
      final updates = AppUpdateController()..version = info.version;
      addTearDown(updates.dispose);
      final next = AppRelease(
        '2.1.4',
        Uri.parse(
          'https://github.com/blizzard-new/abroad/releases/download/android-v2.1.4-preview/UniWay-2.1.4-preview.apk',
        ),
        Uri.parse(
          'https://github.com/blizzard-new/abroad/releases/tag/android-v2.1.4-preview',
        ),
        80000000,
      );
      Uri? opened;
      final dialog = showAppUpdatePrompt(
        tester.element(find.byType(ForumPostScreen)),
        updates,
        next,
        openUrl: (url) async {
          opened = url;
          return true;
        },
      );
      await tester.pumpAndSettle();
      await File(
        '${folder.path}/update-preview.png',
      ).writeAsBytes(await binding.takeScreenshot('update-preview'));
      await tester.tap(find.text('下載更新'));
      await tester.pumpAndSettle();
      await dialog;
      expect(opened, next.downloadUrl);
      await api.deleteForum(
        login.accessToken,
        await store.ensureIdentity(),
        feed.items.single.id,
      );
      expect(tester.takeException(), isNull);
    },
  );
}
