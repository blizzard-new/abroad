import 'package:exchange_guide_flutter/core/application_calendar.dart';
import 'package:exchange_guide_flutter/core/mobile_notifications.dart';
import 'package:exchange_guide_flutter/core/study_plan_widget_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:home_widget/home_widget.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets(
    'Android delivers and cancels notifications and updates widget data',
    (tester) async {
      await tester.pumpWidget(
        const MaterialApp(home: Scaffold(body: Text('UniWay platform test'))),
      );
      final notifications = MobileNotifications('https://fixture.invalid/');
      await notifications.initialize();
      expect(notifications.initialized, isTrue);
      await notifications.bindAccount('platform-test');
      // Grant POST_NOTIFICATIONS to this test APK via adb before running.
      expect(await notifications.enable(), isTrue);
      final tomorrow = DateTime.now().add(const Duration(days: 2));
      await notifications.schedule('platform-test', '長庚大學', [
        ApplicationCalendarEvent.fromJson({
          'id': 'fixture-event',
          'title': 'Fixture deadline',
          'date':
              '${tomorrow.year}-${tomorrow.month.toString().padLeft(2, '0')}-${tomorrow.day.toString().padLeft(2, '0')}',
          'reminder_days': 1,
          'category': 'personal',
        }),
      ]);
      expect(
        (await notifications.plugin.pendingNotificationRequests()).length,
        1,
      );
      await notifications.testNotification('platform-test', '長庚大學');
      expect(
        (await notifications.plugin.getActiveNotifications()).isNotEmpty,
        isTrue,
      );
      final widgets = StudyPlanWidgetService();
      await widgets.sync(
        const StudyPlanWidgetSnapshot(
          nextTitle: '平台測試：下一步',
          nextDateLabel: '2026/10/26',
          progressLabel: '準備進度 20%',
          tasks: ['文件準備'],
          updatedLabel: '測試資料',
        ),
      );
      expect(
        await HomeWidget.getWidgetData<String>(
          'home_widget.StudyPlanWidgetDefinition.nextTitle',
        ),
        '平台測試：下一步',
      );
      expect(
        await HomeWidget.updateWidget(
          qualifiedAndroidName: StudyPlanWidgetService.androidReceiver,
        ),
        isTrue,
      );
      await notifications.bindAccount(null);
      expect(await notifications.plugin.pendingNotificationRequests(), isEmpty);
      expect(await notifications.plugin.getActiveNotifications(), isEmpty);
      await widgets.sync(
        const StudyPlanWidgetSnapshot(
          nextTitle: '登入 UniWay，開始你的交換計畫',
          nextDateLabel: '與電腦共用帳號與進度',
          progressLabel: '尚未登入',
        ),
      );
    },
  );
}
