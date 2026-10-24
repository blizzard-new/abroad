import 'package:exchange_guide_flutter/core/application_calendar.dart';
import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/screens/deadlines_screen.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets(
    'calendar deadline card grows to fit larger text on a narrow phone',
    (tester) async {
      tester.view.physicalSize = const Size(360, 800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final store = ExchangeStore();
      store.personalCalendarEvents.add(
        ApplicationCalendarEvent(
          id: 'layout-fixture',
          title: '完成交換申請資料與語言證明',
          date: DateTime.now().add(const Duration(days: 2)),
          category: 'documents',
          reminderDays: 1,
          note: '',
          sourceUrl: '',
          isOfficial: false,
        ),
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
            home: const DeadlinesScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('下一個期限'), findsOneWidget);
      expect(find.widgetWithText(AppBar, '申請時程'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
      store.dispose();
    },
  );
}
