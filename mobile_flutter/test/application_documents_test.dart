import 'dart:convert';
import 'dart:typed_data';

import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/screens/application_documents_screen.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  final template = ApplicationDocumentTemplate.fromJson({
    'id': 'study-plan',
    'title': '交換學生讀書計畫',
    'short_title': '讀書計畫',
    'category': '校內表單',
    'stage': '校內申請',
    'description': '說明交換動機、課程安排與返國規劃。',
    'fields': [
      {
        'id': 'student_name_zh',
        'label': '中文姓名',
        'field_type': 'text',
        'required': true,
        'reusable_profile_key': 'student_name_zh',
        'help_text': '請填寫與校務系統相同的姓名。',
      },
      {
        'id': 'motivation',
        'label': '申請動機',
        'field_type': 'textarea',
        'required': true,
        'max_length': 2000,
      },
    ],
    'default_copies': 3,
    'destinations': ['國際處'],
    'signatures': ['申請人'],
    'stamps': ['系所主管'],
    'program_types': ['exchange'],
    'condition_flags': [],
    'official_layout': true,
    'official_form_number': 'CGU-EX-01',
    'source_url': 'https://www.cgu.edu.tw/oia',
    'source_checked_at': '2026-07-18T00:00:00+08:00',
    'version': '2026-07-18',
  });

  test('application template and file payload retain official metadata', () {
    expect(template.officialLayout, isTrue);
    expect(template.officialFormNumber, 'CGU-EX-01');
    expect(template.fields.last.kind, ApplicationFieldKind.textarea);
    expect(template.defaultCopies, 3);

    final upload = ApplicationUpload(
      name: 'admission.pdf',
      mimeType: 'application/pdf',
      bytes: Uint8List.fromList([37, 80, 68, 70]),
    );
    expect(
      upload.toJson()['data_url'],
      startsWith('data:application/pdf;base64,'),
    );
  });

  test('API requests conditional templates and returns PDF bytes', () async {
    final client = MockClient((request) async {
      if (request.url.path.endsWith('/application-center/templates')) {
        expect(request.url.queryParameters['program_type'], 'exchange');
        expect(request.url.queryParameters['flags'], 'subsidy');
        return http.Response(
          jsonEncode([_templateJson(template)]),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      if (request.url.path.endsWith('/application-center/pdf')) {
        expect(request.method, 'POST');
        expect(jsonDecode(request.body)['selections'], isNotEmpty);
        return http.Response.bytes(
          Uint8List.fromList([37, 80, 68, 70]),
          200,
          headers: {'content-type': 'application/pdf'},
        );
      }
      return http.Response('Not found', 404);
    });
    final api = ExchangeApi(client: client, baseUrl: 'https://example.test/');

    final templates = await api.applicationTemplates(
      programType: 'exchange',
      flags: const ['subsidy'],
    );
    expect(templates.single.shortTitle, '讀書計畫');

    final pdf = await api.applicationPacketPdf({
      'context': const ApplicationCenterContext().toJson(),
      'profile': {},
      'answers': {},
      'selections': [
        {'template_id': 'study-plan', 'copies': 1},
      ],
    });
    expect(pdf, [37, 80, 68, 70]);
  });

  test(
    'shared profile is reused and a saved form joins the print packet',
    () async {
      SharedPreferences.setMockInitialValues({});
      final store = ExchangeStore(
        api: ExchangeApi(
          client: MockClient((_) async => http.Response('[]', 200)),
          baseUrl: 'https://example.test/',
        ),
      )..applicationTemplates = [template];

      expect(store.applicationTemplateCompletion(template).percent, 0);
      await store.saveApplicationProfile({'student_name_zh': '王小明'});
      expect(store.applicationTemplateCompletion(template).percent, 50);

      await store.saveApplicationDocument(template, {
        'student_name_zh': '王小明',
        'motivation': '希望培養跨文化合作能力。',
      });

      expect(store.applicationTemplateCompletion(template).ready, isTrue);
      expect(store.applicationAnswers['study-plan'], {
        'motivation': '希望培養跨文化合作能力。',
      });
      expect(store.applicationSelections['study-plan']?.selected, isTrue);
      expect(
        store.applicationSelections['study-plan']?.status,
        ApplicationDocumentProgress.readyToPrint,
      );
      expect(store.applicationPacketPayload()['selections'], [
        {'template_id': 'study-plan', 'copies': 3},
      ]);
    },
  );

  test(
    'device memory keeps common fields and excludes identity data',
    () async {
      SharedPreferences.setMockInitialValues({});
      final store = ExchangeStore(
        api: ExchangeApi(
          client: MockClient((_) async => http.Response('[]', 200)),
          baseUrl: 'https://example.test/',
        ),
      );

      await store.saveApplicationProfile({
        'student_name_zh': '王小明',
        'email': 'student@example.com',
        'id_number': 'A123456789',
        'birth_date': '2004-01-01',
        'passport_number': '300000000',
      });
      await store.setApplicationProfileMemoryEnabled(true);

      final prefs = await SharedPreferences.getInstance();
      final memoryKey = prefs.getKeys().singleWhere(
        (key) => key.endsWith(':application_profile_memory_v1'),
      );
      final remembered =
          jsonDecode(prefs.getString(memoryKey)!) as Map<String, dynamic>;
      expect(remembered['student_name_zh'], '王小明');
      expect(remembered['email'], 'student@example.com');
      expect(remembered.containsKey('id_number'), isFalse);
      expect(remembered.containsKey('birth_date'), isFalse);
      expect(remembered.containsKey('passport_number'), isFalse);
      expect(store.applicationRememberedProfileCount, 2);

      await store.clearApplicationProfileMemory();
      expect(store.applicationProfile['student_name_zh'], '王小明');
      expect(prefs.getString('application_profile_memory_v1'), isNull);
      expect(prefs.getString(memoryKey), isNull);
    },
  );

  testWidgets(
    'document center keeps list cards concise and opens one form page',
    (tester) async {
      SharedPreferences.setMockInitialValues({});
      final store = ExchangeStore(
        api: ExchangeApi(
          client: MockClient((_) async => http.Response('[]', 200)),
          baseUrl: 'https://example.test/',
        ),
      )..applicationTemplates = [template];

      await tester.pumpWidget(
        ExchangeStoreScope(
          store: store,
          child: MaterialApp(
            theme: buildExchangeTheme(),
            home: const Scaffold(body: ApplicationDocumentsScreen()),
          ),
        ),
      );

      expect(find.text('申請文件'), findsOneWidget);
      await tester.scrollUntilVisible(
        find.text('待辦文件'),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      expect(find.text('待辦文件'), findsOneWidget);
      await tester.scrollUntilVisible(
        find.text('讀書計畫').last,
        240,
        scrollable: find.byType(Scrollable).first,
      );
      expect(find.text('讀書計畫'), findsWidgets);
      expect(find.text(template.description), findsNothing);

      await tester.ensureVisible(find.text('讀書計畫').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('讀書計畫').last);
      await tester.pumpAndSettle();

      expect(find.text('填寫文件'), findsOneWidget);
      expect(find.byTooltip('文件清單'), findsOneWidget);
      expect(find.text('官方格式'), findsOneWidget);
      expect(find.text('填寫說明'), findsOneWidget);
      expect(find.text('中文姓名 *'), findsOneWidget);
      expect(find.text('申請動機 *'), findsOneWidget);
      expect(find.text('請填寫與校務系統相同的姓名。'), findsNothing);
      expect(find.text('資料整理列印版'), findsNothing);
    },
  );

  testWidgets('document summary follows actual required-field completion', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues({});
    final store = ExchangeStore(
      api: ExchangeApi(
        client: MockClient((_) async => http.Response('[]', 200)),
        baseUrl: 'https://example.test/',
      ),
    )..applicationTemplates = [template];
    addTearDown(store.dispose);
    await tester.pumpWidget(
      ExchangeStoreScope(
        store: store,
        child: MaterialApp(
          theme: buildExchangeTheme(),
          home: const Scaffold(body: ApplicationDocumentsScreen()),
        ),
      ),
    );
    expect(find.text('0 / 1 份文件必填欄位已完成'), findsOneWidget);
    expect(find.text('接著準備'), findsOneWidget);
    expect(find.text('讀書計畫'), findsWidgets);
    expect(find.widgetWithText(FilledButton, '繼續準備'), findsOneWidget);

    await store.saveApplicationDocument(template, {
      'student_name_zh': '王小明',
      'motivation': '希望培養跨文化合作能力。',
    });
    await tester.pumpAndSettle();
    expect(find.text('1 / 1 份文件必填欄位已完成'), findsOneWidget);
    expect(find.text('必填欄位已完成，請核對官方要求。'), findsOneWidget);
    expect(find.widgetWithText(FilledButton, '繼續準備'), findsNothing);
    expect(find.widgetWithText(FilledButton, '檢查文件'), findsOneWidget);
  });
}

Map<String, dynamic> _templateJson(ApplicationDocumentTemplate template) => {
  'id': template.id,
  'title': template.title,
  'short_title': template.shortTitle,
  'category': template.category,
  'stage': template.stage,
  'description': template.description,
  'fields': template.fields
      .map(
        (field) => {
          'id': field.id,
          'label': field.label,
          'field_type': field.kind.name,
          'required': field.required,
          'reusable_profile_key': field.reusableProfileKey,
          'options': field.options,
          'sensitive': field.sensitive,
          'min_files': field.minFiles,
          'max_files': field.maxFiles,
        },
      )
      .toList(),
  'default_copies': template.defaultCopies,
  'destinations': template.destinations,
  'signatures': template.signatures,
  'stamps': template.stamps,
  'program_types': template.programTypes,
  'condition_flags': template.conditionFlags,
  'conditional_note': template.conditionalNote,
  'official_layout': template.officialLayout,
  'official_form_number': template.officialFormNumber,
  'official_file_name': template.officialFileName,
  'source_url': template.sourceUrl,
  'source_checked_at': template.sourceCheckedAt,
  'version': template.version,
};
