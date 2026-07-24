import 'dart:convert';
import 'dart:typed_data';

typedef JsonMap = Map<String, dynamic>;

JsonMap jsonMap(dynamic value) => value is Map<String, dynamic> ? value : {};

List<JsonMap> jsonMapList(dynamic value) => value is List
    ? value
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList()
    : const [];

List<String> stringList(dynamic value) => value is List
    ? value
          .where((item) => item != null && item.toString().trim().isNotEmpty)
          .map((item) => item.toString().trim())
          .toList()
    : const [];

String textValue(dynamic value, [String fallback = '']) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

int intValue(dynamic value, [int fallback = 0]) =>
    value is int ? value : int.tryParse(value?.toString() ?? '') ?? fallback;

class AuthProviderStatus {
  const AuthProviderStatus({
    required this.provider,
    required this.enabled,
    required this.label,
  });

  factory AuthProviderStatus.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AuthProviderStatus(
      provider: textValue(json['provider']),
      enabled: json['enabled'] == true,
      label: textValue(json['label']),
    );
  }

  final String provider;
  final bool enabled;
  final String label;
}

class StudentVerificationResult {
  const StudentVerificationResult({
    required this.verificationToken,
    required this.schoolName,
    required this.checks,
    required this.expiresAt,
    required this.imagesRetained,
  });

  factory StudentVerificationResult.fromJson(dynamic value) {
    final json = jsonMap(value);
    return StudentVerificationResult(
      verificationToken: textValue(json['verification_token']),
      schoolName: textValue(json['school_name']),
      checks: stringList(json['checks']),
      expiresAt: textValue(json['expires_at']),
      imagesRetained: json['images_retained'] == true,
    );
  }

  final String verificationToken;
  final String schoolName;
  final List<String> checks;
  final String expiresAt;
  final bool imagesRetained;
}

class AccountProfile {
  const AccountProfile({
    required this.id,
    required this.email,
    required this.displayName,
    required this.avatarUrl,
    required this.homeUniversity,
    required this.targetCountries,
    required this.applicationStage,
    required this.schoolEmailVerified,
    required this.studentStatusVerified,
    required this.verifiedUniversity,
    required this.studentVerifiedAt,
    required this.providers,
    required this.followedBoards,
  });

  factory AccountProfile.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AccountProfile(
      id: textValue(json['id']),
      email: textValue(json['email']),
      displayName: textValue(json['display_name'], '交換學生'),
      avatarUrl: textValue(json['avatar_url']),
      homeUniversity: textValue(json['home_university'], '長庚大學'),
      targetCountries: stringList(json['target_countries']),
      applicationStage: textValue(json['application_stage'], 'exploring'),
      schoolEmailVerified: json['school_email_verified'] == true,
      studentStatusVerified: json['student_status_verified'] == true,
      verifiedUniversity: textValue(json['verified_university']),
      studentVerifiedAt: textValue(json['student_verified_at']),
      providers: stringList(json['providers']),
      followedBoards: stringList(json['followed_boards']),
    );
  }

  final String id;
  final String email;
  final String displayName;
  final String avatarUrl;
  final String homeUniversity;
  final List<String> targetCountries;
  final String applicationStage;
  final bool schoolEmailVerified;
  final bool studentStatusVerified;
  final String verifiedUniversity;
  final String studentVerifiedAt;
  final List<String> providers;
  final List<String> followedBoards;
}

class AccountSession {
  const AccountSession({
    required this.accessToken,
    required this.expiresAt,
    required this.profile,
  });

  factory AccountSession.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AccountSession(
      accessToken: textValue(json['access_token']),
      expiresAt: textValue(json['expires_at']),
      profile: AccountProfile.fromJson(json['profile']),
    );
  }

  final String accessToken;
  final String expiresAt;
  final AccountProfile profile;
}

class SourceReference {
  const SourceReference({
    required this.title,
    required this.sourceUrl,
    this.category = '',
  });

  factory SourceReference.fromJson(dynamic value) {
    final json = jsonMap(value);
    return SourceReference(
      title: textValue(json['title'], '官方來源'),
      sourceUrl: textValue(json['source_url']),
      category: textValue(json['category']),
    );
  }

  final String title;
  final String sourceUrl;
  final String category;
}

class StudentInfoItem {
  const StudentInfoItem({
    required this.title,
    required this.details,
    this.source,
  });

  factory StudentInfoItem.fromJson(dynamic value) {
    final json = jsonMap(value);
    final source = json['source'];
    return StudentInfoItem(
      title: textValue(json['title']),
      details: stringList(json['details']),
      source: source == null ? null : SourceReference.fromJson(source),
    );
  }

  final String title;
  final List<String> details;
  final SourceReference? source;
}

class RuleExplanation {
  const RuleExplanation({
    required this.title,
    required this.summary,
    required this.keyPoints,
    required this.appliesTo,
    required this.source,
    required this.documentUrl,
    required this.fullTextExtracted,
  });

  factory RuleExplanation.fromJson(dynamic value) {
    final json = jsonMap(value);
    return RuleExplanation(
      title: textValue(json['title']),
      summary: textValue(json['summary']),
      keyPoints: stringList(json['key_points']),
      appliesTo: stringList(json['applies_to']),
      source: SourceReference.fromJson(json['source']),
      documentUrl: textValue(json['document_url']),
      fullTextExtracted: json['full_text_extracted'] == true,
    );
  }

  final String title;
  final String summary;
  final List<String> keyPoints;
  final List<String> appliesTo;
  final SourceReference source;
  final String documentUrl;
  final bool fullTextExtracted;
}

class PartnerStudentSummary {
  const PartnerStudentSummary({
    required this.studyPeriod,
    required this.applicationDeadline,
    required this.eligibilityPoints,
    required this.applicationSteps,
    required this.tuitionPoints,
    required this.translatedFromEnglish,
  });

  const PartnerStudentSummary.empty()
    : studyPeriod = '',
      applicationDeadline = '',
      eligibilityPoints = const [],
      applicationSteps = const [],
      tuitionPoints = const [],
      translatedFromEnglish = false;

  factory PartnerStudentSummary.fromJson(dynamic value) {
    final json = jsonMap(value);
    return PartnerStudentSummary(
      studyPeriod: textValue(json['study_period']),
      applicationDeadline: textValue(json['application_deadline']),
      eligibilityPoints: stringList(json['eligibility_points']),
      applicationSteps: stringList(json['application_steps']),
      tuitionPoints: stringList(json['tuition_points']),
      translatedFromEnglish: json['translated_from_english'] == true,
    );
  }

  final String studyPeriod;
  final String applicationDeadline;
  final List<String> eligibilityPoints;
  final List<String> applicationSteps;
  final List<String> tuitionPoints;
  final bool translatedFromEnglish;
}

class PartnerUniversity {
  const PartnerUniversity({
    required this.schoolName,
    required this.country,
    required this.programType,
    required this.colleges,
    required this.degreeLevels,
    required this.website,
    required this.studyPeriod,
    required this.quota,
    required this.eligibility,
    required this.applicationDeadline,
    required this.applicationInfo,
    required this.tuitionInfo,
    required this.rankingInfo,
    required this.sourceUrl,
    required this.imageUrl,
    required this.imageSourceUrl,
    required this.imagePageUrl,
    required this.imageStatus,
    required this.studentSummaryZh,
  });

  factory PartnerUniversity.fromJson(dynamic value) {
    final json = jsonMap(value);
    return PartnerUniversity(
      schoolName: textValue(json['school_name'], '合作學校'),
      country: textValue(json['country'], '國家待確認'),
      programType: textValue(json['program_type'], '交換學生'),
      colleges: textValue(json['colleges']),
      degreeLevels: textValue(json['degree_levels']),
      website: textValue(json['website']),
      studyPeriod: textValue(json['study_period']),
      quota: textValue(json['quota']),
      eligibility: textValue(json['eligibility']),
      applicationDeadline: textValue(json['application_deadline']),
      applicationInfo: textValue(json['application_info']),
      tuitionInfo: textValue(json['tuition_info']),
      rankingInfo: textValue(json['ranking_info']),
      sourceUrl: textValue(json['source_url']),
      imageUrl: textValue(
        json['image_url'] ?? json['photo_url'] ?? json['og_image_url'],
      ),
      imageSourceUrl: textValue(json['image_source_url']),
      imagePageUrl: textValue(json['image_page_url']),
      imageStatus: textValue(json['image_status'], 'missing'),
      studentSummaryZh: PartnerStudentSummary.fromJson(
        json['student_summary_zh'],
      ),
    );
  }

  final String schoolName;
  final String country;
  final String programType;
  final String colleges;
  final String degreeLevels;
  final String website;
  final String studyPeriod;
  final String quota;
  final String eligibility;
  final String applicationDeadline;
  final String applicationInfo;
  final String tuitionInfo;
  final String rankingInfo;
  final String sourceUrl;
  final String imageUrl;
  final String imageSourceUrl;
  final String imagePageUrl;
  final String imageStatus;
  final PartnerStudentSummary studentSummaryZh;

  String get displayStudyPeriod => studentSummaryZh.studyPeriod.isNotEmpty
      ? studentSummaryZh.studyPeriod
      : studyPeriod;

  String get displayApplicationDeadline =>
      studentSummaryZh.applicationDeadline.isNotEmpty
      ? studentSummaryZh.applicationDeadline
      : applicationDeadline;

  List<String> get eligibilityPoints =>
      studentSummaryZh.eligibilityPoints.isNotEmpty
      ? studentSummaryZh.eligibilityPoints
      : [if (eligibility.isNotEmpty) eligibility];

  List<String> get applicationSteps =>
      studentSummaryZh.applicationSteps.isNotEmpty
      ? studentSummaryZh.applicationSteps
      : [if (applicationInfo.isNotEmpty) applicationInfo];

  List<String> get tuitionPoints => studentSummaryZh.tuitionPoints.isNotEmpty
      ? studentSummaryZh.tuitionPoints
      : [if (tuitionInfo.isNotEmpty) tuitionInfo];

  String get mobileListSummary => [
    programType,
    colleges,
    degreeLevels,
  ].where((item) => item.trim().isNotEmpty).join(' · ');

  PartnerUniversity withVisual(SchoolVisual visual, String imageUrl) {
    return PartnerUniversity(
      schoolName: schoolName,
      country: country,
      programType: programType,
      colleges: colleges,
      degreeLevels: degreeLevels,
      website: website,
      studyPeriod: studyPeriod,
      quota: quota,
      eligibility: eligibility,
      applicationDeadline: applicationDeadline,
      applicationInfo: applicationInfo,
      tuitionInfo: tuitionInfo,
      rankingInfo: rankingInfo,
      sourceUrl: sourceUrl,
      imageUrl: imageUrl,
      imageSourceUrl: visual.imageSourceUrl,
      imagePageUrl: visual.officialPageUrl,
      imageStatus: visual.status,
      studentSummaryZh: studentSummaryZh,
    );
  }

  String get searchableText => [
    schoolName,
    country,
    programType,
    eligibility,
    displayApplicationDeadline,
    ...eligibilityPoints,
  ].join(' ').toLowerCase();
}

class SchoolVisual {
  const SchoolVisual({
    required this.schoolName,
    required this.officialPageUrl,
    required this.imageSourceUrl,
    required this.localPath,
    required this.status,
  });

  factory SchoolVisual.fromJson(dynamic value) {
    final json = jsonMap(value);
    return SchoolVisual(
      schoolName: textValue(json['school_name']),
      officialPageUrl: textValue(json['official_page_url']),
      imageSourceUrl: textValue(json['image_source_url']),
      localPath: textValue(json['local_path']),
      status: textValue(json['status'], 'missing'),
    );
  }

  final String schoolName;
  final String officialPageUrl;
  final String imageSourceUrl;
  final String localPath;
  final String status;
}

class StudentDashboard {
  const StudentDashboard({
    required this.schoolName,
    required this.lastChecked,
    required this.applicationPeriods,
    required this.programOverview,
    required this.eligibility,
    required this.languageRequirements,
    required this.requiredDocuments,
    required this.scholarshipInfo,
    required this.ruleExplanations,
    required this.partnerUniversities,
    required this.sources,
  });

  factory StudentDashboard.fromJson(dynamic value) {
    final json = jsonMap(value);
    List<StudentInfoItem> items(String key) =>
        jsonMapList(json[key]).map(StudentInfoItem.fromJson).toList();
    final rules = [
      ...jsonMapList(json['rule_explanations']),
      ...jsonMapList(json['document_explanations']),
    ];
    return StudentDashboard(
      schoolName: textValue(json['school_name'], '長庚大學'),
      lastChecked: textValue(json['last_checked']),
      applicationPeriods: items('application_periods'),
      programOverview: items('program_overview'),
      eligibility: items('eligibility'),
      languageRequirements: items('language_requirements'),
      requiredDocuments: items('required_documents'),
      scholarshipInfo: items('scholarship_info'),
      ruleExplanations: rules.map(RuleExplanation.fromJson).toList(),
      partnerUniversities: jsonMapList(
        json['partner_universities'],
      ).map(PartnerUniversity.fromJson).toList(),
      sources: jsonMapList(
        json['sources'],
      ).map(SourceReference.fromJson).toList(),
    );
  }

  final String schoolName;
  final String lastChecked;
  final List<StudentInfoItem> applicationPeriods;
  final List<StudentInfoItem> programOverview;
  final List<StudentInfoItem> eligibility;
  final List<StudentInfoItem> languageRequirements;
  final List<StudentInfoItem> requiredDocuments;
  final List<StudentInfoItem> scholarshipInfo;
  final List<RuleExplanation> ruleExplanations;
  final List<PartnerUniversity> partnerUniversities;
  final List<SourceReference> sources;

  StudentDashboard withSchoolVisuals(
    Map<String, SchoolVisual> visuals,
    String Function(String) resolveUrl,
  ) {
    return StudentDashboard(
      schoolName: schoolName,
      lastChecked: lastChecked,
      applicationPeriods: applicationPeriods,
      programOverview: programOverview,
      eligibility: eligibility,
      languageRequirements: languageRequirements,
      requiredDocuments: requiredDocuments,
      scholarshipInfo: scholarshipInfo,
      ruleExplanations: ruleExplanations,
      partnerUniversities: partnerUniversities.map((school) {
        final visual = visuals[school.schoolName];
        if (visual == null ||
            visual.status != 'verified' ||
            visual.localPath.isEmpty) {
          return school;
        }
        return school.withVisual(visual, resolveUrl(visual.localPath));
      }).toList(),
      sources: sources,
    );
  }
}

class AdvisorProfile {
  const AdvisorProfile({
    this.schoolName = '長庚大學',
    this.college = '',
    this.department = '',
    this.currentYear = '',
    this.degreeLevel = '',
    this.academicScore,
    this.languageTest = '',
    this.languageScore,
    this.targetTerm = '',
    this.preferredCountry = '',
    this.monthlyBudget,
    this.needsScholarship = false,
    this.question = '',
  });

  final String schoolName;
  final String college;
  final String department;
  final String currentYear;
  final String degreeLevel;
  final double? academicScore;
  final String languageTest;
  final double? languageScore;
  final String targetTerm;
  final String preferredCountry;
  final double? monthlyBudget;
  final bool needsScholarship;
  final String question;

  JsonMap toJson() => {
    'school_name': schoolName,
    if (college.isNotEmpty) 'college': college,
    if (department.isNotEmpty) 'department': department,
    if (currentYear.isNotEmpty) 'current_year': currentYear,
    if (degreeLevel.isNotEmpty) 'degree_level': degreeLevel,
    if (academicScore != null) 'academic_score': academicScore,
    if (languageTest.isNotEmpty) 'language_test': languageTest,
    if (languageScore != null) 'language_score': languageScore,
    if (targetTerm.isNotEmpty) 'target_term': targetTerm,
    if (preferredCountry.isNotEmpty) 'preferred_country': preferredCountry,
    if (monthlyBudget != null) 'monthly_budget': monthlyBudget,
    'needs_scholarship': needsScholarship,
    if (question.isNotEmpty) 'question': question,
  };
}

class AdvisorCitation {
  const AdvisorCitation({
    required this.title,
    required this.sourceUrl,
    required this.section,
    required this.publishedAt,
    required this.lastChecked,
  });

  factory AdvisorCitation.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AdvisorCitation(
      title: textValue(json['title'], '官方來源'),
      sourceUrl: textValue(json['source_url']),
      section: textValue(json['section']),
      publishedAt: textValue(json['published_at']),
      lastChecked: textValue(json['last_checked']),
    );
  }

  final String title;
  final String sourceUrl;
  final String section;
  final String publishedAt;
  final String lastChecked;
}

class AdvisorAnswer {
  const AdvisorAnswer({
    required this.question,
    required this.answer,
    required this.keyPoints,
    required this.sources,
    required this.evidenceStatus,
    required this.aiEnhanced,
  });

  factory AdvisorAnswer.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AdvisorAnswer(
      question: textValue(json['question']),
      answer: textValue(json['answer']),
      keyPoints: stringList(json['key_points']),
      sources: jsonMapList(
        json['sources'],
      ).map(AdvisorCitation.fromJson).toList(),
      evidenceStatus: textValue(json['evidence_status'], 'not_found'),
      aiEnhanced: json['ai_enhanced'] == true,
    );
  }

  final String question;
  final String answer;
  final List<String> keyPoints;
  final List<AdvisorCitation> sources;
  final String evidenceStatus;
  final bool aiEnhanced;
}

class AdvisorSchoolMatch {
  const AdvisorSchoolMatch({
    required this.schoolName,
    required this.country,
    required this.matchScore,
    required this.fitLabel,
    required this.reasons,
    required this.gaps,
    required this.sourceUrls,
    required this.imageUrl,
  });

  factory AdvisorSchoolMatch.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AdvisorSchoolMatch(
      schoolName: textValue(json['school_name']),
      country: textValue(json['country']),
      matchScore: intValue(json['match_score']),
      fitLabel: textValue(json['fit_label'], '待確認'),
      reasons: stringList(json['reasons']),
      gaps: stringList(json['gaps']),
      sourceUrls: stringList(json['source_urls']),
      imageUrl: textValue(json['image_url']),
    );
  }

  final String schoolName;
  final String country;
  final int matchScore;
  final String fitLabel;
  final List<String> reasons;
  final List<String> gaps;
  final List<String> sourceUrls;
  final String imageUrl;
}

class AdvisorTask {
  const AdvisorTask({
    required this.id,
    required this.title,
    required this.detail,
    required this.category,
    required this.priority,
    required this.dueDate,
    required this.daysRemaining,
    required this.sourceUrl,
  });

  factory AdvisorTask.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AdvisorTask(
      id: textValue(json['id']),
      title: textValue(json['title']),
      detail: textValue(json['detail']),
      category: textValue(json['category'], 'other'),
      priority: textValue(json['priority'], 'medium'),
      dueDate: textValue(json['due_date']),
      daysRemaining: json['days_remaining'] == null
          ? null
          : intValue(json['days_remaining']),
      sourceUrl: textValue(json['source_url']),
    );
  }

  final String id;
  final String title;
  final String detail;
  final String category;
  final String priority;
  final String dueDate;
  final int? daysRemaining;
  final String sourceUrl;
}

class AdvisorPlan {
  const AdvisorPlan({
    required this.schoolName,
    required this.generatedAt,
    required this.mode,
    required this.summary,
    required this.qualification,
    required this.recommendations,
    required this.tasks,
    required this.answer,
    required this.disclaimer,
  });

  factory AdvisorPlan.fromJson(dynamic value) {
    final json = jsonMap(value);
    final answer = json['answer'];
    return AdvisorPlan(
      schoolName: textValue(json['school_name'], '長庚大學'),
      generatedAt: textValue(json['generated_at']),
      mode: textValue(json['mode'], 'source_grounded'),
      summary: textValue(json['summary']),
      qualification: stringList(json['qualification']),
      recommendations: jsonMapList(
        json['recommendations'],
      ).map(AdvisorSchoolMatch.fromJson).toList(),
      tasks: jsonMapList(json['tasks']).map(AdvisorTask.fromJson).toList(),
      answer: answer is Map ? AdvisorAnswer.fromJson(answer) : null,
      disclaimer: textValue(json['disclaimer']),
    );
  }

  final String schoolName;
  final String generatedAt;
  final String mode;
  final String summary;
  final List<String> qualification;
  final List<AdvisorSchoolMatch> recommendations;
  final List<AdvisorTask> tasks;
  final AdvisorAnswer? answer;
  final String disclaimer;
}

class DocumentCheckIssue {
  const DocumentCheckIssue({
    required this.severity,
    required this.code,
    required this.title,
    required this.detail,
  });

  factory DocumentCheckIssue.fromJson(dynamic value) {
    final json = jsonMap(value);
    return DocumentCheckIssue(
      severity: textValue(json['severity'], 'info'),
      code: textValue(json['code']),
      title: textValue(json['title']),
      detail: textValue(json['detail']),
    );
  }

  final String severity;
  final String code;
  final String title;
  final String detail;
}

class DocumentCheckResult {
  const DocumentCheckResult({
    required this.fileName,
    required this.documentType,
    required this.summary,
    required this.pageCount,
    required this.characterCount,
    required this.wordCount,
    required this.completenessScore,
    required this.checksPassed,
    required this.issues,
    required this.suggestions,
    required this.extractedPreview,
    required this.aiEnhanced,
    required this.privacyNote,
  });

  factory DocumentCheckResult.fromJson(dynamic value) {
    final json = jsonMap(value);
    return DocumentCheckResult(
      fileName: textValue(json['file_name']),
      documentType: textValue(json['document_type']),
      summary: textValue(json['summary']),
      pageCount: intValue(json['page_count'], 1),
      characterCount: intValue(json['character_count']),
      wordCount: intValue(json['word_count']),
      completenessScore: intValue(json['completeness_score']),
      checksPassed: stringList(json['checks_passed']),
      issues: jsonMapList(
        json['issues'],
      ).map(DocumentCheckIssue.fromJson).toList(),
      suggestions: stringList(json['suggestions']),
      extractedPreview: textValue(json['extracted_preview']),
      aiEnhanced: json['ai_enhanced'] == true,
      privacyNote: textValue(json['privacy_note']),
    );
  }

  final String fileName;
  final String documentType;
  final String summary;
  final int pageCount;
  final int characterCount;
  final int wordCount;
  final int completenessScore;
  final List<String> checksPassed;
  final List<DocumentCheckIssue> issues;
  final List<String> suggestions;
  final String extractedPreview;
  final bool aiEnhanced;
  final String privacyNote;
}

class DocumentRewriteResult {
  const DocumentRewriteResult({
    required this.action,
    required this.draft,
    required this.changes,
    required this.warnings,
    required this.aiEnhanced,
    required this.disclaimer,
  });

  factory DocumentRewriteResult.fromJson(dynamic value) {
    final json = jsonMap(value);
    return DocumentRewriteResult(
      action: textValue(json['action']),
      draft: textValue(json['draft']),
      changes: stringList(json['changes']),
      warnings: stringList(json['warnings']),
      aiEnhanced: json['ai_enhanced'] == true,
      disclaimer: textValue(json['disclaimer']),
    );
  }

  final String action;
  final String draft;
  final List<String> changes;
  final List<String> warnings;
  final bool aiEnhanced;
  final String disclaimer;
}

class DeadlineRecord {
  const DeadlineRecord({
    required this.title,
    required this.sourceUrl,
    required this.publishedAt,
    required this.category,
    required this.snippets,
  });

  factory DeadlineRecord.fromJson(dynamic value) {
    final json = jsonMap(value);
    return DeadlineRecord(
      title: textValue(json['title'], '申請時程'),
      sourceUrl: textValue(json['source_url']),
      publishedAt: textValue(json['published_at']),
      category: textValue(json['category'], 'deadline'),
      snippets: stringList(json['snippets']),
    );
  }

  final String title;
  final String sourceUrl;
  final String publishedAt;
  final String category;
  final List<String> snippets;
}

class ApplicationStep {
  const ApplicationStep({
    required this.order,
    required this.phase,
    required this.title,
    required this.responsibleParty,
    required this.timing,
    required this.summary,
    required this.details,
    required this.requiredDocuments,
    required this.actionUrl,
    required this.sourceUrls,
    required this.needsConfirmation,
  });

  factory ApplicationStep.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ApplicationStep(
      order: json['order'] is int ? json['order'] as int : 0,
      phase: textValue(json['phase']),
      title: textValue(json['title']),
      responsibleParty: textValue(json['responsible_party']),
      timing: textValue(json['timing']),
      summary: textValue(json['summary']),
      details: stringList(json['details']),
      requiredDocuments: stringList(json['required_documents']),
      actionUrl: textValue(json['action_url']),
      sourceUrls: stringList(json['source_urls']),
      needsConfirmation: json['needs_confirmation'] == true,
    );
  }

  final int order;
  final String phase;
  final String title;
  final String responsibleParty;
  final String timing;
  final String summary;
  final List<String> details;
  final List<String> requiredDocuments;
  final String actionUrl;
  final List<String> sourceUrls;
  final bool needsConfirmation;
}

class ApplicationWorkflow {
  const ApplicationWorkflow({
    required this.schoolName,
    required this.country,
    required this.programType,
    required this.steps,
    required this.lastChecked,
    required this.coverageStatus,
    required this.coverageNote,
    required this.disclaimer,
  });

  factory ApplicationWorkflow.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ApplicationWorkflow(
      schoolName: textValue(json['school_name']),
      country: textValue(json['country']),
      programType: textValue(json['program_type']),
      steps: jsonMapList(json['steps']).map(ApplicationStep.fromJson).toList()
        ..sort((a, b) => a.order.compareTo(b.order)),
      lastChecked: textValue(json['last_checked']),
      coverageStatus: textValue(json['coverage_status']),
      coverageNote: textValue(json['coverage_note']),
      disclaimer: textValue(json['disclaimer']),
    );
  }

  final String schoolName;
  final String country;
  final String programType;
  final List<ApplicationStep> steps;
  final String lastChecked;
  final String coverageStatus;
  final String coverageNote;
  final String disclaimer;
}

class ExperienceHighlight {
  const ExperienceHighlight({
    required this.theme,
    required this.title,
    required this.summary,
    required this.sourceCount,
    required this.keyPoints,
    required this.sourceUrls,
  });

  factory ExperienceHighlight.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ExperienceHighlight(
      theme: textValue(json['theme']),
      title: textValue(json['title']),
      summary: textValue(json['summary']),
      sourceCount: json['source_count'] is int
          ? json['source_count'] as int
          : 0,
      keyPoints: stringList(json['key_points']),
      sourceUrls: stringList(json['source_urls']),
    );
  }

  final String theme;
  final String title;
  final String summary;
  final int sourceCount;
  final List<String> keyPoints;
  final List<String> sourceUrls;

  bool get hasConcreteSummary => keyPoints.isNotEmpty;
}

class ExperienceSource {
  const ExperienceSource({
    required this.title,
    required this.sourceUrl,
    required this.sourceType,
    required this.platform,
    required this.summary,
    required this.themes,
  });

  factory ExperienceSource.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ExperienceSource(
      title: textValue(json['title'], '學生分享'),
      sourceUrl: textValue(json['source_url']),
      sourceType: textValue(json['source_type'], 'article'),
      platform: textValue(json['platform']),
      summary: textValue(json['summary']),
      themes: stringList(json['themes']),
    );
  }

  final String title;
  final String sourceUrl;
  final String sourceType;
  final String platform;
  final String summary;
  final List<String> themes;
}

class ExperienceDigest {
  const ExperienceDigest({
    required this.schoolName,
    required this.totalSources,
    required this.articleCount,
    required this.videoCount,
    required this.communityCount,
    required this.highlights,
    required this.sources,
    required this.coverageNote,
    required this.disclaimer,
  });

  factory ExperienceDigest.fromJson(dynamic value) {
    final json = jsonMap(value);
    final highlights =
        jsonMapList(
          json['highlights'],
        ).map(ExperienceHighlight.fromJson).toList()..sort((a, b) {
          final aRank = a.hasConcreteSummary ? 2 : (a.sourceCount > 0 ? 1 : 0);
          final bRank = b.hasConcreteSummary ? 2 : (b.sourceCount > 0 ? 1 : 0);
          final rank = bRank.compareTo(aRank);
          return rank != 0 ? rank : b.sourceCount.compareTo(a.sourceCount);
        });
    return ExperienceDigest(
      schoolName: textValue(json['school_name']),
      totalSources: json['total_sources'] is int
          ? json['total_sources'] as int
          : 0,
      articleCount: json['article_count'] is int
          ? json['article_count'] as int
          : 0,
      videoCount: json['video_count'] is int ? json['video_count'] as int : 0,
      communityCount: json['community_count'] is int
          ? json['community_count'] as int
          : 0,
      highlights: highlights,
      sources: jsonMapList(
        json['sources'],
      ).map(ExperienceSource.fromJson).toList(),
      coverageNote: textValue(json['coverage_note']),
      disclaimer: textValue(json['disclaimer']),
    );
  }

  final String schoolName;
  final int totalSources;
  final int articleCount;
  final int videoCount;
  final int communityCount;
  final List<ExperienceHighlight> highlights;
  final List<ExperienceSource> sources;
  final String coverageNote;
  final String disclaimer;
}

class AnonymousIdentity {
  const AnonymousIdentity({
    required this.id,
    required this.displayName,
    required this.accessToken,
    this.accountId = '',
  });

  factory AnonymousIdentity.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AnonymousIdentity(
      id: textValue(json['id']),
      displayName: textValue(json['display_name']),
      accessToken: textValue(json['access_token']),
      accountId: textValue(json['account_id']),
    );
  }

  final String id;
  final String displayName;
  final String accessToken;
  final String accountId;
}

class CommunityPost {
  const CommunityPost({
    required this.id,
    required this.schoolName,
    required this.authorId,
    required this.displayName,
    required this.postType,
    required this.topic,
    required this.country,
    required this.academicYear,
    required this.applicationStage,
    required this.title,
    required this.body,
    required this.commentCount,
    required this.createdAt,
  });

  factory CommunityPost.fromJson(dynamic value) {
    final json = jsonMap(value);
    return CommunityPost(
      id: textValue(json['id']),
      schoolName: textValue(json['school_name']),
      authorId: textValue(json['author_id']),
      displayName: textValue(json['display_name'], '匿名同學'),
      postType: textValue(json['post_type'], 'discussion'),
      topic: textValue(json['topic'], 'application'),
      country: textValue(json['country']),
      academicYear: textValue(json['academic_year']),
      applicationStage: textValue(json['application_stage']),
      title: textValue(json['title']),
      body: textValue(json['body']),
      commentCount: json['comment_count'] is int
          ? json['comment_count'] as int
          : 0,
      createdAt: textValue(json['created_at']),
    );
  }

  final String id;
  final String schoolName;
  final String authorId;
  final String displayName;
  final String postType;
  final String topic;
  final String country;
  final String academicYear;
  final String applicationStage;
  final String title;
  final String body;
  final int commentCount;
  final String createdAt;
}

class CommunityComment {
  const CommunityComment({
    required this.id,
    required this.postId,
    required this.authorId,
    required this.displayName,
    required this.body,
    required this.createdAt,
  });

  factory CommunityComment.fromJson(dynamic value) {
    final json = jsonMap(value);
    return CommunityComment(
      id: textValue(json['id']),
      postId: textValue(json['post_id']),
      authorId: textValue(json['author_id']),
      displayName: textValue(json['display_name'], '匿名同學'),
      body: textValue(json['body']),
      createdAt: textValue(json['created_at']),
    );
  }

  final String id;
  final String postId;
  final String authorId;
  final String displayName;
  final String body;
  final String createdAt;
}

class CommunityThread {
  const CommunityThread({required this.post, required this.comments});

  factory CommunityThread.fromJson(dynamic value) {
    final json = jsonMap(value);
    return CommunityThread(
      post: CommunityPost.fromJson(json['post']),
      comments: jsonMapList(
        json['comments'],
      ).map(CommunityComment.fromJson).toList(),
    );
  }

  final CommunityPost post;
  final List<CommunityComment> comments;
}

class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.schoolName,
    required this.authorId,
    required this.displayName,
    required this.body,
    required this.createdAt,
  });

  factory ChatMessage.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ChatMessage(
      id: textValue(json['id']),
      schoolName: textValue(json['school_name']),
      authorId: textValue(json['author_id']),
      displayName: textValue(json['display_name'], '匿名同學'),
      body: textValue(json['body']),
      createdAt: textValue(json['created_at']),
    );
  }

  final String id;
  final String schoolName;
  final String authorId;
  final String displayName;
  final String body;
  final String createdAt;
}

class PrivateConversation {
  const PrivateConversation({
    required this.id,
    required this.schoolName,
    required this.senderId,
    required this.senderName,
    required this.recipientId,
    required this.recipientName,
    required this.status,
    required this.updatedAt,
  });

  factory PrivateConversation.fromJson(dynamic value) {
    final json = jsonMap(value);
    return PrivateConversation(
      id: textValue(json['id']),
      schoolName: textValue(json['school_name']),
      senderId: textValue(json['sender_id']),
      senderName: textValue(json['sender_name'], '匿名同學'),
      recipientId: textValue(json['recipient_id']),
      recipientName: textValue(json['recipient_name'], '匿名同學'),
      status: textValue(json['status'], 'pending'),
      updatedAt: textValue(json['updated_at']),
    );
  }

  final String id;
  final String schoolName;
  final String senderId;
  final String senderName;
  final String recipientId;
  final String recipientName;
  final String status;
  final String updatedAt;

  String otherName(String identityId) =>
      senderId == identityId ? recipientName : senderName;
}

class PrivateMessage {
  const PrivateMessage({
    required this.id,
    required this.conversationId,
    required this.authorId,
    required this.displayName,
    required this.body,
    required this.createdAt,
  });

  factory PrivateMessage.fromJson(dynamic value) {
    final json = jsonMap(value);
    return PrivateMessage(
      id: textValue(json['id']),
      conversationId: textValue(json['conversation_id']),
      authorId: textValue(json['author_id']),
      displayName: textValue(json['display_name'], '匿名同學'),
      body: textValue(json['body']),
      createdAt: textValue(json['created_at']),
    );
  }

  final String id;
  final String conversationId;
  final String authorId;
  final String displayName;
  final String body;
  final String createdAt;
}

enum ApplicationFieldKind {
  text,
  email,
  tel,
  date,
  number,
  textarea,
  select,
  checkbox,
  files,
}

ApplicationFieldKind applicationFieldKind(dynamic value) =>
    ApplicationFieldKind.values.firstWhere(
      (kind) => kind.name == value?.toString(),
      orElse: () => ApplicationFieldKind.text,
    );

class ApplicationFormField {
  const ApplicationFormField({
    required this.id,
    required this.label,
    required this.kind,
    required this.required,
    required this.options,
    required this.sensitive,
    required this.minFiles,
    required this.maxFiles,
    this.reusableProfileKey = '',
    this.placeholder = '',
    this.helpText = '',
    this.maxLength,
  });

  factory ApplicationFormField.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ApplicationFormField(
      id: textValue(json['id']),
      label: textValue(json['label']),
      kind: applicationFieldKind(json['field_type']),
      required: json['required'] == true,
      reusableProfileKey: textValue(json['reusable_profile_key']),
      placeholder: textValue(json['placeholder']),
      helpText: textValue(json['help_text']),
      options: stringList(json['options']),
      sensitive: json['sensitive'] == true,
      maxLength: json['max_length'] == null
          ? null
          : intValue(json['max_length']),
      minFiles: intValue(json['min_files']),
      maxFiles: intValue(json['max_files'], 6).clamp(1, 12),
    );
  }

  final String id;
  final String label;
  final ApplicationFieldKind kind;
  final bool required;
  final String reusableProfileKey;
  final String placeholder;
  final String helpText;
  final List<String> options;
  final bool sensitive;
  final int? maxLength;
  final int minFiles;
  final int maxFiles;
}

class ApplicationDocumentTemplate {
  const ApplicationDocumentTemplate({
    required this.id,
    required this.title,
    required this.shortTitle,
    required this.category,
    required this.stage,
    required this.description,
    required this.fields,
    required this.defaultCopies,
    required this.destinations,
    required this.signatures,
    required this.stamps,
    required this.programTypes,
    required this.conditionFlags,
    required this.officialLayout,
    required this.sourceUrl,
    required this.sourceCheckedAt,
    required this.version,
    this.conditionalNote = '',
    this.officialFormNumber = '',
    this.officialFileName = '',
  });

  factory ApplicationDocumentTemplate.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ApplicationDocumentTemplate(
      id: textValue(json['id']),
      title: textValue(json['title']),
      shortTitle: textValue(json['short_title']),
      category: textValue(json['category']),
      stage: textValue(json['stage']),
      description: textValue(json['description']),
      fields: jsonMapList(
        json['fields'],
      ).map(ApplicationFormField.fromJson).toList(),
      defaultCopies: intValue(json['default_copies'], 1).clamp(1, 10),
      destinations: stringList(json['destinations']),
      signatures: stringList(json['signatures']),
      stamps: stringList(json['stamps']),
      programTypes: stringList(json['program_types']),
      conditionFlags: stringList(json['condition_flags']),
      conditionalNote: textValue(json['conditional_note']),
      officialLayout: json['official_layout'] == true,
      officialFormNumber: textValue(json['official_form_number']),
      officialFileName: textValue(json['official_file_name']),
      sourceUrl: textValue(json['source_url']),
      sourceCheckedAt: textValue(json['source_checked_at']),
      version: textValue(json['version']),
    );
  }

  final String id;
  final String title;
  final String shortTitle;
  final String category;
  final String stage;
  final String description;
  final List<ApplicationFormField> fields;
  final int defaultCopies;
  final List<String> destinations;
  final List<String> signatures;
  final List<String> stamps;
  final List<String> programTypes;
  final List<String> conditionFlags;
  final String conditionalNote;
  final bool officialLayout;
  final String officialFormNumber;
  final String officialFileName;
  final String sourceUrl;
  final String sourceCheckedAt;
  final String version;
}

class ApplicationCenterContext {
  const ApplicationCenterContext({
    this.schoolName = '長庚大學',
    this.targetSchool = '',
    this.targetCountry = '',
    this.programType = 'exchange',
    this.academicYear = '',
    this.semester = '',
    this.flags = const [],
  });

  factory ApplicationCenterContext.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ApplicationCenterContext(
      schoolName: textValue(json['school_name'], '長庚大學'),
      targetSchool: textValue(json['target_school']),
      targetCountry: textValue(json['target_country']),
      programType: textValue(json['program_type'], 'exchange'),
      academicYear: textValue(json['academic_year']),
      semester: textValue(json['semester']),
      flags: stringList(json['flags']),
    );
  }

  final String schoolName;
  final String targetSchool;
  final String targetCountry;
  final String programType;
  final String academicYear;
  final String semester;
  final List<String> flags;

  ApplicationCenterContext copyWith({
    String? schoolName,
    String? targetSchool,
    String? targetCountry,
    String? programType,
    String? academicYear,
    String? semester,
    List<String>? flags,
  }) => ApplicationCenterContext(
    schoolName: schoolName ?? this.schoolName,
    targetSchool: targetSchool ?? this.targetSchool,
    targetCountry: targetCountry ?? this.targetCountry,
    programType: programType ?? this.programType,
    academicYear: academicYear ?? this.academicYear,
    semester: semester ?? this.semester,
    flags: flags ?? this.flags,
  );

  JsonMap toJson() => {
    'school_name': schoolName,
    'target_school': targetSchool.isEmpty ? null : targetSchool,
    'target_country': targetCountry.isEmpty ? null : targetCountry,
    'program_type': programType,
    'academic_year': academicYear.isEmpty ? null : academicYear,
    'semester': semester.isEmpty ? null : semester,
    'flags': flags,
  };
}

class ApplicationUpload {
  const ApplicationUpload({
    required this.name,
    required this.mimeType,
    required this.bytes,
  });

  final String name;
  final String mimeType;
  final Uint8List bytes;

  JsonMap toJson() => {
    'name': name,
    'type': mimeType,
    'data_url': 'data:$mimeType;base64,${base64Encode(bytes)}',
  };
}

enum ApplicationDocumentProgress {
  draft('draft', '待填寫'),
  readyToPrint('ready_to_print', '待列印'),
  pendingSignature('pending_signature', '待簽名'),
  pendingDepartmentStamp('pending_department_stamp', '待系所核章'),
  pendingSubmission('pending_submission', '待送件'),
  completed('completed', '已完成');

  const ApplicationDocumentProgress(this.apiValue, this.label);

  final String apiValue;
  final String label;

  static ApplicationDocumentProgress parse(dynamic value) =>
      ApplicationDocumentProgress.values.firstWhere(
        (status) => status.apiValue == value?.toString(),
        orElse: () => ApplicationDocumentProgress.draft,
      );
}

class ApplicationDocumentSelectionState {
  const ApplicationDocumentSelectionState({
    required this.selected,
    required this.copies,
    required this.status,
  });

  factory ApplicationDocumentSelectionState.initial(int copies) =>
      ApplicationDocumentSelectionState(
        selected: false,
        copies: copies.clamp(1, 10),
        status: ApplicationDocumentProgress.draft,
      );

  factory ApplicationDocumentSelectionState.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ApplicationDocumentSelectionState(
      selected: json['selected'] == true,
      copies: intValue(json['copies'], 1).clamp(1, 10),
      status: ApplicationDocumentProgress.parse(json['status']),
    );
  }

  final bool selected;
  final int copies;
  final ApplicationDocumentProgress status;

  ApplicationDocumentSelectionState copyWith({
    bool? selected,
    int? copies,
    ApplicationDocumentProgress? status,
  }) => ApplicationDocumentSelectionState(
    selected: selected ?? this.selected,
    copies: (copies ?? this.copies).clamp(1, 10),
    status: status ?? this.status,
  );

  JsonMap toJson() => {
    'selected': selected,
    'copies': copies,
    'status': status.apiValue,
  };
}

class ApplicationFormCompletion {
  const ApplicationFormCompletion({
    required this.completed,
    required this.total,
  });

  final int completed;
  final int total;

  bool get ready => completed == total;
  int get percent => total == 0 ? 100 : ((completed / total) * 100).round();
}
