import 'package:exchange_guide_flutter/data/models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('partner university parses API fields', () {
    final school = PartnerUniversity.fromJson({
      'school_name': 'Lincoln University',
      'country': 'New Zealand',
      'program_type': '交換學生',
      'colleges': '四院皆可',
      'degree_levels': '大學部、研究所',
      'quota': '2',
      'application_deadline': '30 September',
      'image_url': 'https://example.com/campus.jpg',
      'image_page_url': 'https://example.com/campus',
      'image_source_url': 'https://example.com/campus.jpg',
      'image_status': 'verified',
    });

    expect(school.schoolName, 'Lincoln University');
    expect(school.country, 'New Zealand');
    expect(school.mobileListSummary, '交換學生 · 四院皆可 · 大學部、研究所');
    expect(school.quota, '2');
    expect(school.imageUrl, 'https://example.com/campus.jpg');
    expect(school.imagePageUrl, 'https://example.com/campus');
    expect(school.imageStatus, 'verified');
    expect(school.searchableText, contains('new zealand'));
  });

  test('life highlights put concrete summaries first', () {
    final digest = ExperienceDigest.fromJson({
      'highlights': [
        {
          'title': '課業與教學',
          'source_count': 9,
          'key_points': <String>[],
          'source_urls': <String>['https://example.com/source'],
        },
        {
          'title': '每月生活預算',
          'source_count': 3,
          'key_points': <String>['房租與飲食要分開估算'],
          'source_urls': <String>['https://example.com/budget'],
        },
      ],
    });

    expect(digest.highlights.first.title, '每月生活預算');
    expect(digest.highlights.first.hasConcreteSummary, isTrue);
  });

  test('account session parses profile preferences', () {
    final session = AccountSession.fromJson({
      'access_token': 'account-token',
      'expires_at': '2026-08-01T00:00:00Z',
      'profile': {
        'id': 'account-1',
        'email': 'student@example.edu.tw',
        'display_name': '想去日本的小林',
        'home_university': '長庚大學',
        'target_countries': ['日本', '德國'],
        'application_stage': 'documents',
        'school_email_verified': true,
        'providers': ['email'],
        'followed_boards': ['長庚大學'],
      },
    });

    expect(session.accessToken, 'account-token');
    expect(session.profile.targetCountries, ['日本', '德國']);
    expect(session.profile.applicationStage, 'documents');
    expect(session.profile.schoolEmailVerified, isTrue);
    expect(session.profile.followedBoards, ['長庚大學']);
  });

  test('community post keeps structured discovery fields', () {
    final post = CommunityPost.fromJson({
      'id': 'post-1',
      'school_name': '東京大學',
      'author_id': 'student-1',
      'display_name': '交換準備中',
      'post_type': 'question',
      'topic': 'housing',
      'country': '日本',
      'academic_year': '2027 秋季',
      'application_stage': 'documents',
      'title': '宿舍申請時間',
      'body': '想請問宿舍通常要在哪個階段申請？',
      'comment_count': 2,
      'created_at': '2026-07-17T10:00:00Z',
    });

    expect(post.topic, 'housing');
    expect(post.country, '日本');
    expect(post.academicYear, '2027 秋季');
    expect(post.applicationStage, 'documents');
  });

  test('school without verified image remains neutral', () {
    final school = PartnerUniversity.fromJson({
      'school_name': 'Lincoln University',
      'country': '紐西蘭',
      'program_type': '交換學生',
      'source_url': 'https://example.com/source',
    });

    expect(school.imageUrl, isEmpty);
    expect(school.imageStatus, 'missing');
  });

  test('dashboard applies the verified official image manifest', () {
    final dashboard = StudentDashboard.fromJson({
      'school_name': '長庚大學',
      'partner_universities': [
        {
          'school_name': 'Lincoln University',
          'country': '紐西蘭',
          'program_type': '交換學生',
          'source_url': 'https://example.com/source',
        },
      ],
    });
    final visual = SchoolVisual.fromJson({
      'school_name': 'Lincoln University',
      'official_page_url': 'https://example.com/campus',
      'image_source_url': 'https://example.com/campus.jpg',
      'local_path': '/static/assets/schools/lincoln.jpg',
      'status': 'verified',
    });

    final enriched = dashboard.withSchoolVisuals({
      'Lincoln University': visual,
    }, (path) => 'http://app.test$path');

    expect(enriched.partnerUniversities.single.imageStatus, 'verified');
    expect(
      enriched.partnerUniversities.single.imageUrl,
      'http://app.test/static/assets/schools/lincoln.jpg',
    );
  });

  test('partner university prefers the student-facing Chinese summary', () {
    final school = PartnerUniversity.fromJson({
      'school_name': 'Lincoln University',
      'country': '紐西蘭',
      'application_deadline': 'Semester 1: 30 September',
      'eligibility': 'Option A Entry Requirements: IELTS 6.0 overall',
      'student_summary_zh': {
        'study_period': '1 學期',
        'application_deadline': '第一學期：前一年 9 月 30 日',
        'eligibility_points': ['方案 A：IELTS 總分 6.0。'],
        'application_steps': ['由長庚大學提名。'],
        'tuition_points': ['免繳合作校學雜費。'],
        'translated_from_english': true,
      },
    });

    expect(school.displayApplicationDeadline, '第一學期：前一年 9 月 30 日');
    expect(school.displayStudyPeriod, '1 學期');
    expect(school.eligibilityPoints, ['方案 A：IELTS 總分 6.0。']);
    expect(school.applicationSteps, ['由長庚大學提名。']);
    expect(school.studentSummaryZh.translatedFromEnglish, isTrue);
  });

  test('account session parses profile product tier and providers', () {
    final profile = AccountProfile.fromJson({
      'id': 'account-2',
      'email': 'pro@example.edu.tw',
      'display_name': 'Pro User',
      'home_university': '台大',
      'target_countries': ['US'],
      'application_stage': 'documents',
      'school_email_verified': true,
      'providers': ['email', 'google'],
      'followed_boards': [],
      'product_tier': 'subscription',
      'email_verified': true,
    });

    expect(profile.productTier, ProductAccessTier.subscription);
    expect(profile.providers, ['email', 'google']);
    expect(profile.emailVerified, isTrue);
  });

  test('supported university registry includes all 22 official schools', () {
    expect(defaultSupportedUniversities, hasLength(22));
    expect(defaultSupportedUniversities.first.schoolName, '長庚大學');
    expect(resolveSupportedUniversity('ntu').schoolName, '國立臺灣大學');
    expect(resolveSupportedUniversity('台大').shortName, '臺大');
    expect(resolveSupportedUniversity('cycu').schoolName, '中原大學');
    expect(resolveSupportedUniversity('fcu').schoolName, '逢甲大學');
    expect(resolveSupportedUniversity('nycu').schoolName, '國立陽明交通大學');
    expect(resolveSupportedUniversity('nthu').schoolName, '國立清華大學');
    expect(resolveSupportedUniversity('pccu').schoolName, '中國文化大學');
    expect(resolveSupportedUniversity('wzu').schoolName, '文藻外語大學');
    expect(resolveSupportedUniversity('長庚').boardTabLabel, '長庚板');
    expect(resolveSupportedUniversity('政大').boardTabLabel, '政大板');
    expect(tryResolveSupportedUniversity('未知大學'), isNull);
  });
}
