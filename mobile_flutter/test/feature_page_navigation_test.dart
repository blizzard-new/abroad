import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/screens/home_screen.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('CGU overview opens every feature as an independent page', (
    tester,
  ) async {
    final store = ExchangeStore()
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
          home: Scaffold(body: HomeScreen(onSelectTab: (_) {})),
        ),
      ),
    );

    expect(find.text('申請顧問'), findsOneWidget);
    expect(find.text('長庚大學交換服務'), findsNothing);
    expect(find.textContaining('一個功能'), findsNothing);
    expect(find.text('接下來的期限'), findsNothing);
    expect(find.text('文件準備'), findsNothing);

    await tester.scrollUntilVisible(
      find.text('補助資訊'),
      320,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.ensureVisible(find.text('補助資訊'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('補助資訊'));
    await tester.pumpAndSettle();

    expect(find.text('補助資訊'), findsWidgets);
    expect(find.byTooltip('返回'), findsOneWidget);
    expect(find.text('目前沒有補助資料'), findsOneWidget);
  });
}
