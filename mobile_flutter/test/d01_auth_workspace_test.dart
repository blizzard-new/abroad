import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('D-01: Auth token lifecycle', () {
    test('AccountSession parses token, expiry and profile', () {
      final session = AccountSession.fromJson({
        'access_token': 'tok_abc123',
        'expires_at': '2099-12-31T23:59:59Z',
        'profile': {
          'id': 'u1',
          'display_name': '測試帳號',
          'home_university': '長庚大學',
          'application_stage': 'exploring',
          'email_verified': true,
          'school_email_verified': false,
          'student_status_verified': false,
          'target_countries': ['日本'],
          'followed_boards': ['公共留學板'],
          'product_tier': 'free',
          'providers': [],
        },
      });
      expect(session.accessToken, 'tok_abc123');
      expect(session.expiresAt, '2099-12-31T23:59:59Z');
      expect(session.profile.displayName, '測試帳號');
      expect(session.profile.homeUniversity, '長庚大學');
      expect(session.profile.emailVerified, isTrue);
      expect(session.profile.productTier, ProductAccessTier.free);
    });

    test('expired expiresAt is detectable', () {
      final session = AccountSession.fromJson({
        'access_token': 'tok_old',
        'expires_at': '2020-01-01T00:00:00Z',
        'profile': {
          'id': 'u2', 'display_name': '過期',
          'home_university': '國立臺北大學',
          'application_stage': 'exploring',
          'email_verified': false, 'school_email_verified': false,
          'student_status_verified': false, 'target_countries': [],
          'followed_boards': [], 'product_tier': 'guest', 'providers': [],
        },
      });
      expect(
        DateTime.parse(session.expiresAt).isBefore(DateTime.now()),
        isTrue,
      );
    });

    test('API raises ExchangeApiException on 401', () async {
      final api = ExchangeApi(
        client: MockClient((_) async =>
            http.Response('{"detail":"Not authenticated"}', 401)),
        baseUrl: 'https://test.example/',
      );
      expect(
        () => api.profile('bad_token'),
        throwsA(isA<ExchangeApiException>()
            .having((e) => e.statusCode, 'statusCode', 401)),
      );
    });

    test('API raises ExchangeApiException on 403', () async {
      final api = ExchangeApi(
        client: MockClient((_) async =>
            http.Response('{"detail":"Forbidden"}', 403)),
        baseUrl: 'https://test.example/',
      );
      expect(
        () => api.profile('no_perm_token'),
        throwsA(isA<ExchangeApiException>()
            .having((e) => e.statusCode, 'statusCode', 403)),
      );
    });

    test('ProductAccessTier round-trips through name', () {
      for (final tier in ProductAccessTier.values) {
        final parsed = ProductAccessTier.values
            .where((t) => t.name == tier.name)
            .firstOrNull;
        expect(parsed, tier);
      }
    });
  });

  group('D-01: Workspace persistence round-trip', () {
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

    test('toggleFavorite persists to SharedPreferences', () async {
      await store.toggleFavorite('Lincoln University');
      expect(store.favorites, contains('Lincoln University'));

      final prefs = await SharedPreferences.getInstance();
      final key = prefs.getKeys().singleWhere((key) => key.startsWith('local_v2:') && key.endsWith(':favorite_schools'));
      final saved = prefs.getStringList(key);
      expect(saved, contains('Lincoln University'));
    });

    test('toggleFavorite twice removes the school', () async {
      await store.toggleFavorite('Fordham University');
      await store.toggleFavorite('Fordham University');
      expect(store.favorites, isNot(contains('Fordham University')));
    });

    test('logout clears accessToken and account', () async {
      store.accessToken = 'tok_session';
      await store.logout();
      expect(store.accessToken, isEmpty);
      expect(store.account, isNull);
      expect(store.identity, isNull);
    });
  });
}
