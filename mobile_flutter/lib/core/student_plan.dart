import '../data/models.dart';

enum DocumentPreparationStatus { todo, preparing, ready }

extension DocumentPreparationStatusLabel on DocumentPreparationStatus {
  String get label => switch (this) {
    DocumentPreparationStatus.todo => '待準備',
    DocumentPreparationStatus.preparing => '準備中',
    DocumentPreparationStatus.ready => '已完成',
  };
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
    'months': months,
    'monthly_housing': monthlyHousing,
    'monthly_food': monthlyFood,
    'monthly_transport': monthlyTransport,
    'monthly_other': monthlyOther,
    'one_time_costs': oneTimeCosts,
    'scholarship': scholarship,
  };
}

List<SchoolMatch> rankPartnerSchools(
  Iterable<PartnerUniversity> schools,
  StudentPlanProfile profile,
) {
  final matches = schools.map((school) {
    var score = 0;
    final reasons = <String>[];
    final risks = <String>[];

    final collegeMatch =
        school.colleges.isEmpty ||
        school.colleges.contains('全校') ||
        school.colleges.contains(profile.college);
    if (collegeMatch) {
      score += 28;
      reasons.add(school.colleges.contains('全校') ? '全校學生可申請' : '符合所屬學院');
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

    if ((profile.academicScore ?? 0) >= 70) {
      score += 8;
      reasons.add('已達校內 70 分基本參考線');
    } else {
      risks.add('學業成績尚未達校內基本參考線');
    }

    if (school.displayApplicationDeadline.isNotEmpty) score += 3;
    if (school.eligibilityPoints.isNotEmpty) score += 3;
    if (profile.needsScholarship) risks.add('申請前需再確認可搭配補助');

    return SchoolMatch(
      school: school,
      score: score.clamp(0, 100),
      reasons: reasons,
      risks: risks,
    );
  }).toList();

  matches.sort((left, right) {
    final byScore = right.score.compareTo(left.score);
    return byScore != 0
        ? byScore
        : left.school.schoolName.compareTo(right.school.schoolName);
  });
  return matches;
}

double? languageThresholdFor(PartnerUniversity school, String test) {
  final label = switch (test) {
    'ielts' => 'IELTS',
    'toeic' => 'TOEIC',
    'toefl' => 'TOEFL(?:\\s*iBT)?',
    'duolingo' => 'Duolingo',
    _ => '',
  };
  if (label.isEmpty) return null;
  final text = [school.eligibility, ...school.eligibilityPoints].join(' ');
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
