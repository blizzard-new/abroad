import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/screens/root_shell.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  testWidgets('global home and CGU board use separate navigation spaces', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues({});
    final client = MockClient(
      (_) async => http.Response(
        '[]',
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      ),
    );
    final store =
        ExchangeStore(
            api: ExchangeApi(client: client, baseUrl: 'https://example.test/'),
          )
          ..dashboard = const StudentDashboard(
            schoolName: '長庚大學',
            lastChecked: '2026-07-18',
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

    expect(find.text('留學首頁'), findsWidgets);
    expect(find.text('全台學生共用'), findsNothing);
    expect(find.text('看申請、交換生活與獎學金的最新討論。'), findsNothing);
    expect(find.text('全站共用'), findsNothing);
    expect(find.text('校級看板'), findsNothing);
    expect(find.text('長庚大學交換服務'), findsNothing);
    expect(find.textContaining('先選功能'), findsNothing);
    expect(find.byTooltip('發文'), findsOneWidget);
    expect(find.byTooltip('長庚板'), findsOneWidget);

    await tester.tap(find.byTooltip('長庚板'));
    await tester.pumpAndSettle();

    expect(find.text('長庚大學交換服務'), findsNothing);
    expect(find.text('申請顧問'), findsOneWidget);
    expect(find.textContaining('一個功能'), findsNothing);
    expect(find.byTooltip('返回留學首頁'), findsOneWidget);
    expect(find.byTooltip('找學校'), findsOneWidget);
    expect(find.byTooltip('填文件'), findsOneWidget);
    expect(find.byTooltip('討論板'), findsOneWidget);
    expect(find.byTooltip('我的帳號'), findsOneWidget);

    await tester.tap(find.byTooltip('填文件'));
    await tester.pumpAndSettle();

    expect(find.text('申請文件'), findsWidgets);
    expect(find.text('文件清單'), findsOneWidget);
    expect(find.text('目前沒有待填文件'), findsOneWidget);

    await tester.tap(find.byTooltip('討論板'));
    await tester.pumpAndSettle();

    expect(find.text('長庚討論板'), findsWidgets);
    expect(find.text('討論哪一間學校'), findsNothing);

    await tester.tap(find.byTooltip('找學校'));
    await tester.pumpAndSettle();

    expect(find.text('找到適合你的學校'), findsNothing);
    expect(find.text('沒有符合條件的學校'), findsOneWidget);
    expect(find.text('找交換學校'), findsWidgets);

    await tester.tap(find.byTooltip('返回留學首頁'));
    await tester.pumpAndSettle();

    expect(find.text('留學首頁'), findsWidgets);
    expect(find.text('長庚大學交換服務'), findsNothing);
  });
}
