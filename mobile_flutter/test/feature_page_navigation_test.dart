import 'dart:convert';

import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/core/student_plan.dart';
import 'package:exchange_guide_flutter/core/study_plan_widget_service.dart';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/screens/journey_screen.dart';
import 'package:exchange_guide_flutter/screens/root_shell.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _NoopWidgetBridge implements StudyPlanWidgetBridge {
  @override
  Future<void> initialize() async {}

  @override
  Future<void> sync(StudyPlanWidgetSnapshot snapshot) async {}

  @override
  Future<bool> canRequestPin() async => false;

  @override
  Future<void> requestPin({
    StudyPlanWidgetStyle style = StudyPlanWidgetStyle.overview,
  }) async {}
}

ExchangeStore _workflowStore() {
  final futureYear = DateTime.now().year + 1;
  return ExchangeStore(
      widgetBridge: _NoopWidgetBridge(),
      api: ExchangeApi(
        baseUrl: 'https://workflow.invalid/',
        client: MockClient((request) async {
          if (request.url.path.endsWith('/feed')) {
            return http.Response(jsonEncode({'items': []}), 200);
          }
          if (request.url.path.contains('application-documents/templates')) {
            return http.Response(jsonEncode({'templates': []}), 200);
          }
          return http.Response('[]', 200);
        }),
      ),
    )
    ..dashboard = StudentDashboard.fromJson({
      'school_name': '長庚大學',
      'last_checked': '2026-07-18',
      'application_periods': [
        {
          'title': '春季班校內報名截止',
          'details': ['$futureYear/03/15 下午五點前送達國際處'],
        },
      ],
      'partner_universities': [
        {
          'school_name': '東京工業大學',
          'country': '日本',
          'availability_status': 'open',
          'colleges': '工學院、管理學院',
          'degree_levels': '大學部、研究所',
          'quota': '2 名',
          'application_deadline': '$futureYear/02/20',
          'language_requirement': 'TOEIC 750',
          'language_conditions': [
            {'test': 'toeic', 'minimum_score': 750},
          ],
        },
        {
          'school_name': '京都工藝纖維大學',
          'country': '日本',
          'availability_status': 'agreement_only',
          'availability_note': '僅列姐妹校協議，本期未公告名額',
          'quota_status': 'not_listed',
          'application_window_status': 'not_announced',
          'colleges': '工學院',
          'degree_levels': '大學部',
        },
      ],
    });
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  void setPhoneViewport(WidgetTester tester) {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
  }

  testWidgets(
    'JourneyScreen surfaces official deadlines and opens feature pages without AI copy',
    (tester) async {
      setPhoneViewport(tester);
      final store = _workflowStore();
      addTearDown(store.dispose);

      await tester.pumpWidget(
        ExchangeStoreScope(
          store: store,
          child: MaterialApp(
            theme: buildExchangeTheme(),
            home: Scaffold(body: JourneyScreen(onSelectTab: (_) {})),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('交換準備總覽'), findsOneWidget);
      expect(find.text('申請顧問'), findsNothing);

      await tester.scrollUntilVisible(
        find.textContaining('春季班校內報名截止'),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();
      expect(find.text('下一個重要期限'), findsOneWidget);
      expect(find.text('校內官方'), findsOneWidget);
      expect(find.textContaining('春季班校內報名截止'), findsOneWidget);

      await tester.scrollUntilVisible(
        find.text('補助資訊'),
        280,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.ensureVisible(find.text('補助資訊'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('補助資訊'));
      await tester.pumpAndSettle();

      expect(find.text('補助資訊'), findsWidgets);
      expect(find.byTooltip('返回'), findsOneWidget);
      expect(find.text('目前沒有補助資料'), findsOneWidget);
    },
  );

  testWidgets(
    'searchable 71-university picker filters by alias and updates selectedUniversity',
    (tester) async {
      setPhoneViewport(tester);
      final store = _workflowStore();
      addTearDown(store.dispose);

      await tester.pumpWidget(
        ExchangeStoreScope(
          store: store,
          child: MaterialApp(
            theme: buildExchangeTheme(),
            home: const RootShell(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const ValueKey('journey-university-switcher')));
      await tester.pumpAndSettle();

      expect(find.text('切換就讀學校（71 校）'), findsOneWidget);
      await tester.enterText(
        find.byKey(const ValueKey('university-picker-search')),
        '台大',
      );
      await tester.pumpAndSettle();

      expect(find.text('國立臺灣大學'), findsOneWidget);
      await tester.tap(find.text('國立臺灣大學'));
      await tester.pumpAndSettle();

      expect(store.selectedUniversity, '國立臺灣大學');
    },
  );

  testWidgets(
    'guest conditions, open-only filter, 2-school compare sheet, and 1-tap target bridge work end-to-end',
    (tester) async {
      setPhoneViewport(tester);
      final store = _workflowStore();
      addTearDown(store.dispose);

      await store.savePlanProfile(
        const StudentPlanProfile(
          college: '工學院',
          degreeLevel: '大學部',
          academicScore: 85,
          languageTest: 'toeic',
          languageScore: 820,
          targetTerm: '2027 春季',
          preferredCountry: '',
          monthlyBudget: null,
          needsScholarship: false,
        ),
      );

      await tester.pumpWidget(
        ExchangeStoreScope(
          store: store,
          child: MaterialApp(
            theme: buildExchangeTheme(),
            home: const RootShell(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Switch to Schools tab
      await tester.tap(find.byKey(const ValueKey('main-tab-1')));
      await tester.pumpAndSettle();

      // Guest conditions bar shows saved conditions; open school gets match, agreement_only shows 合作備查
      expect(find.textContaining('工學院 · 大學部'), findsOneWidget);
      expect(find.text('本期開放'), findsOneWidget);
      expect(find.text('合作備查'), findsOneWidget);
      expect(find.textContaining('已知條件初步相符'), findsOneWidget);

      // Toggle 僅看本期開放 hides agreement_only school
      await tester.tap(find.byKey(const ValueKey('filter-open-only')));
      await tester.pumpAndSettle();
      expect(find.text('東京工業大學'), findsOneWidget);
      expect(find.text('京都工藝纖維大學'), findsNothing);

      // Un-toggle open-only, add both schools to compare tray, open compare sheet
      await tester.tap(find.byKey(const ValueKey('filter-open-only')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('compare-toggle-東京工業大學')));
      await tester.pumpAndSettle();
      await tester.drag(find.byType(CustomScrollView), const Offset(0, -240));
      await tester.pumpAndSettle();
      await tester.ensureVisible(
        find.byKey(const ValueKey('compare-toggle-京都工藝纖維大學')),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('compare-toggle-京都工藝纖維大學')));
      await tester.pumpAndSettle();

      expect(find.text('已選 2 / 4 間比較'), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('open-compare-sheet')));
      await tester.pumpAndSettle();
      expect(find.text('合作校並排比較（2/4 間）'), findsOneWidget);

      // Select target school directly from compare sheet -> switches to Application tab (tab 2)
      await tester.tap(find.text('設為目標校').first);
      await tester.pumpAndSettle();

      expect(store.navigationTab, 2);
      expect(store.applicationContext.targetSchool, '東京工業大學');
      expect(store.applicationProfile['college'], '工學院');
      expect(find.text('申請文件'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
