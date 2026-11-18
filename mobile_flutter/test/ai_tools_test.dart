import 'dart:convert';
import 'dart:typed_data';

import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/screens/ai_tools_screens.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('deterministic document check model parses rule-based counts and issues', () {
    final review = DocumentCheckResult.fromJson({
      'file_name': 'plan.pdf',
      'document_type': 'study_plan',
      'page_count': 2,
      'word_count': 680,
      'character_count': 1420,
      'summary': '字數與頁數符合建議範圍，請於列印後親筆簽名。',
      'checks_passed': ['文字可正常擷取', '頁數在 2 頁以內'],
      'issues': [
        {
          'severity': 'warning',
          'code': 'signature',
          'title': '簽名待確認',
          'detail': '列印後請於申請人欄位簽名',
        },
      ],
      'extracted_preview': '交換學生讀書計畫摘要',
    });

    expect(review.fileName, 'plan.pdf');
    expect(review.pageCount, 2);
    expect(review.wordCount, 680);
    expect(review.characterCount, 1420);
    expect(review.checksPassed, contains('文字可正常擷取'));
    expect(review.issues.single.title, '簽名待確認');
    expect(review.extractedPreview, '交換學生讀書計畫摘要');
  });

  test(
    'reviewDocument posts deterministic /document-check with consent=true, use_ai=false and bearer token',
    () async {
      final requests = <http.BaseRequest>[];
      String? bodyText;
      final client = MockClient((request) async {
        requests.add(request);
        bodyText = request.body;
        if (request.url.path.endsWith('/document-check')) {
          return _jsonResponse({
            'file_name': 'plan.txt',
            'document_type': 'study_plan',
            'page_count': 1,
            'word_count': 120,
            'character_count': 360,
            'summary': '格式與字數檢查完成。',
            'checks_passed': ['文字可讀取'],
            'issues': [],
            'suggestions': [],
          });
        }
        return http.Response('not found', 404);
      });
      final api = ExchangeApi(client: client, baseUrl: 'https://example.test/');

      final review = await api.reviewDocument(
        fileName: 'plan.txt',
        bytes: Uint8List.fromList(utf8.encode('交換讀書計畫內容')),
        documentType: 'study_plan',
        accessToken: 'student-jwt-token',
      );

      expect(review.summary, '格式與字數檢查完成。');
      expect(review.wordCount, 120);
      expect(requests, hasLength(1));
      expect(requests.single.url.path, '/document-check');
      expect(
        requests.single.headers['authorization'] ??
            requests.single.headers['Authorization'],
        'Bearer student-jwt-token',
      );
      expect(bodyText, contains('name="consent"'));
      expect(bodyText, contains('true'));
      expect(bodyText, contains('name="use_ai"'));
      expect(bodyText, contains('false'));
    },
  );

  testWidgets(
    'DocumentCheckScreen presents honest deterministic copy and supports text scaling',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final store = ExchangeStore()
        ..dashboard = const StudentDashboard(
          schoolName: '長庚大學',
          lastChecked: '2026-07-19',
          applicationPeriods: [],
          programOverview: [],
          eligibility: [],
          languageRequirements: [],
          requiredDocuments: [],
          scholarshipInfo: [],
          ruleExplanations: [],
          partnerUniversities: [],
          sources: [],
        );
      addTearDown(store.dispose);

      await tester.pumpWidget(
        ExchangeStoreScope(
          store: store,
          child: MaterialApp(
            theme: buildExchangeTheme(),
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(
                context,
              ).copyWith(textScaler: const TextScaler.linear(1.4)),
              child: child!,
            ),
            home: const DocumentCheckScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('格式與字數檢查'), findsWidgets);
      expect(find.text('開始檢查'), findsOneWidget);
      expect(find.textContaining('AI 深度檢查'), findsNothing);
      expect(find.textContaining('AI 建議稿'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );
}

http.Response _jsonResponse(Map<String, dynamic> body) => http.Response(
  jsonEncode(body),
  200,
  headers: {'content-type': 'application/json; charset=utf-8'},
);
