import 'dart:async';
import 'dart:convert';

import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/data/latest.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import 'application_calendar.dart';

class MobileNotificationTarget {
  const MobileNotificationTarget({
    required this.accountId,
    required this.homeSchool,
    this.eventId = '',
    this.notificationId = '',
  });
  final String accountId;
  final String homeSchool;
  final String eventId;
  final String notificationId;
  String encode() => jsonEncode({
    'account_id': accountId,
    'home_school': homeSchool,
    'event_id': eventId,
    'notification_id': notificationId,
  });
  static MobileNotificationTarget? decode(String? value) {
    if (value == null) return null;
    try {
      final data = jsonDecode(value);
      if (data is! Map ||
          data['account_id'] is! String ||
          data['home_school'] is! String) {
        return null;
      }
      return MobileNotificationTarget(
        accountId: data['account_id'],
        homeSchool: data['home_school'],
        eventId: data['event_id']?.toString() ?? '',
        notificationId: data['notification_id']?.toString() ?? '',
      );
    } catch (_) {
      return null;
    }
  }
}

class MobileNotifications {
  MobileNotifications(this.server);
  final String server;
  final FlutterLocalNotificationsPlugin plugin =
      FlutterLocalNotificationsPlugin();
  final ValueNotifier<MobileNotificationTarget?> target = ValueNotifier(null);
  bool initialized = false;
  bool enabled = false;
  bool _bound = false;
  String? currentAccount;
  String? lastSchedule;
  int _generation = 0;
  Future<void> _queue = Future.value();
  static const details = NotificationDetails(
    android: AndroidNotificationDetails(
      'uniway_reminders',
      '交換申請提醒',
      channelDescription: '個人申請時程與待辦提醒',
      importance: Importance.high,
      priority: Priority.high,
      visibility: NotificationVisibility.private,
      icon: '@drawable/ic_notification',
    ),
    iOS: DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: false,
      presentSound: true,
    ),
  );

  Future<void> initialize() async {
    if (initialized ||
        kIsWeb ||
        (defaultTargetPlatform != TargetPlatform.android &&
            defaultTargetPlatform != TargetPlatform.iOS)) {
      return;
    }
    try {
      tzdata.initializeTimeZones();
      final zone = await FlutterTimezone.getLocalTimezone();
      tz.setLocalLocation(
        const {'GMT', 'UTC', 'Etc/UTC', 'Etc/GMT'}.contains(zone.identifier)
            ? tz.UTC
            : tz.getLocation(zone.identifier),
      );
      await plugin.initialize(
        settings: const InitializationSettings(
          android: AndroidInitializationSettings('@drawable/ic_notification'),
          iOS: DarwinInitializationSettings(
            requestAlertPermission: false,
            requestBadgePermission: false,
            requestSoundPermission: false,
          ),
        ),
        onDidReceiveNotificationResponse: (response) =>
            target.value = MobileNotificationTarget.decode(response.payload),
      );
      final launch = await plugin.getNotificationAppLaunchDetails();
      if (launch?.didNotificationLaunchApp == true) {
        target.value = MobileNotificationTarget.decode(
          launch?.notificationResponse?.payload,
        );
      }
      initialized = true;
    } on MissingPluginException {
      initialized = false;
    } on PlatformException {
      initialized = false;
    } on tz.LocationNotFoundException {
      // An unfamiliar device timezone must never block account/catalogue loading.
      initialized = false;
    }
  }

  String _key(String account) =>
      'notification_enabled:${Uri.encodeComponent(server)}:$account';

  Future<void> bindAccount(String? accountId) async {
    if (_bound && currentAccount == accountId) return;
    _bound = true;
    _generation++;
    currentAccount = accountId;
    lastSchedule = null;
    enabled = false;
    await _queue.catchError((Object _) {});
    if (initialized) await plugin.cancelAll();
    if (accountId != null) {
      final prefs = await SharedPreferences.getInstance();
      enabled = prefs.getBool(_key(accountId)) ?? false;
    }
  }

  Future<bool> enable() async {
    await initialize();
    if (!initialized || currentAccount == null) return false;
    final expectedAccount = currentAccount;
    final generation = _generation;
    final granted = defaultTargetPlatform == TargetPlatform.iOS
        ? await plugin
                  .resolvePlatformSpecificImplementation<
                    IOSFlutterLocalNotificationsPlugin
                  >()
                  ?.requestPermissions(
                    alert: true,
                    badge: false,
                    sound: true,
                  ) ??
              false
        : await plugin
                  .resolvePlatformSpecificImplementation<
                    AndroidFlutterLocalNotificationsPlugin
                  >()
                  ?.requestNotificationsPermission() ??
              false;
    if (generation != _generation || currentAccount != expectedAccount) {
      return false;
    }
    enabled = granted;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_key(currentAccount!), granted);
    lastSchedule = null;
    return granted;
  }

  Future<void> disable() async {
    _generation++;
    enabled = false;
    lastSchedule = null;
    final account = currentAccount;
    if (account != null) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_key(account), false);
    }
    await _queue.catchError((Object _) {});
    if (initialized) await plugin.cancelAll();
  }

  Future<void> schedule(
    String account,
    String school,
    List<ApplicationCalendarEvent> events,
  ) {
    if (!initialized || !enabled || currentAccount != account) {
      return Future.value();
    }
    final signature = jsonEncode([
      account,
      school,
      events.map((e) => e.toJson()).toList(),
    ]);
    if (lastSchedule == signature) return _queue;
    final generation = _generation;
    final snapshot = List<ApplicationCalendarEvent>.from(events);
    _queue = _queue.catchError((Object _) {}).then((_) async {
      if (generation != _generation || !enabled || currentAccount != account) {
        return;
      }
      await plugin.cancelAllPendingNotifications();
      for (final event in snapshot.take(
        defaultTargetPlatform == TargetPlatform.iOS ? 60 : 100,
      )) {
        if (generation != _generation ||
            !enabled ||
            currentAccount != account) {
          return;
        }
        // Only dates explicitly saved in the student's workspace are scheduled.
        // Never infer next year's deadline from an unverified month/day string.
        final day = event.date.subtract(Duration(days: event.reminderDays));
        final when = tz.TZDateTime(tz.local, day.year, day.month, day.day, 9);
        if (!when.isAfter(tz.TZDateTime.now(tz.local))) continue;
        final bytes = sha256
            .convert(utf8.encode('$account:$school:${event.id}'))
            .bytes;
        final id =
            ((bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] << 8) | bytes[3]) &
            0x7fffffff;
        await plugin.zonedSchedule(
          id: id,
          title: 'UniWay · 交換計畫提醒',
          body: '你設定的申請事項即將到期，打開查看。',
          scheduledDate: when,
          notificationDetails: details,
          androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
          payload: MobileNotificationTarget(
            accountId: account,
            homeSchool: school,
            eventId: event.id,
          ).encode(),
        );
      }
      if (generation == _generation) lastSchedule = signature;
    });
    return _queue;
  }

  Future<void> testNotification(String account, String school) async {
    if (!initialized || !enabled || currentAccount != account) return;
    await plugin.show(
      id: 2147483646,
      title: 'UniWay 通知已開啟',
      body: '點一下，回到你的交換申請時程。',
      notificationDetails: details,
      payload: MobileNotificationTarget(
        accountId: account,
        homeSchool: school,
      ).encode(),
    );
  }
}
