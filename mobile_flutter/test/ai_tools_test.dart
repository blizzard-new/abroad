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
  test('advisor and document AI models parse grounded API responses', () {
    final plan = AdvisorPlan.fromJson({
      'school_name': '長庚大學',
      'mode': 'ai_enhanced',
      'summary': '先補齊語言成績。',
      'qualification': ['學業平均已填寫'],
      'recommendations': [
        {
          'school_name': 'Lincoln University',
          'country': '紐西蘭',
          'match_score': 76,
          'fit_label': '條件接近',
          'reasons': ['學制符合'],
          'gaps': ['待確認語言門檻'],
          'source_urls': ['https://example.test/lincoln'],
        },
      ],
      'tasks': [
        {
          'id': 'task-1',
          'title': '準備語言成績',
          'detail': '確認有效期限',
          'category': 'language',
          'priority': 'high',
        },
      ],
      'answer': {
        'question': '需要哪些文件？',
        'answer': '目前來源只確認申請表。',
        'key_points': ['以當期公告為準'],
        'sources': [
          {
            'title': '交換公告',
            'source_url': 'https://example.test/source',
            'last_checked': '2026-07-19T00:00:00Z',
          },
        ],
        'evidence_status': 'limited',
      },
      'disclaimer': '符合度不是錄取機率。',
    });
    final review = DocumentCheckResult.fromJson({
      'file_name': 'plan.pdf',
      'document_type': 'study_plan',
      'summary': '缺少簽名。',
      'completeness_score': 72,
      'issues': [
        {
          'severity': 'warning',
          'code': 'signature',
          'title': '簽名待確認',
          'detail': '列印後簽名',
        },
      ],
    });

    expect(plan.recommendations.single.matchScore, 76);
    expect(plan.answer?.sources.single.title, '交換公告');
    expect(plan.tasks.single.priority, 'high');
    expect(review.completenessScore, 72);
    expect(review.issues.single.title, '簽名待確認');
  });

  test(
    'API sends advisor, review, and rewrite requests to AI endpoints',
    () async {
      final requests = <http.BaseRequest>[];
      final client = MockClient((request) async {
        requests.add(request);
        final path = request.url.path;
        if (path.endsWith('/advisor/plan')) {
          return _jsonResponse({
            'school_name': '長庚大學',
            'mode': 'source_grounded',
            'summary': '完成條件整理。',
            'qualification': [],
            'recommendations': [],
            'tasks': [],
            'disclaimer': '符合度不是錄取機率。',
          });
        }
        if (path.endsWith('/ai/review-document')) {
          return _jsonResponse({
            'file_name': 'plan.txt',
            'document_type': 'study_plan',
            'summary': '基本檢查完成。',
            'completeness_score': 90,
            'checks_passed': ['文字可讀取'],
            'issues': [],
            'suggestions': [],
          });
        }
        if (path.endsWith('/ai/rewrite-document')) {
          return _jsonResponse({
            'action': 'formalize',
            'draft': '我期望透過交換學習拓展專業視野。',
            'changes': ['調整正式語氣'],
            'warnings': [],
            'ai_enhanced': true,
            'disclaimer': '送出前請自行確認。',
          });
        }
        return http.Response('not found', 404);
      });
      final api = ExchangeApi(client: client, baseUrl: 'https://example.test/');

      final plan = await api.advisorPlan(
        const AdvisorProfile(
          academicScore: 82,
          preferredCountry: '日本',
          question: '我該先做什麼？',
        ),
      );
      final review = await api.reviewDocument(
        fileName: 'plan.txt',
        bytes: Uint8List.fromList(utf8.encode('交換讀書計畫內容')),
      );
      final rewrite = await api.rewriteDocument(
        text: '我希望申請交換，並在不同文化環境中學習專業課程及提升溝通能力。',
        action: 'formalize',
        documentType: 'study_plan',
      );

      expect(plan.summary, '完成條件整理。');
      expect(review.completenessScore, 90);
      expect(rewrite.aiEnhanced, isTrue);
      expect(
        requests.map((request) => request.url.path),
        contains('/advisor/plan'),
      );
      expect(
        requests.map((request) => request.url.path),
        contains('/ai/review-document'),
      );
      expect(
        requests.map((request) => request.url.path),
        contains('/ai/rewrite-document'),
      );
    },
  );

  testWidgets(
    'AI tools are independent pages and support system text scaling',
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

      Future<void> pump(Widget page) async {
        await tester.pumpWidget(
          ExchangeStoreScope(
            store: store,
            child: MaterialApp(
              theme: buildExchangeTheme(),
              builder: (context, child) => MediaQuery(
                data: MediaQuery.of(
                  context,
                ).copyWith(textScaler: const TextScaler.linear(1.3)),
                child: child!,
              ),
              home: page,
            ),
          ),
        );
        await tester.pumpAndSettle();
      }

      await pump(const AdvisorScreen());
      expect(find.text('產生申請方案'), findsOneWidget);
      expect(tester.takeException(), isNull);

      await pump(const DocumentCheckScreen());
      expect(find.text('開始檢查'), findsOneWidget);
      expect(tester.takeException(), isNull);

      await pump(const WritingAssistantScreen());
      expect(find.text('產生建議稿'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}

http.Response _jsonResponse(Map<String, dynamic> body) => http.Response(
  jsonEncode(body),
  200,
  headers: {'content-type': 'application/json; charset=utf-8'},
);
