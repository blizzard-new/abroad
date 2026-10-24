import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/core/study_plan_widget_service.dart';
import 'package:exchange_guide_flutter/screens/app_update_prompt.dart';
import 'package:exchange_guide_flutter/screens/student_plan_screens.dart';
import 'package:exchange_guide_flutter/screens/widget_style_preview.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test(
    'all widget styles refresh and logout snapshot clears private content',
    () async {
      debugDefaultTargetPlatformOverride = TargetPlatform.android;
      addTearDown(() => debugDefaultTargetPlatformOverride = null);
      final saved = <String, dynamic>{};
      final refreshed = <String>[];
      final pinned = <String>[];
      const channel = MethodChannel('home_widget');
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (call) async {
            final args = call.arguments as Map?;
            if (call.method == 'saveWidgetData')
              saved[args!['id']] = args['data'];
            if (call.method == 'updateWidget')
              refreshed.add(args!['qualifiedAndroidName']);
            if (call.method == 'requestPinWidget') {
              pinned.add(args!['qualifiedAndroidName']);
              return null;
            }
            return true;
          });
      addTearDown(
        () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null),
      );
      final service = StudyPlanWidgetService();
      await service.sync(
        const StudyPlanWidgetSnapshot(
          nextTitle: 'Private test task',
          nextDateLabel: '2030/1/2',
          progressLabel: '準備進度 50%',
          tasks: ['Private document'],
          deadlineIso: '2030-01-02',
        ),
      );
      expect(refreshed, StudyPlanWidgetStyle.values.map((s) => s.androidName));
      for (final style in StudyPlanWidgetStyle.values) {
        await service.requestPin(style: style);
      }
      expect(pinned, StudyPlanWidgetStyle.values.map((s) => s.androidName));
      await service.sync(
        const StudyPlanWidgetSnapshot(
          nextTitle: '登入後開始',
          nextDateLabel: '',
          progressLabel: '尚未登入',
        ),
      );
      expect(saved['home_widget.StudyPlanWidgetDefinition.deadlineIso'], '');
      expect(saved['home_widget.StudyPlanWidgetDefinition.tasks'], '');
      expect(saved.values.join(), isNot(contains('Private')));
      expect(refreshed.length, 8);
    },
  );

  testWidgets('four previews remain readable at narrow width and large text', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(320, 720));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    for (final style in StudyPlanWidgetStyle.values) {
      await tester.pumpWidget(
        MaterialApp(
          theme: buildExchangeTheme(),
          home: MediaQuery(
            data: const MediaQueryData(
              size: Size(320, 720),
              textScaler: TextScaler.linear(2),
            ),
            child: Scaffold(
              body: SingleChildScrollView(
                child: WidgetStylePreview(
                  style: style,
                  title: '測試用交換申請文件與送件日期',
                  dateLabel: '2030/1/2',
                  percent: 65,
                  tasks: const ['測試文件一', '測試文件二'],
                  deadline: DateTime(2030, 1, 2),
                ),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    }
  });

  testWidgets('gallery pins selected style without changing other widgets', (
    tester,
  ) async {
    final bridge = _PinBridge();
    final store = ExchangeStore(widgetBridge: bridge);
    addTearDown(store.dispose);
    await tester.pumpWidget(
      ExchangeStoreScope(
        store: store,
        child: MaterialApp(
          theme: buildExchangeTheme(),
          home: const WidgetSettingsScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();
    for (final style in StudyPlanWidgetStyle.values) {
      await tester.tap(find.widgetWithText(ChoiceChip, style.label));
      await tester.pumpAndSettle();
      expect(
        find.byKey(ValueKey('widget-preview-${style.name}')),
        findsOneWidget,
      );
      await tester.tap(find.widgetWithText(FilledButton, '加入桌面'));
      await tester.pumpAndSettle();
      expect(bridge.pinned.last, style);
    }
  });

  testWidgets('iOS update entry never offers an Android APK', (tester) async {
    debugDefaultTargetPlatformOverride = TargetPlatform.iOS;
    addTearDown(() => debugDefaultTargetPlatformOverride = null);
    await tester.pumpWidget(
      MaterialApp(
        theme: buildExchangeTheme(),
        home: const Scaffold(body: AppUpdateTile()),
      ),
    );
    expect(find.textContaining('TestFlight'), findsOneWidget);
    expect(find.text('檢查更新'), findsNothing);
    expect(find.textContaining('APK'), findsNothing);
    debugDefaultTargetPlatformOverride = null;
  });

  test('cosmic text and controls meet normal-text contrast', () {
    for (final foreground in [
      ExchangeColors.ink,
      ExchangeColors.secondaryInk,
      ExchangeColors.teal,
    ]) {
      for (final background in [
        ExchangeColors.background,
        ExchangeColors.surface,
        const Color(0xFF29344F),
        const Color(0xFF2D4869),
      ]) {
        expect(
          (foreground.computeLuminance() + .05) /
              (background.computeLuminance() + .05),
          greaterThanOrEqualTo(4.5),
        );
      }
    }
  });
}

class _PinBridge implements StudyPlanWidgetBridge {
  final pinned = <StudyPlanWidgetStyle>[];
  @override
  Future<void> initialize() async {}
  @override
  Future<bool> canRequestPin() async => true;
  @override
  Future<void> requestPin({
    StudyPlanWidgetStyle style = StudyPlanWidgetStyle.overview,
  }) async {
    pinned.add(style);
  }

  @override
  Future<void> sync(StudyPlanWidgetSnapshot snapshot) async {}
}
