import 'package:exchange_guide_flutter/core/application_calendar.dart';
import 'package:exchange_guide_flutter/core/connected_calendar.dart';
import 'package:device_calendar_plus/device_calendar_plus.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('detects common cloud calendar providers', () {
    const google = WritableCalendar(
      id: 'google',
      name: '申請時程',
      accountName: 'student@gmail.com',
      accountType: 'com.google',
    );
    const outlook = WritableCalendar(
      id: 'outlook',
      name: 'Calendar',
      accountName: 'student@outlook.com',
      accountType: 'com.microsoft.exchange',
    );

    expect(google.providerName, 'Google 日曆');
    expect(google.accountLabel, 'Google 日曆 · student@gmail.com');
    expect(outlook.providerName, 'Outlook');
  });

  test('persists connection and updates the same external event', () async {
    final gateway = _FakeCalendarGateway();
    final service = CalendarSyncService(gateway: gateway);
    await service.initialize();
    final calendars = await service.requestWritableCalendars();
    final event = _event(title: '完成讀書計畫');

    await service.connect(calendars.single, [event]);

    expect(service.connectedCalendar?.id, 'google-calendar');
    expect(service.isSynced(event.id), isTrue);
    expect(gateway.created, hasLength(1));

    final updated = _event(title: '完成讀書計畫第二版');
    await service.syncEvent(updated);

    expect(gateway.created, hasLength(1));
    expect(gateway.updated.single.$1, 'external-1');
    expect(gateway.updated.single.$2.title, '完成讀書計畫第二版');

    gateway.missingOnNextUpdate = true;
    await service.syncEvent(_event(title: '重建已被刪除的事件'));
    expect(gateway.created, hasLength(2));

    final restored = CalendarSyncService(gateway: gateway);
    await restored.initialize();
    expect(restored.connectedCalendar?.id, 'google-calendar');
    expect(restored.isSynced(event.id), isTrue);

    await restored.deleteEvent(event.id);
    expect(gateway.deleted, ['external-2']);
    expect(restored.isSynced(event.id), isFalse);
  });
}

ApplicationCalendarEvent _event({required String title}) {
  return ApplicationCalendarEvent(
    id: 'personal-1',
    title: title,
    date: DateTime(2026, 9, 30),
    category: 'documents',
    reminderDays: 7,
    note: '交換申請文件',
    sourceUrl: '',
    isOfficial: false,
  );
}

class _FakeCalendarGateway implements CalendarGateway {
  final created = <ApplicationCalendarEvent>[];
  final updated = <(String, ApplicationCalendarEvent)>[];
  final deleted = <String>[];
  bool missingOnNextUpdate = false;

  @override
  Future<List<WritableCalendar>> requestWritableCalendars() async => const [
    WritableCalendar(
      id: 'google-calendar',
      name: '交換申請',
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
  }) async {
    if (missingOnNextUpdate) {
      missingOnNextUpdate = false;
      throw const DeviceCalendarException(
        errorCode: DeviceCalendarError.notFound,
        message: 'event was deleted',
      );
    }
    updated.add((externalEventId, event));
  }

  @override
  Future<void> deleteEvent(String externalEventId) async {
    deleted.add(externalEventId);
  }

  @override
  Future<void> openAppSettings() async {}
}
