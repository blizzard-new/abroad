import '../data/models.dart';

enum DocumentPreparationStatus { todo, preparing, ready }

extension DocumentPreparationStatusLabel on DocumentPreparationStatus {
  String get label => switch (this) {
    DocumentPreparationStatus.todo => '待準備',
    DocumentPreparationStatus.preparing => '準備中',
    DocumentPreparationStatus.ready => '已完成',
  };
}

enum SchoolConditionStatus { preliminaryMatch, needsConfirmation, mismatch }

class SchoolConditionAssessment {
  const SchoolConditionAssessment({
    required this.status,
    required this.label,
    required this.detail,
  });

  final SchoolConditionStatus status;
  final String label;
  final String detail;
}

const applicationDocumentLabels = [
  '學生赴境外修課申請表',
  '語言能力證明',
  '歷年成績單',
  '出國研修切結書',
  '出國通報單',
];

class StudentPlanProfile {
  const StudentPlanProfile({
    required this.college,
    required this.degreeLevel,
    required this.academicScore,
    required this.languageTest,
    required this.languageScore,
    required this.targetTerm,
    required this.preferredCountry,
    required this.monthlyBudget,
    required this.needsScholarship,
  });

  factory StudentPlanProfile.fromJson(Map<String, dynamic> json) {
    return StudentPlanProfile(
      college: textValue(json['college']),
      degreeLevel: textValue(json['degree_level']),
      academicScore: _doubleValue(json['academic_score']),
      languageTest: textValue(json['language_test']),
      languageScore: _doubleValue(json['language_score']),
      targetTerm: textValue(json['target_term']),
      preferredCountry: textValue(json['preferred_country']),
      monthlyBudget: _doubleValue(json['monthly_budget']),
      needsScholarship: json['needs_scholarship'] == true,
    );
  }

  final String college;
  final String degreeLevel;
  final double? academicScore;
  final String languageTest;
  final double? languageScore;
  final String targetTerm;
  final String preferredCountry;
  final double? monthlyBudget;
  final bool needsScholarship;

  bool get isConfigured =>
      college.isNotEmpty &&
      degreeLevel.isNotEmpty &&
      academicScore != null &&
      languageTest.isNotEmpty;

  String get goalLabel => [
    targetTerm,
    preferredCountry,
  ].where((value) => value.isNotEmpty).join(' · ');

  String get summaryLabel {
    final parts = <String>[
      if (college.isNotEmpty) college,
      if (degreeLevel.isNotEmpty) degreeLevel,
      if (academicScore != null) '平均 ${_scoreGap(academicScore!)}',
      if (languageTest.isNotEmpty && languageTest != 'other')
        '${languageTestLabel(languageTest)}${languageScore != null ? ' ${_scoreGap(languageScore!)}' : ''}',
    ];
    return parts.join(' · ');
  }

  Map<String, dynamic> toJson() => {
    'college': college,
    'degree_level': degreeLevel,
    'academic_score': academicScore,
    'language_test': languageTest,
    'language_score': languageScore,
    'target_term': targetTerm,
    'preferred_country': preferredCountry,
    'monthly_budget': monthlyBudget,
    'needs_scholarship': needsScholarship,
  };
}

class SchoolMatch {
  const SchoolMatch({
    required this.school,
    required this.score,
    required this.reasons,
    required this.risks,
  });

  final PartnerUniversity school;
  final int score;
  final List<String> reasons;
  final List<String> risks;
}

class ExchangeBudgetPlan {
  const ExchangeBudgetPlan({
    this.currency = 'TWD',
    required this.schoolName,
    required this.months,
    required this.monthlyHousing,
    required this.monthlyFood,
    required this.monthlyTransport,
    required this.monthlyOther,
    required this.oneTimeCosts,
    required this.scholarship,
  });

  factory ExchangeBudgetPlan.fromJson(Map<String, dynamic> json) {
    return ExchangeBudgetPlan(
      currency: textValue(json['currency'], 'TWD'),
      schoolName: textValue(json['school_name']),
      months: int.tryParse(textValue(json['months'])) ?? 5,
      monthlyHousing: _doubleValue(json['monthly_housing']) ?? 0,
      monthlyFood: _doubleValue(json['monthly_food']) ?? 0,
      monthlyTransport: _doubleValue(json['monthly_transport']) ?? 0,
      monthlyOther: _doubleValue(json['monthly_other']) ?? 0,
      oneTimeCosts: _doubleValue(json['one_time_costs']) ?? 0,
      scholarship: _doubleValue(json['scholarship']) ?? 0,
    );
  }

  final String schoolName;
  final String currency;
  final int months;
  final double monthlyHousing;
  final double monthlyFood;
  final double monthlyTransport;
  final double monthlyOther;
  final double oneTimeCosts;
  final double scholarship;

  double get monthlyTotal =>
      monthlyHousing + monthlyFood + monthlyTransport + monthlyOther;

  double get grossTotal => monthlyTotal * months + oneTimeCosts;

  double get netTotal => (grossTotal - scholarship).clamp(0, double.infinity);

  Map<String, dynamic> toJson() => {
    'school_name': schoolName,
    'currency': currency,
    'months': months,
    'monthly_housing': monthlyHousing,
    'monthly_food': monthlyFood,
    'monthly_transport': monthlyTransport,
    'monthly_other': monthlyOther,
    'one_time_costs': oneTimeCosts,
    'scholarship': scholarship,
  };
}

bool _collegeMatches(String colleges, String studentCollege) {
  if (colleges.isEmpty || studentCollege.isEmpty) return true;
  if (colleges.contains('全校') ||
      colleges.contains('各院') ||
      colleges.contains('皆可') ||
      colleges.contains('不限')) {
    return true;
  }
  return colleges.contains(studentCollege);
}

/// Evaluates known student profile against an open partner school without
/// inventing probabilities or overriding non-open availability states.
SchoolConditionAssessment? assessSchoolCondition(
  PartnerUniversity school,
  StudentPlanProfile? profile, {
  double? academicScoreMinimum = 70,
}) {
  if (profile == null || !school.isOpenThisCycle) return null;

  if (profile.college.isNotEmpty &&
      school.colleges.isNotEmpty &&
      !_collegeMatches(school.colleges, profile.college)) {
    return SchoolConditionAssessment(
      status: SchoolConditionStatus.mismatch,
      label: '目前條件不符',
      detail: '限 ${school.colleges}',
    );
  }

  if (profile.degreeLevel.isNotEmpty &&
      school.degreeLevels.isNotEmpty &&
      !school.degreeLevels.contains(profile.degreeLevel)) {
    return SchoolConditionAssessment(
      status: SchoolConditionStatus.mismatch,
      label: '目前條件不符',
      detail: '限 ${school.degreeLevels}',
    );
  }

  if (academicScoreMinimum != null &&
      profile.academicScore != null &&
      profile.academicScore! < academicScoreMinimum) {
    return SchoolConditionAssessment(
      status: SchoolConditionStatus.mismatch,
      label: '目前條件不符',
      detail: '未達校內平均 ${_scoreGap(academicScoreMinimum)}',
    );
  }

  final threshold = languageThresholdFor(school, profile.languageTest);
  if (threshold != null && profile.languageScore != null) {
    if (profile.languageScore! < threshold) {
      return SchoolConditionAssessment(
        status: SchoolConditionStatus.mismatch,
        label: '目前條件不符',
        detail:
            '${languageTestLabel(profile.languageTest)} 尚差 ${_scoreGap(threshold - profile.languageScore!)}',
      );
    }
    return SchoolConditionAssessment(
      status: SchoolConditionStatus.preliminaryMatch,
      label: '已知條件初步相符',
      detail: '${languageTestLabel(profile.languageTest)} 已達公開門檻',
    );
  }

  return const SchoolConditionAssessment(
    status: SchoolConditionStatus.needsConfirmation,
    label: '資格待確認',
    detail: '需核對簡章語檢或院系細則',
  );
}

List<SchoolMatch> rankPartnerSchools(
  Iterable<PartnerUniversity> schools,
  StudentPlanProfile profile, {
  double? academicScoreMinimum = 70,
}) {
  final matches = schools.map((school) {
    var score = 0;
    final reasons = <String>[];
    final risks = <String>[];

    if (!school.isOpenThisCycle) {
      risks.add('本期狀態：${school.availabilityLabel}');
    }

    final collegeMatch = _collegeMatches(school.colleges, profile.college);
    if (collegeMatch) {
      score += 28;
      reasons.add(
        school.colleges.contains('全校') || school.colleges.contains('皆可')
            ? '全校學生可申請'
            : '符合所屬學院',
      );
    } else {
      risks.add('合作範圍可能不包含${profile.college}');
    }

    final degreeMatch =
        school.degreeLevels.isEmpty ||
        school.degreeLevels.contains(profile.degreeLevel);
    if (degreeMatch) {
      score += 20;
      reasons.add('符合${profile.degreeLevel}學制');
    } else {
      risks.add('目前學制可能不在開放範圍');
    }

    if (profile.preferredCountry.isNotEmpty) {
      if (school.country.contains(profile.preferredCountry)) {
        score += 20;
        reasons.add('位於偏好國家');
      } else {
        risks.add('不在目前偏好國家');
      }
    } else {
      score += 8;
    }

    final threshold = languageThresholdFor(school, profile.languageTest);
    if (profile.languageTest == 'other') {
      risks.add('語言測驗尚待確認');
    } else if (threshold == null) {
      score += 6;
      risks.add('合作校未提供可直接比對的語言分數');
    } else if (profile.languageScore == null) {
      risks.add('尚未填寫語言分數');
    } else if (profile.languageScore! >= threshold) {
      score += 18;
      reasons.add('${languageTestLabel(profile.languageTest)} 已達公開門檻');
    } else {
      risks.add(
        '${languageTestLabel(profile.languageTest)} 尚差 ${_scoreGap(threshold - profile.languageScore!)}',
      );
    }

    if (academicScoreMinimum == null) {
      if ((profile.academicScore ?? 0) > 0) {
        score += 8;
        reasons.add('已填寫學業成績供合作校門檻比對');
      }
    } else if ((profile.academicScore ?? 0) >= academicScoreMinimum) {
      score += 8;
      reasons.add(
        academicScoreMinimum == 70
            ? '已達校內 70 分基本參考線'
            : '已達校內 ${_scoreGap(academicScoreMinimum)} 基本參考線',
      );
    } else {
      risks.add('學業成績尚未達校內基本參考線');
    }

    if (school.displayApplicationDeadline.isNotEmpty) score += 3;
    if (school.eligibilityPoints.isNotEmpty) score += 3;
    if (profile.needsScholarship) risks.add('申請前需再確認可搭配補助');

    final adjustedScore = school.isOpenThisCycle
        ? score.clamp(0, 100)
        : (score - 40).clamp(0, 100);

    return SchoolMatch(
      school: school,
      score: adjustedScore,
      reasons: reasons,
      risks: risks,
    );
  }).toList();

  matches.sort((left, right) {
    if (left.school.isOpenThisCycle != right.school.isOpenThisCycle) {
      return left.school.isOpenThisCycle ? -1 : 1;
    }
    final byScore = right.score.compareTo(left.score);
    return byScore != 0
        ? byScore
        : left.school.schoolName.compareTo(right.school.schoolName);
  });
  return matches;
}

double? languageThresholdFor(PartnerUniversity school, String test) {
  final normalizedTest = test.trim().toLowerCase();
  if (normalizedTest.isEmpty || normalizedTest == 'other') return null;

  for (final cond in school.languageConditions) {
    final condName = '${cond.test} ${cond.testVariant}'.toLowerCase();
    final matches = switch (normalizedTest) {
      'ielts' => condName.contains('ielts'),
      'toeic' => condName.contains('toeic'),
      'toefl' => condName.contains('toefl'),
      'duolingo' => condName.contains('duolingo'),
      _ => false,
    };
    if (matches && cond.minimumScore != null) {
      return cond.minimumScore;
    }
  }

  final label = switch (normalizedTest) {
    'ielts' => 'IELTS',
    'toeic' => 'TOEIC',
    'toefl' => 'TOEFL(?:\\s*iBT)?',
    'duolingo' => 'Duolingo',
    _ => '',
  };
  if (label.isEmpty) return null;
  final text = [
    school.languageRequirement,
    school.eligibility,
    ...school.eligibilityPoints,
  ].join(' ');
  final match = RegExp(
    '$label[^0-9]{0,24}([0-9]{1,3}(?:\\.[0-9])?)',
    caseSensitive: false,
  ).firstMatch(text);
  return double.tryParse(match?.group(1) ?? '');
}

String languageTestLabel(String value) => switch (value) {
  'ielts' => 'IELTS',
  'toeic' => 'TOEIC',
  'toefl' => 'TOEFL iBT',
  'duolingo' => 'Duolingo',
  _ => '語言條件',
};

double? _doubleValue(dynamic value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '');
}

String _scoreGap(double value) {
  if (value == value.roundToDouble()) return value.toInt().toString();
  return value.toStringAsFixed(1);
}
