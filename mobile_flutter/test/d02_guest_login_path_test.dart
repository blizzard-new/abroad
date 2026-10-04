import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

ExchangeStore _store() => ExchangeStore(
      api: ExchangeApi(
        client: MockClient((_) async => http.Response('[]', 200)),
        baseUrl: 'https://test.example/',
      ),
    );

void main() {
  group('D-02: Guest golden path', () {
    late ExchangeStore store;
    setUp(() {
      SharedPreferences.setMockInitialValues({});
      store = _store();
    });

    test('guest store starts with no account, no token', () {
      expect(store.account, isNull);
      expect(store.accessToken, isEmpty);
      expect(store.identity, isNull);
      expect(store.favorites, isEmpty);
    });

    test('guest store has default application context', () {
      expect(store.applicationTemplates, isEmpty);
      expect(store.applicationProfile, isEmpty);
    });
  });

  group('D-02: Multi-university dynamic profile', () {
    test('CGU profile reflects 長庚大學', () {
      final p = AccountProfile.fromJson({
        'id': 'u1', 'display_name': 'CGU學生',
        'home_university': '長庚大學', 'application_stage': 'exploring',
        'email_verified': true, 'school_email_verified': false,
        'student_status_verified': false, 'target_countries': [],
        'followed_boards': [], 'product_tier': 'free', 'providers': [],
      });
      expect(p.homeUniversity, '長庚大學');
    });

    test('NTPU profile reflects 國立臺北大學 with subscription', () {
      final p = AccountProfile.fromJson({
        'id': 'u2', 'display_name': 'NTPU學生',
        'home_university': '國立臺北大學', 'application_stage': 'applying',
        'email_verified': true, 'school_email_verified': true,
        'student_status_verified': true, 'target_countries': ['日本'],
        'followed_boards': ['公共留學板'], 'product_tier': 'subscription',
        'providers': [],
      });
      expect(p.homeUniversity, '國立臺北大學');
      expect(p.productTier, ProductAccessTier.subscription);
      expect(p.studentStatusVerified, isTrue);
    });
  });
}
