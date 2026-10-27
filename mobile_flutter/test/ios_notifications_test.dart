import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:exchange_guide_flutter/core/mobile_notifications.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test(
    'iOS requests notification permission only after the user enables it',
    () async {
      debugDefaultTargetPlatformOverride = TargetPlatform.iOS;
      IOSFlutterLocalNotificationsPlugin.registerWith();
      SharedPreferences.setMockInitialValues({});
      const notifications = MethodChannel(
        'dexterous.com/flutter/local_notifications',
      );
      const timezone = MethodChannel('flutter_timezone');
      final calls = <MethodCall>[];
      final messenger =
          TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
      messenger.setMockMethodCallHandler(timezone, (_) async => 'UTC');
      messenger.setMockMethodCallHandler(notifications, (call) async {
        calls.add(call);
        if (call.method == 'getNotificationAppLaunchDetails') {
          return <String, dynamic>{'notificationLaunchedApp': false};
        }
        if (call.method == 'initialize' || call.method == 'requestPermissions') {
          return true;
        }
        return null;
      });
      addTearDown(() {
        debugDefaultTargetPlatformOverride = null;
        AndroidFlutterLocalNotificationsPlugin.registerWith();
        messenger.setMockMethodCallHandler(notifications, null);
        messenger.setMockMethodCallHandler(timezone, null);
      });
      final service = MobileNotifications('https://example.test');
      await service.initialize();
      expect(service.initialized, isTrue);
      expect(
        calls.where((call) => call.method == 'requestPermissions'),
        isEmpty,
      );
      final settings =
          calls.firstWhere((call) => call.method == 'initialize').arguments
              as Map;
      expect(settings['requestAlertPermission'], isFalse);
      await service.bindAccount('test-user');
      expect(await service.enable(), isTrue);
      final request =
          calls
                  .singleWhere((call) => call.method == 'requestPermissions')
                  .arguments
              as Map;
      expect(request['alert'], isTrue);
      expect(request['sound'], isTrue);
      await service.bindAccount(null);
      expect(service.enabled, isFalse);
      expect(
        calls.where((call) => call.method == 'cancelAll').length,
        greaterThanOrEqualTo(2),
      );
    },
  );
}
