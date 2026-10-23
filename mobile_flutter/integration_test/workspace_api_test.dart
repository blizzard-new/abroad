import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:exchange_guide_flutter/core/account_session_storage.dart';
import 'package:exchange_guide_flutter/core/mobile_login.dart';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets(
    'PKCE handoff and Web/mobile REST workspace preserve the same account',
    (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: Text('Local API acceptance test')),
        ),
      );
      const base = 'http://127.0.0.1:18765/';
      final api = ExchangeApi(baseUrl: base);
      const verifier =
          'vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv';
      const state = 'sssssssssssssssssssssssssssssssssssssssssss';
      await const FlutterSecureStorage().write(
        key: 'mobile_login:${Uri.encodeComponent(base)}',
        value: jsonEncode({
          'verifier': verifier,
          'state': state,
          'expires_at': DateTime.now()
              .add(const Duration(minutes: 5))
              .toIso8601String(),
        }),
      );
      final response = await http.post(
        Uri.parse('${base}__fixture__/handoff'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'challenge': base64Url
              .encode(sha256.convert(ascii.encode(verifier)).bytes)
              .replaceAll('=', ''),
          'state': state,
        }),
      );
      expect(response.statusCode, 200);
      final login = await MobileLogin(
        api,
      ).complete(Uri.parse(jsonDecode(response.body)['url'] as String));
      expect(login, isNotNull);
      await AccountSessionStorage(base).save(login!.accessToken, login.profile);
      final store = ExchangeStore(api: api);
      await store.initialize();
      expect(store.account?.id, login.profile.id);
      expect(store.workspaceSync, isNotNull);
      if (!store.favorites.contains('Integration fixture university')) {
        await store.toggleFavorite('Integration fixture university');
      }
      await store.synchronizeWorkspace();
      final web = ExchangeApi(baseUrl: base);
      final workspace = await web.workspace(
        login.accessToken,
        store.selectedUniversity,
      );
      expect(
        workspace['favorite_schools'],
        contains('Integration fixture university'),
      );
      workspace['budget_plans'] = {
        'Integration fixture university': {
          'currency': 'JPY',
          'months': 5,
          'housing': 100,
          'food': 200,
          'transport': 30,
          'other': 40,
          'one_time': 500,
          'scholarship': 10,
          'saved_at': DateTime.now().toUtc().toIso8601String(),
        },
      };
      workspace['document_readiness'] = {'語言能力證明': 'ready'};
      await web.saveWorkspace(login.accessToken, workspace);
      await store.synchronizeWorkspace();
      expect(
        store.budgetPlans['Integration fixture university']?.currency,
        'JPY',
      );
      expect(store.documentReadyCount, 1);
      await store.toggleFavorite('Second fixture university');
      await store.synchronizeWorkspace();
      final updated = await web.workspace(
        login.accessToken,
        store.selectedUniversity,
      );
      expect(
        updated['budget_plans']['Integration fixture university']['currency'],
        'JPY',
      );
      expect(updated['document_readiness']['語言能力證明'], 'ready');
      await store.logout();
      expect(store.account, isNull);
      expect(store.favorites, isEmpty);
      expect(await AccountSessionStorage(base).read(), isNull);
      store.dispose();
    },
  );
}
