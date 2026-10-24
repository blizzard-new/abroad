import 'dart:async';
import 'dart:convert';
import 'package:exchange_guide_flutter/core/app_updates.dart';
import 'package:exchange_guide_flutter/screens/app_update_prompt.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

Map<String, dynamic> release(
  String version, {
  bool draft = false,
  String? host,
}) => {
  'tag_name': 'android-v$version-preview',
  'draft': draft,
  'published_at': '2026-10-24',
  'assets': [
    {
      'name': 'UniWay-$version-preview.apk',
      'state': 'uploaded',
      'size': 80000000,
      'browser_download_url':
          'https://${host ?? 'github.com'}/blizzard-new/abroad/releases/download/android-v$version-preview/UniWay-$version-preview.apk',
    },
  ],
};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => SharedPreferences.setMockInitialValues({}));
  test('numeric version ordering finds uploaded Android preview only', () {
    expect(
      AppRelease.newest([
        release('2.1.9'),
        release('2.1.10'),
        release('2.1.4'),
      ], '2.1.3')?.version,
      '2.1.10',
    );
    expect(
      AppRelease.newest([
        release('2.1.3'),
        release('2.1.2'),
        release('2.2.0', draft: true),
        release('3.0.0', host: 'evil.test'),
        {...release('4.0.0'), 'assets': []},
        {...release('5.0.0'), 'tag_name': 'web-v5.0.0'},
      ], '2.1.3'),
      isNull,
    );
    expect(() => AppRelease.newest({}, '2.1.3'), throwsFormatException);
  });
  test(
    'checks coalesce, throttle, retry manually, and never send account credentials',
    () async {
      var calls = 0;
      var now = DateTime(2026, 10, 24);
      final gate = Completer<http.Response>();
      final updates = AppUpdateController(
        installedVersion: () async => '2.1.3',
        clock: () => now,
        client: MockClient((request) async {
          calls++;
          expect(request.url, AppUpdateController.releasesUri);
          expect(
            request.headers.keys.map((k) => k.toLowerCase()),
            isNot(contains('authorization')),
          );
          if (calls == 1) return gate.future;
          return http.Response(jsonEncode([release('2.1.4')]), 200);
        }),
      );
      addTearDown(updates.dispose);
      final first = updates.check(), second = updates.check();
      gate.complete(http.Response(jsonEncode([release('2.1.4')]), 200));
      final results = await Future.wait([first, second]);
      expect(results.first?.version, '2.1.4');
      expect(calls, 1);
      await updates.check();
      expect(calls, 1);
      await updates.check(manual: true);
      expect(calls, 2);
      await updates.remindTomorrow(results.first!);
      expect(await updates.shouldPrompt(results.first!), false);
      now = now.add(const Duration(days: 1));
      expect(await updates.shouldPrompt(results.first!), true);
      await updates.check();
      expect(calls, 3);
    },
  );
  test('failed check backs off but manual check can recover', () async {
    var calls = 0;
    final updates = AppUpdateController(
      installedVersion: () async => '2.1.3',
      client: MockClient((_) async {
        calls++;
        return calls == 1
            ? http.Response('rate limited', 403)
            : http.Response('[]', 200);
      }),
    );
    addTearDown(updates.dispose);
    expect(await updates.check(), isNull);
    expect(updates.error, isNotNull);
    await updates.check();
    expect(calls, 1);
    await updates.check(manual: true);
    expect(calls, 2);
    expect(updates.error, isNull);
  });
  testWidgets(
    'update dialog downloads the APK and suppresses duplicate prompts',
    (tester) async {
      final updates = AppUpdateController()..version = '2.1.3';
      addTearDown(updates.dispose);
      final newer = AppRelease.newest([release('2.1.4')], '2.1.3')!;
      final opened = <Uri>[];
      late BuildContext context;
      await tester.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (c) {
              context = c;
              return const Scaffold();
            },
          ),
        ),
      );
      final dialog = showAppUpdatePrompt(
        context,
        updates,
        newer,
        openUrl: (url) async {
          opened.add(url);
          return true;
        },
      );
      await tester.pumpAndSettle();
      await showAppUpdatePrompt(context, updates, newer);
      expect(find.byType(AlertDialog), findsOneWidget);
      await tester.tap(find.text('下載更新'));
      await tester.pumpAndSettle();
      await dialog;
      expect(opened, [newer.downloadUrl]);
      expect(updates.promptOpen, false);
      expect(await updates.shouldPrompt(newer), false);
    },
  );
  testWidgets('failed browser launch retains retry and does not crash', (
    tester,
  ) async {
    final updates = AppUpdateController()..version = '2.1.3';
    addTearDown(updates.dispose);
    late BuildContext context;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (c) {
            context = c;
            return const Scaffold();
          },
        ),
      ),
    );
    final dialog = showAppUpdatePrompt(
      context,
      updates,
      AppRelease.newest([release('2.1.4')], '2.1.3')!,
      openUrl: (_) async => false,
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('下載更新'));
    await tester.pumpAndSettle();
    expect(find.text('無法開啟下載，請再試一次。'), findsOneWidget);
    await tester.tap(find.text('稍後提醒'));
    await tester.pumpAndSettle();
    await dialog;
    expect(tester.takeException(), isNull);
  });
}
