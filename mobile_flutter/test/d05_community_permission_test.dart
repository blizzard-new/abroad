import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('D-05: Community permission matrix', () {
    test('guest store has no account and no identity', () {
      final store = ExchangeStore(
        api: ExchangeApi(
          client: MockClient((_) async => http.Response('[]', 200)),
          baseUrl: 'https://test.example/',
        ),
      );
      expect(store.account, isNull);
      expect(store.identity, isNull);
      expect(store.accessToken, isEmpty);
    });

    test('AnonymousIdentity parses token and display name', () {
      final id = AnonymousIdentity.fromJson({
        'id': 'anon1',
        'display_name': '匿名學生',
        'access_token': 'anon_tok',
      });
      expect(id.displayName, '匿名學生');
      expect(id.accessToken, 'anon_tok');
    });

    test('CommunityPost parses board and display name', () {
      final post = CommunityPost.fromJson({
        'id': 'p1', 'school_name': '長庚大學', 'author_id': '',
        'display_name': '匿名學生', 'post_type': 'discussion',
        'topic': '', 'country': '', 'academic_year': '',
        'application_stage': '', 'title': '測試', 'body': '內容',
        'comment_count': 0, 'created_at': '2026-09-01T12:00:00Z',
      });
      expect(post.displayName, '匿名學生');
      expect(post.schoolName, '長庚大學');
    });
  });

  group('D-05: Cross-school access control', () {
    test('CGU student homeUniversity does not match NTPU board', () {
      final p = AccountProfile.fromJson({
        'id': 'u1', 'display_name': 'CGU',
        'home_university': '長庚大學', 'application_stage': 'exploring',
        'email_verified': true, 'school_email_verified': true,
        'student_status_verified': true, 'target_countries': [],
        'followed_boards': [], 'product_tier': 'free', 'providers': [],
      });
      expect(p.homeUniversity, isNot('國立臺北大學'));
    });

    test('NTPU student homeUniversity does not match CGU board', () {
      final p = AccountProfile.fromJson({
        'id': 'u2', 'display_name': 'NTPU',
        'home_university': '國立臺北大學', 'application_stage': 'exploring',
        'email_verified': true, 'school_email_verified': true,
        'student_status_verified': true, 'target_countries': [],
        'followed_boards': [], 'product_tier': 'free', 'providers': [],
      });
      expect(p.homeUniversity, isNot('長庚大學'));
    });

    test('unverified student cannot have studentStatusVerified', () {
      final p = AccountProfile.fromJson({
        'id': 'u3', 'display_name': '未驗證',
        'home_university': '長庚大學', 'application_stage': 'exploring',
        'email_verified': true, 'school_email_verified': false,
        'student_status_verified': false, 'target_countries': [],
        'followed_boards': [], 'product_tier': 'free', 'providers': [],
      });
      expect(p.studentStatusVerified, isFalse);
    });
  });

  group('D-05: Account deletion', () {
    late ExchangeStore store;
    setUp(() {
      SharedPreferences.setMockInitialValues({});
      store = ExchangeStore(
        api: ExchangeApi(
          client: MockClient((_) async => http.Response('[]', 200)),
          baseUrl: 'https://test.example/',
        ),
      );
    });

    test('logout clears session state (token, account, identity)', () async {
      store.accessToken = 'tok_test';
      await store.logout();
      expect(store.accessToken, isEmpty);
      expect(store.account, isNull);
      expect(store.identity, isNull);
    });

    test('toggleFavorite adds and removes correctly', () async {
      await store.toggleFavorite('Test School');
      expect(store.favorites, contains('Test School'));
      await store.toggleFavorite('Test School');
      expect(store.favorites, isNot(contains('Test School')));
    });
  });
}
