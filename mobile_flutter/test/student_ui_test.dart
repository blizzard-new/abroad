import 'dart:convert';
import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/screens/account_screen.dart';
import 'package:exchange_guide_flutter/screens/root_shell.dart';
import 'package:exchange_guide_flutter/screens/schools_screen.dart';
import 'package:exchange_guide_flutter/screens/school_detail_screen.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

ExchangeStore fixtureStore() =>
    ExchangeStore(
        api: ExchangeApi(
          baseUrl: 'https://fixture.invalid/',
          client: MockClient(
            (request) async => http.Response(
              jsonEncode(
                request.url.path.endsWith('feed') ? {'items': []} : [],
              ),
              200,
            ),
          ),
        ),
      )
      ..dashboard = StudentDashboard.fromJson({
        'school_name': '長庚大學',
        'partner_universities': [
          {'school_name': '日本測試校', 'country': '日本', 'study_period': '一學期'},
          {'school_name': '德國測試校', 'country': '德國', 'study_period': '一學期'},
        ],
      });
Widget app(ExchangeStore store, Widget page, {double scale = 1}) =>
    ExchangeStoreScope(
      store: store,
      child: MaterialApp(
        theme: buildExchangeTheme(),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(scale)),
          child: child!,
        ),
        home: Scaffold(body: page),
      ),
    );

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));
  testWidgets(
    'guide is optional, all five destinations remain reachable at 320px and 2x text',
    (tester) async {
      await tester.binding.setSurfaceSize(const Size(320, 800));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final store = fixtureStore();
      addTearDown(store.dispose);
      await tester.pumpWidget(app(store, const RootShell(), scale: 2));
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip('使用指南'));
      await tester.pumpAndSettle();
      expect(find.text('1. 找到學校'), findsOneWidget);
      await tester.ensureVisible(find.text('開始吧'));
      await tester.tap(find.text('開始吧'));
      await tester.pumpAndSettle();
      for (final tab in ['學校', '申請', '論壇', '我的', '旅程']) {
        await tester.tap(find.text(tab).last);
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull, reason: tab);
      }
      for (
        var i = 0;
        i < 8 && find.text('同學論壇').hitTestable().evaluate().isEmpty;
        i++
      ) {
        await tester.drag(find.byType(Scrollable).first, const Offset(0, -320));
        await tester.pumpAndSettle();
      }
      await tester.tap(find.text('同學論壇'));
      await tester.pumpAndSettle();
      expect(store.navigationTab, 3);
      expect(find.text('交換生論壇'), findsOneWidget);
    },
  );
  testWidgets(
    'school filters preserve real matches and bookmark works without expanding a card',
    (tester) async {
      final store = fixtureStore();
      addTearDown(store.dispose);
      await tester.pumpWidget(app(store, const SchoolsScreen()));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(ChoiceChip, '日本'));
      await tester.pumpAndSettle();
      expect(find.text('日本測試校'), findsOneWidget);
      expect(find.text('德國測試校'), findsNothing);
      await tester.tap(find.byTooltip('加入收藏'));
      await tester.pumpAndSettle();
      expect(store.favorites, contains('日本測試校'));
      expect(find.byType(SchoolDetailScreen), findsNothing);
      await tester.tap(find.widgetWithText(ChoiceChip, '全部國家'));
      await tester.tap(find.byType(FilterChip).first);
      await tester.pumpAndSettle();
      expect(find.text('德國測試校'), findsNothing);
      await tester.tap(find.text('日本測試校'));
      await tester.pumpAndSettle();
      expect(find.byType(SchoolDetailScreen), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'account university picker searches instead of rendering a chip wall',
    (tester) async {
      final store = fixtureStore()
        ..account = AccountProfile.fromJson({
          'id': 'student',
          'display_name': '同學',
          'home_university': '長庚大學',
        });
      addTearDown(store.dispose);
      store.universities = [
        SupportedUniversity.fromJson({
          'id': 'cgu',
          'school_name': '長庚大學',
          'short_name': '長庚',
        }),
        SupportedUniversity.fromJson({
          'id': 'ntpu',
          'school_name': '國立臺北大學',
          'short_name': '北大',
        }),
      ];
      await tester.pumpWidget(app(store, const AccountScreen()));
      await tester.pumpAndSettle();
      expect(find.byType(ActionChip), findsNothing);
      await tester.tap(find.text('個人設定'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.widgetWithText(TextField, '就讀大學'));
      await tester.tap(find.widgetWithText(TextField, '就讀大學'));
      await tester.pumpAndSettle();
      await tester.enterText(find.widgetWithText(TextField, '搜尋就讀大學'), '北大');
      await tester.pumpAndSettle();
      expect(find.widgetWithText(ListTile, '國立臺北大學'), findsOneWidget);
      expect(find.widgetWithText(ListTile, '長庚大學'), findsNothing);
      await tester.tap(find.widgetWithText(ListTile, '國立臺北大學'));
      await tester.pumpAndSettle();
      expect(
        store.account!.homeUniversity,
        '長庚大學',
      ); // Selection is only saved by the explicit save action.
      expect(find.text('國立臺北大學'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('Google login still requires explicit consent', (tester) async {
    final store = fixtureStore();
    addTearDown(store.dispose);
    await tester.pumpWidget(app(store, const AccountScreen()));
    await tester.pumpAndSettle();
    expect(
      tester.widget<CheckboxListTile>(find.byType(CheckboxListTile)).value,
      false,
    );
    expect(find.text('服務條款'), findsOneWidget);
    expect(find.text('隱私權政策'), findsOneWidget);
    await tester.tap(find.byType(CheckboxListTile));
    await tester.pumpAndSettle();
    expect(
      tester.widget<CheckboxListTile>(find.byType(CheckboxListTile)).value,
      true,
    );
  });
}
