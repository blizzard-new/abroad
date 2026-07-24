import 'dart:convert';

import 'package:device_calendar_plus/device_calendar_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'application_calendar.dart';

class WritableCalendar {
  const WritableCalendar({
    required this.id,
    required this.name,
    this.accountName,
    this.accountType,
    this.colorHex,
    this.isPrimary = false,
    this.hidden = false,
  });

  factory WritableCalendar.fromJson(Map<String, dynamic> json) {
    return WritableCalendar(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '日曆',
      accountName: json['account_name'] as String?,
      accountType: json['account_type'] as String?,
      colorHex: json['color_hex'] as String?,
      isPrimary: json['is_primary'] == true,
      hidden: json['hidden'] == true,
    );
  }

  final String id;
  final String name;
  final String? accountName;
  final String? accountType;
  final String? colorHex;
  final bool isPrimary;
  final bool hidden;

  String get providerName {
    final value = '${accountType ?? ''} ${accountName ?? ''}'.toLowerCase();
    if (value.contains('google') || value.contains('gmail')) {
      return 'Google 日曆';
    }
    if (value.contains('icloud') || value.contains('apple')) return 'iCloud';
    if (value.contains('outlook') ||
        value.contains('exchange') ||
        value.contains('microsoft') ||
        value.contains('hotmail') ||
        value.contains('live.com')) {
      return 'Outlook';
    }
    if (value.contains('local')) return '本機日曆';
    return '裝置日曆';
  }

  String get accountLabel {
    final account = accountName?.trim() ?? '';
    if (account.isEmpty || account == name) return providerName;
    return '$providerName · $account';
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'account_name': accountName,
    'account_type': accountType,
    'color_hex': colorHex,
    'is_primary': isPrimary,
    'hidden': hidden,
  };
}

class CalendarConnectionException implements Exception {
  const CalendarConnectionException(
    this.message, {
    this.canOpenSettings = false,
  });

  final String message;
  final bool canOpenSettings;

  @override
  String toString() => message;
}

abstract class CalendarGateway {
  Future<List<WritableCalendar>> requestWritableCalendars();

  Future<void> openAppSettings();

  Future<String> createEvent({
    required WritableCalendar calendar,
    required ApplicationCalendarEvent event,
  });

  Future<void> updateEvent({
    required String externalEventId,
    required ApplicationCalendarEvent event,
  });

  Future<void> deleteEvent(String externalEventId);
}

class DeviceCalendarGateway implements CalendarGateway {
  DeviceCalendarGateway({DeviceCalendar? deviceCalendar})
    : _deviceCalendar = deviceCalendar ?? DeviceCalendar.instance;

  final DeviceCalendar _deviceCalendar;

  @override
  Future<List<WritableCalendar>> requestWritableCalendars() async {
    final status = await _deviceCalendar.requestPermissions(
      level: CalendarAccessLevel.full,
    );
    if (status != CalendarPermissionStatus.granted) {
      final restricted = status == CalendarPermissionStatus.restricted;
      throw CalendarConnectionException(
        restricted ? '此裝置限制了日曆存取。' : '請允許日曆存取，才能開啟自動同步。',
        canOpenSettings: status == CalendarPermissionStatus.denied,
      );
    }

    final calendars = (await _deviceCalendar.listCalendars())
        .where((calendar) => !calendar.readOnly && !calendar.hidden)
        .map(
          (calendar) => WritableCalendar(
            id: calendar.id,
            name: calendar.name,
            accountName: calendar.accountName,
            accountType: calendar.accountType,
            colorHex: calendar.colorHex,
            isPrimary: calendar.isPrimary,
            hidden: calendar.hidden,
          ),
        )
        .toList();
    calendars.sort((left, right) {
      if (left.hidden != right.hidden) return left.hidden ? 1 : -1;
      if (left.isPrimary != right.isPrimary) return left.isPrimary ? -1 : 1;
      final byProvider = left.providerName.compareTo(right.providerName);
      return byProvider != 0 ? byProvider : left.name.compareTo(right.name);
    });
    return calendars;
  }

  @override
  Future<void> openAppSettings() => _deviceCalendar.openAppSettings();

  @override
  Future<String> createEvent({
    required WritableCalendar calendar,
    required ApplicationCalendarEvent event,
  }) {
    final description = calendarEventDescription(event);
    return _deviceCalendar.createEvent(
      calendarId: calendar.id,
      title: '[交換申請] ${event.title}',
      startDate: dateOnly(event.date),
      endDate: dateOnly(event.date).add(const Duration(days: 1)),
      isAllDay: true,
      description: description.isEmpty ? null : description,
      url: event.sourceUrl.isEmpty ? null : event.sourceUrl,
      reminders: [Duration(days: event.reminderDays)],
    );
  }

  @override
  Future<void> updateEvent({
    required String externalEventId,
    required ApplicationCalendarEvent event,
  }) {
    final description = calendarEventDescription(event);
    return _deviceCalendar.updateEvent(
      eventId: externalEventId,
      title: '[交換申請] ${event.title}',
      startDate: dateOnly(event.date),
      endDate: dateOnly(event.date).add(const Duration(days: 1)),
      isAllDay: true,
      description: description.isEmpty
          ? const Patch<String>.clear()
          : Patch<String>.set(description),
      url: event.sourceUrl.isEmpty
          ? const Patch<String>.clear()
          : Patch<String>.set(event.sourceUrl),
      reminders: Patch<List<Duration>>.set([
        Duration(days: event.reminderDays),
      ]),
    );
  }

  @override
  Future<void> deleteEvent(String externalEventId) {
    return _deviceCalendar.deleteEvent(eventId: externalEventId);
  }
}

class CalendarSyncService {
  CalendarSyncService({CalendarGateway? gateway})
    : gateway = gateway ?? DeviceCalendarGateway();

  static const _calendarKey = 'connected_calendar_v1';
  static const _eventLinksKey = 'calendar_event_links_v1';
  static const _separator = '|';

  final CalendarGateway gateway;
  final Map<String, String> _eventLinks = {};
  WritableCalendar? connectedCalendar;

  Future<void> initialize() async {
    final prefs = await SharedPreferences.getInstance();
    final calendarJson = prefs.getString(_calendarKey);
    if (calendarJson != null) {
      try {
        final decoded = jsonDecode(calendarJson);
        if (decoded is Map) {
          final calendar = WritableCalendar.fromJson(
            Map<String, dynamic>.from(decoded),
          );
          if (calendar.id.isNotEmpty) connectedCalendar = calendar;
        }
      } catch (_) {
        await prefs.remove(_calendarKey);
      }
    }

    final linksJson = prefs.getString(_eventLinksKey);
    if (linksJson != null) {
      try {
        final decoded = jsonDecode(linksJson);
        if (decoded is Map) {
          _eventLinks
            ..clear()
            ..addAll(
              decoded.map(
                (key, value) => MapEntry(key.toString(), value.toString()),
              ),
            );
        }
      } catch (_) {
        await prefs.remove(_eventLinksKey);
      }
    }
  }

  Future<List<WritableCalendar>> requestWritableCalendars() {
    return gateway.requestWritableCalendars();
  }

  Future<void> openAppSettings() => gateway.openAppSettings();

  bool isSynced(String eventId) {
    final calendar = connectedCalendar;
    return calendar != null &&
        _eventLinks.containsKey(_linkKey(calendar.id, eventId));
  }

  bool hasAnyLink(String eventId) {
    return _eventLinks.keys.any((key) => key.endsWith('$_separator$eventId'));
  }

  Future<void> connect(
    WritableCalendar calendar,
    Iterable<ApplicationCalendarEvent> events,
  ) async {
    final previous = connectedCalendar;
    final values = events.toList();
    if (previous != null && previous.id != calendar.id) {
      for (final event in values) {
        final key = _linkKey(previous.id, event.id);
        final externalId = _eventLinks[key];
        if (externalId == null) continue;
        await gateway.deleteEvent(externalId);
        _eventLinks.remove(key);
        await _saveLinks();
      }
    }

    connectedCalendar = calendar;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_calendarKey, jsonEncode(calendar.toJson()));
    await syncAll(values);
  }

  Future<void> disconnect() async {
    connectedCalendar = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_calendarKey);
  }

  Future<void> syncAll(Iterable<ApplicationCalendarEvent> events) async {
    for (final event in events) {
      await syncEvent(event);
    }
  }

  Future<void> syncEvent(ApplicationCalendarEvent event) async {
    final calendar = connectedCalendar;
    if (calendar == null) {
      throw const CalendarConnectionException('請先連接第三方日曆。');
    }
    final key = _linkKey(calendar.id, event.id);
    final externalId = _eventLinks[key];
    if (externalId == null) {
      _eventLinks[key] = await gateway.createEvent(
        calendar: calendar,
        event: event,
      );
      await _saveLinks();
      return;
    }
    try {
      await gateway.updateEvent(externalEventId: externalId, event: event);
    } on DeviceCalendarException catch (exception) {
      if (exception.errorCode != DeviceCalendarError.notFound) rethrow;
      _eventLinks[key] = await gateway.createEvent(
        calendar: calendar,
        event: event,
      );
      await _saveLinks();
    }
  }

  Future<void> deleteEvent(String eventId) async {
    final calendar = connectedCalendar;
    if (calendar == null) return;
    final key = _linkKey(calendar.id, eventId);
    final externalId = _eventLinks[key];
    if (externalId == null) return;
    try {
      await gateway.deleteEvent(externalId);
    } on DeviceCalendarException catch (exception) {
      if (exception.errorCode != DeviceCalendarError.notFound) rethrow;
    }
    _eventLinks.remove(key);
    await _saveLinks();
  }

  String _linkKey(String calendarId, String eventId) =>
      '$calendarId$_separator$eventId';

  Future<void> _saveLinks() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_eventLinksKey, jsonEncode(_eventLinks));
  }
}
