import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:home_widget/home_widget.dart';

import '../src/home_widget/study_plan_widget.home_widget.dart';

class StudyPlanWidgetSnapshot {
  const StudyPlanWidgetSnapshot({
    required this.nextTitle,
    required this.nextDateLabel,
    required this.progressLabel,
    this.tasks = const [],
    this.updatedLabel = '',
  });

  final String nextTitle;
  final String nextDateLabel;
  final String progressLabel;
  final List<String> tasks;
  final String updatedLabel;
}

abstract interface class StudyPlanWidgetBridge {
  Future<void> initialize();

  Future<void> sync(StudyPlanWidgetSnapshot snapshot);

  Future<bool> canRequestPin();

  Future<void> requestPin();
}

class StudyPlanWidgetService implements StudyPlanWidgetBridge {
  static const appGroupId = 'group.tw.edu.cgu.exchangeGuideFlutter';
  static const androidReceiver =
      'tw.edu.cgu.exchange_guide_flutter.StudyPlanWidgetDefinitionHomeWidgetReceiver';

  @override
  Future<void> initialize() async {
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.iOS) {
      await _ignorePlatformFailure(() async {
        await HomeWidget.setAppGroupId(appGroupId);
      });
    }
  }

  @override
  Future<void> sync(StudyPlanWidgetSnapshot snapshot) async {
    await _ignorePlatformFailure(() async {
      await StudyPlanWidgetDefinitionHomeWidget.saveData(
        nextTitle: snapshot.nextTitle,
        nextDateLabel: snapshot.nextDateLabel,
        progressLabel: snapshot.progressLabel,
      );
      await HomeWidget.saveWidgetData<String>(
        'home_widget.StudyPlanWidgetDefinition.tasks',
        snapshot.tasks.join('\n'),
      );
      await HomeWidget.saveWidgetData<String>(
        'home_widget.StudyPlanWidgetDefinition.updatedLabel',
        snapshot.updatedLabel,
      );
      await HomeWidget.updateWidget(
        qualifiedAndroidName: androidReceiver,
        iOSName: 'StudyPlanWidgetDefinitionHomeWidget',
      );
    });
  }

  @override
  Future<bool> canRequestPin() async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) return false;
    try {
      return await HomeWidget.isRequestPinWidgetSupported() ?? false;
    } on MissingPluginException {
      return false;
    } on PlatformException {
      return false;
    }
  }

  @override
  Future<void> requestPin() async {
    if (!await canRequestPin()) return;
    await HomeWidget.requestPinWidget(qualifiedAndroidName: androidReceiver);
  }

  Future<void> _ignorePlatformFailure(Future<void> Function() operation) async {
    try {
      await operation();
    } on MissingPluginException {
      // Widget channels are unavailable in unit tests and unsupported shells.
    } on PlatformException {
      // The app remains usable when the current launcher blocks widgets.
    } on Exception {
      // Widget refresh must never block the in-app planning workflow.
    }
  }
}
