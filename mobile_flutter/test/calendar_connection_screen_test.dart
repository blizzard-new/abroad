import 'package:exchange_guide_flutter/core/application_calendar.dart';
import 'package:exchange_guide_flutter/core/connected_calendar.dart';
import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/screens/deadlines_screen.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  testWidgets('connects a device calendar and syncs a new task', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues({});
    final gateway = _ScreenCalendarGateway();
    final sync = CalendarSyncService(gateway: gateway);
    await sync.initialize();
    final store = ExchangeStore(calendarSync: sync)
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
          home: const Scaffold(body: DeadlinesScreen()),
        ),
      ),
    );

    expect(find.text('連接第三方日曆'), findsOneWidget);
    await tester.tap(find.text('連接'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('我的 Google 日曆'));
    await tester.pumpAndSettle();

    expect(find.text('我的 Google 日曆'), findsOneWidget);
    expect(find.text('Google 日曆 · student@gmail.com'), findsOneWidget);

    await tester.drag(find.byType(ListView).first, const Offset(0, -520));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, '新增申請任務'));
    await tester.pumpAndSettle();
    final titleField = find.byWidgetPredicate(
      (widget) => widget is TextField && widget.decoration?.labelText == '任務名稱',
    );
    await tester.enterText(titleField, '繳交校內申請');
    final saveButton = find.text('儲存任務');
    await tester.ensureVisible(saveButton);
    await tester.tap(saveButton);
    await tester.pumpAndSettle();

    expect(gateway.created.single.title, '繳交校內申請');
    expect(store.isCalendarEventSynced(gateway.created.single.id), isTrue);
  });
}

class _ScreenCalendarGateway implements CalendarGateway {
  final created = <ApplicationCalendarEvent>[];

  @override
  Future<List<WritableCalendar>> requestWritableCalendars() async => const [
    WritableCalendar(
      id: 'google-calendar',
      name: '我的 Google 日曆',
      accountName: 'student@gmail.com',
      accountType: 'com.google',
      isPrimary: true,
    ),
  ];

  @override
  Future<String> createEvent({
    required WritableCalendar calendar,
    required ApplicationCalendarEvent event,
  }) async {
    created.add(event);
    return 'external-${created.length}';
  }

  @override
  Future<void> updateEvent({
    required String externalEventId,
    required ApplicationCalendarEvent event,
  }) async {}

  @override
  Future<void> deleteEvent(String externalEventId) async {}

  @override
  Future<void> openAppSettings() async {}
}
