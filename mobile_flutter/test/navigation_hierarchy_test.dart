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
  testWidgets(
    'student journey schools documents and account remain reachable',
    (tester) async {
      SharedPreferences.setMockInitialValues({});
      await tester.binding.setSurfaceSize(const Size(360, 800));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final client = MockClient(
        (_) async => http.Response(
          '[]',
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        ),
      );
      final store =
          ExchangeStore(
              api: ExchangeApi(
                client: client,
                baseUrl: 'https://example.test/',
              ),
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
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(
                context,
              ).copyWith(textScaler: const TextScaler.linear(1.4)),
              child: child!,
            ),
            home: const RootShell(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('旅程'), findsOneWidget);
      expect(find.byTooltip('通知與提醒'), findsOneWidget);
      await tester.tap(find.text('學校').last);
      await tester.pumpAndSettle();
      expect(find.text('找學校'), findsOneWidget);
      await tester.tap(find.text('申請').last);
      await tester.pumpAndSettle();
      expect(find.text('申請文件'), findsOneWidget);
      await tester.tap(find.text('論壇').last);
      await tester.pumpAndSettle();
      expect(find.text('交換生論壇'), findsOneWidget);
      await tester.tap(find.text('我的').last);
      await tester.pumpAndSettle();
      expect(find.textContaining('Google'), findsWidgets);
      await tester.tap(find.text('旅程').last);
      await tester.pumpAndSettle();
      expect(find.byTooltip('通知與提醒'), findsOneWidget);
      expect(tester.takeException(), isNull);
      store.dispose();
    },
  );
}
