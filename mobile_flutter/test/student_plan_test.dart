import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/core/student_plan.dart';
import 'package:exchange_guide_flutter/core/study_plan_widget_service.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('學校推薦會優先排序符合學院、國家與語言門檻的合作校', () {
    const profile = StudentPlanProfile(
      college: '管理學院',
      degreeLevel: '大學部',
      academicScore: 82,
      languageTest: 'ielts',
      languageScore: 6,
      targetTerm: '2027 秋季',
      preferredCountry: '日本',
      monthlyBudget: 50000,
      needsScholarship: false,
    );
    final matches = rankPartnerSchools([
      _school(
        name: '符合條件大學',
        country: '日本',
        colleges: '管理學院',
        eligibility: 'IELTS 5.5',
      ),
      _school(
        name: '其他大學',
        country: '法國',
        colleges: '工學院',
        eligibility: 'IELTS 7.0',
      ),
    ], profile);

    expect(matches.first.school.schoolName, '符合條件大學');
    expect(matches.first.score, greaterThan(matches.last.score));
    expect(matches.first.reasons, contains('符合所屬學院'));
  });

  test('預算會扣除補助且不產生負數', () {
    const plan = ExchangeBudgetPlan(
      schoolName: '測試大學',
      months: 5,
      monthlyHousing: 20000,
      monthlyFood: 10000,
      monthlyTransport: 3000,
      monthlyOther: 2000,
      oneTimeCosts: 50000,
      scholarship: 60000,
    );

    expect(plan.monthlyTotal, 35000);
    expect(plan.grossTotal, 225000);
    expect(plan.netTotal, 165000);
  });

  test('文件狀態與個人計畫會同步到 Widget 摘要', () async {
    final bridge = _FakeWidgetBridge();
    final store = ExchangeStore(widgetBridge: bridge);
    store.account = AccountProfile.fromJson({
      'id': 'widget-owner',
      'display_name': 'Student',
    });
    await store.savePlanProfile(
      const StudentPlanProfile(
        college: '管理學院',
        degreeLevel: '大學部',
        academicScore: 82,
        languageTest: 'ielts',
        languageScore: 6,
        targetTerm: '2027 秋季',
        preferredCountry: '日本',
        monthlyBudget: 50000,
        needsScholarship: true,
      ),
    );
    await store.setDocumentStatus(
      applicationDocumentLabels.first,
      DocumentPreparationStatus.preparing,
    );
    await store.setDocumentStatus(
      applicationDocumentLabels.first,
      DocumentPreparationStatus.ready,
    );

    expect(
      store.documentStatus(applicationDocumentLabels.first),
      DocumentPreparationStatus.ready,
    );
    expect(store.documentReadyCount, 1);
    expect(bridge.snapshots.last.progressLabel, '準備進度 20%');
    await store.logout();
    expect(bridge.snapshots.last.progressLabel, '尚未登入');
    expect(bridge.snapshots.last.tasks, isEmpty);
    store.dispose();
  });

  test('App 使用平台系統字型，Android Widget 支援桌面縮放', () {
    final theme = buildExchangeTheme();
    expect(theme.textTheme.bodyMedium?.fontFamily, isNull);

    final androidXml = File(
      'android/app/src/main/res/xml/study_plan_widget_definition_home_widget.xml',
    ).readAsStringSync();
    final iosSwift = File(
      'ios/StudyPlanWidgetDefinitionHomeWidget/Widget.swift',
    ).readAsStringSync();
    expect(androidXml, contains('android:widgetCategory="home_screen"'));
    expect(androidXml, contains('android:minResizeWidth="140dp"'));
    expect(iosSwift, contains('.accessoryCircular'));
    expect(iosSwift, contains('.accessoryRectangular'));
  });
}

PartnerUniversity _school({
  required String name,
  required String country,
  required String colleges,
  required String eligibility,
}) {
  return PartnerUniversity.fromJson({
    'school_name': name,
    'country': country,
    'program_type': '交換學生',
    'colleges': colleges,
    'degree_levels': '大學部',
    'eligibility': eligibility,
    'application_deadline': '4 月 15 日',
  });
}

class _FakeWidgetBridge implements StudyPlanWidgetBridge {
  final List<StudyPlanWidgetSnapshot> snapshots = [];

  @override
  Future<bool> canRequestPin() async => true;

  @override
  Future<void> initialize() async {}

  @override
  Future<void> requestPin() async {}

  @override
  Future<void> sync(StudyPlanWidgetSnapshot snapshot) async {
    snapshots.add(snapshot);
  }
}
