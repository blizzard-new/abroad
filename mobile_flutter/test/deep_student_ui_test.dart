import 'dart:convert';
import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/screens/ai_tools_screens.dart';
import 'package:exchange_guide_flutter/screens/application_document_form_screen.dart';
import 'package:exchange_guide_flutter/screens/application_documents_screen.dart';
import 'package:exchange_guide_flutter/screens/feature_screens.dart';
import 'package:exchange_guide_flutter/screens/school_detail_screen.dart';
import 'package:exchange_guide_flutter/screens/student_plan_screens.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

final deepTemplate = ApplicationDocumentTemplate.fromJson({
  'id': 'deep-ui-fixture',
  'title': '交換申請測試文件',
  'short_title': '測試文件',
  'stage': '校內申請',
  'description': '這是版面測試用的虛構內容。',
  'default_copies': 2,
  'destinations': ['測試窗口'],
  'signatures': ['申請人'],
  'stamps': ['系所'],
  'fields': [
    {
      'id': 'student_name_zh',
      'label': '姓名',
      'field_type': 'text',
      'required': true,
      'reusable_profile_key': 'student_name_zh',
    },
    {
      'id': 'email',
      'label': '聯絡信箱',
      'field_type': 'email',
      'reusable_profile_key': 'email',
    },
    {'id': 'start', 'label': '開始日期', 'field_type': 'date'},
    {
      'id': 'motivation',
      'label': '申請動機',
      'field_type': 'textarea',
      'required': true,
    },
    {'id': 'files', 'label': '證明附件', 'field_type': 'files'},
    {
      'id': 'agree',
      'label': '確認申請內容',
      'field_type': 'checkbox',
      'required': true,
    },
  ],
});

ExchangeStore deepStore() =>
    ExchangeStore(
        api: ExchangeApi(
          baseUrl: 'https://deep-ui.invalid/',
          client: MockClient((request) async {
            Object response = [];
            if (request.url.path.contains('workflow')) {
              response = {
                'steps': [
                  {
                    'order': 1,
                    'title': '準備測試申請資料',
                    'summary': '確認測試表單與附件。',
                    'details': ['保留完整說明'],
                  },
                ],
              };
            }
            if (request.url.path.contains('experiences')) {
              response = {'highlights': [], 'sources': []};
            }
            return http.Response.bytes(
              utf8.encode(jsonEncode(response)),
              200,
              headers: {'content-type': 'application/json'},
            );
          }),
        ),
      )
      ..applicationTemplates = [deepTemplate]
      ..dashboard = StudentDashboard.fromJson({
        'school_name': '測試大學',
        'partner_universities': [
          {
            'school_name': '跨國交換測試大學 International Example University',
            'country': '測試國家',
            'study_period': '一學期',
            'quota': '依公告',
            'source_url': 'https://example.invalid/official',
          },
        ],
      });

Widget deepApp(ExchangeStore store, Widget page, {double scale = 2}) =>
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
        home: page,
      ),
    );

Future<void> scrollAll(WidgetTester tester) async {
  final scroll = find.byType(Scrollable).first;
  for (var i = 0; i < 12; i++) {
    await tester.drag(scroll, const Offset(0, -420));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  }
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });
  final pages = <String, Widget>{
    'setup': const ApplicationSetupScreen(),
    'profile': const ApplicationProfileScreen(),
    'packet': const ApplicationPacketScreen(),
    'budget': const BudgetScreen(),
    'advisor': const AdvisorScreen(),
    'document check': const DocumentCheckScreen(),
    'writing': const WritingAssistantScreen(),
    'eligibility': const EligibilityScreen(),
  };
  for (final entry in pages.entries) {
    testWidgets('${entry.key} stays usable at 320px with 2x text', (
      tester,
    ) async {
      await tester.binding.setSurfaceSize(const Size(320, 800));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final store = deepStore();
      await tester.pumpWidget(deepApp(store, entry.value));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await scrollAll(tester);
      await tester.pumpWidget(const SizedBox());
      store.dispose();
    });
  }
  testWidgets(
    'form can save incomplete input from fixed actions after keyboard editing',
    (tester) async {
      await tester.binding.setSurfaceSize(const Size(360, 800));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final store = deepStore();
      await tester.pumpWidget(
        deepApp(
          store,
          ApplicationDocumentFormScreen(template: deepTemplate),
          scale: 1.4,
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('儲存草稿').hitTestable(), findsOneWidget);
      final name = find.widgetWithText(TextFormField, '姓名 *');
      await tester.scrollUntilVisible(
        name,
        240,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.enterText(name, '測試學生');
      FocusManager.instance.primaryFocus?.unfocus();
      await tester.pumpAndSettle();
      await tester.tap(find.text('儲存草稿'));
      await tester.pumpAndSettle();
      expect(store.applicationProfile['student_name_zh'], '測試學生');
      expect(
        store.applicationSelections[deepTemplate.id]?.status,
        ApplicationDocumentProgress.draft,
      );
      await scrollAll(tester);
      expect(find.text('下載 PDF').hitTestable(), findsOneWidget);
      final form = tester.widget<Form>(find.byType(Form));
      expect((form.key! as GlobalKey<FormState>).currentState, isNotNull);
      await tester.tap(find.text('下載 PDF'));
      await tester.pumpAndSettle();
      expect(find.text('請填寫申請動機'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
      store.dispose();
    },
  );
  testWidgets(
    'school detail keeps full name, all sections, sources and favorite action',
    (tester) async {
      await tester.binding.setSurfaceSize(const Size(320, 800));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final store = deepStore();
      final school = store.dashboard!.partnerUniversities.single;
      await tester.pumpWidget(
        deepApp(store, SchoolDetailScreen(school: school)),
      );
      await tester.pumpAndSettle();
      expect(find.text(school.schoolName), findsOneWidget);
      expect(find.text('官方來源').hitTestable(), findsOneWidget);
      await tester.tap(find.text('加入收藏'));
      await tester.pumpAndSettle();
      expect(store.favorites, contains(school.schoolName));
      await tester.scrollUntilVisible(
        find.widgetWithText(ChoiceChip, '流程'),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.tap(find.widgetWithText(ChoiceChip, '流程'));
      await tester.pumpAndSettle();
      await scrollAll(tester);
      for (final tab in ['生活', '心得', '社群']) {
        tester
            .state<ScrollableState>(find.byType(Scrollable).first)
            .position
            .jumpTo(0);
        await tester.pumpAndSettle();
        await tester.scrollUntilVisible(
          find.widgetWithText(ChoiceChip, tab),
          200,
          scrollable: find.byType(Scrollable).first,
        );
        await tester.pumpAndSettle();
        await tester.tap(find.widgetWithText(ChoiceChip, tab));
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull, reason: tab);
        await scrollAll(tester);
      }
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
      store.dispose();
    },
  );
}
