import 'dart:convert';
import 'dart:typed_data';

import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('D-03: PDF generation API', () {
    test('applicationPacketPdf returns PDF bytes on 200', () async {
      final pdf = Uint8List.fromList([0x25, 0x50, 0x44, 0x46]);
      final api = ExchangeApi(
        client: MockClient((req) async {
          // applicationPacketPdf uses _client.post, so MockClient receives it
          return http.Response.bytes(pdf, 200);
        }),
        baseUrl: 'https://test.example/',
      );
      final result = await api.applicationPacketPdf({
        'template_id': 'study-plan',
        'answers': {'student_name_zh': '王小明'},
      });
      expect(result.length, 4);
      expect(result[0], 0x25); // %PDF magic byte
    });

    test('PDF generation 500 throws ExchangeApiException', () async {
      final api = ExchangeApi(
        client: MockClient((_) async => http.Response('error', 500)),
        baseUrl: 'https://test.example/',
      );
      expect(
        () => api.applicationPacketPdf({'template_id': 'bad'}),
        throwsA(isA<ExchangeApiException>()),
      );
    });
  });

  group('D-03: Sensitive data exclusion', () {
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

    test('profile memory excludes ID, passport and birthdate', () async {
      await store.setApplicationProfileMemoryEnabled(true);
      await store.saveApplicationProfile({
        'student_name_zh': '張三',
        'email': 'zhang@example.com',
        'id_number': 'A123456789',
        'passport_number': '300000001',
        'birth_date': '2004-06-15',
      });

      final prefs = await SharedPreferences.getInstance();
      final memoryKey = prefs.getKeys().singleWhere((key) => key.endsWith(':application_profile_memory_v1'));
      final raw = prefs.getString(memoryKey);
      expect(raw, isNotNull);
      final saved = jsonDecode(raw!) as Map<String, dynamic>;
      expect(saved.containsKey('student_name_zh'), isTrue);
      expect(saved.containsKey('id_number'), isFalse,
          reason: 'National ID must not persist');
      expect(saved.containsKey('passport_number'), isFalse,
          reason: 'Passport must not persist');
      expect(saved.containsKey('birth_date'), isFalse,
          reason: 'Birth date must not persist');
    });

    test('clear memory disables profile persistence', () async {
      await store.setApplicationProfileMemoryEnabled(true);
      await store.saveApplicationProfile({'email': 'x@y.com'});
      await store.clearApplicationProfileMemory();
      expect(store.applicationProfileMemoryEnabled, isFalse);
    });
  });

  group('D-03: Document progress states', () {
    test('all 6 ApplicationDocumentProgress values exist', () {
      expect(ApplicationDocumentProgress.values.length, 6);
      expect(ApplicationDocumentProgress.draft.name, 'draft');
      expect(ApplicationDocumentProgress.completed.name, 'completed');
    });

    test('ApplicationFormCompletion percent calculation', () {
      final c = ApplicationFormCompletion(completed: 7, total: 10);
      expect(c.percent, 70);
      expect(c.ready, isFalse);

      final full = ApplicationFormCompletion(completed: 10, total: 10);
      expect(full.ready, isTrue);
      expect(full.percent, 100);
    });
  });

  group('D-03: AI consent added to API', () {
    test('rewriteDocument sends ai_consent_granted in JSON', () async {
      final api = ExchangeApi(
        client: MockClient((req) async {
          final body = jsonDecode(req.body) as Map<String, dynamic>;
          expect(body['ai_consent_granted'], isTrue);
          return http.Response(
            jsonEncode({'rewritten_text': 'polished', 'changes': []}), 200,
          );
        }),
        baseUrl: 'https://test.example/',
      );
      await api.rewriteDocument(
        text: 'original', action: 'polish',
        documentType: 'study_plan', aiConsentGranted: true,
      );
    });
  });
}
