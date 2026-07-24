// dart format off
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint

import 'package:home_widget/home_widget.dart';

class StudyPlanWidgetDefinitionHomeWidget {
  const StudyPlanWidgetDefinitionHomeWidget._();

  static const String _$appGroupId = 'group.tw.edu.cgu.exchangeGuideFlutter';

  static const String _$paramPrefix = 'home_widget.StudyPlanWidgetDefinition';

  static Future<void> saveData({
    String? nextTitle,
    String? nextDateLabel,
    String? progressLabel,
  }) {
    return Future.wait([
      if (nextTitle != null) HomeWidget.saveWidgetData<String>('${_$paramPrefix}.nextTitle', nextTitle, appGroupId: _$appGroupId),
      if (nextDateLabel != null) HomeWidget.saveWidgetData<String>('${_$paramPrefix}.nextDateLabel', nextDateLabel, appGroupId: _$appGroupId),
      if (progressLabel != null) HomeWidget.saveWidgetData<String>('${_$paramPrefix}.progressLabel', progressLabel, appGroupId: _$appGroupId),
    ]);
  }

  static Future<void> deleteData({
    bool nextTitle = false,
    bool nextDateLabel = false,
    bool progressLabel = false,
  }) {
    return Future.wait([
      if (nextTitle) HomeWidget.saveWidgetData('${_$paramPrefix}.nextTitle', null, appGroupId: _$appGroupId),
      if (nextDateLabel) HomeWidget.saveWidgetData('${_$paramPrefix}.nextDateLabel', null, appGroupId: _$appGroupId),
      if (progressLabel) HomeWidget.saveWidgetData('${_$paramPrefix}.progressLabel', null, appGroupId: _$appGroupId),
    ]);
  }

  static Future<({String? nextTitle, String? nextDateLabel, String? progressLabel})> getData() async {
    return (
      nextTitle: await HomeWidget.getWidgetData<String>('${_$paramPrefix}.nextTitle', defaultValue: '設定你的交換目標', appGroupId: _$appGroupId),
      nextDateLabel: await HomeWidget.getWidgetData<String>('${_$paramPrefix}.nextDateLabel', defaultValue: '開啟 App 開始規劃', appGroupId: _$appGroupId),
      progressLabel: await HomeWidget.getWidgetData<String>('${_$paramPrefix}.progressLabel', defaultValue: '準備進度 0%', appGroupId: _$appGroupId),
    );
  }


  static Future<bool?> updateWidget() {
    return HomeWidget.updateWidget(
      androidName: 'tw.edu.cgu.exchange_guide_flutter.StudyPlanWidgetDefinitionHomeWidgetReceiver',
      iOSName: 'StudyPlanWidgetDefinitionHomeWidget',
    );
  }
}
