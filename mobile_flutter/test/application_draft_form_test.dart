import 'dart:convert';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/screens/application_document_form_screen.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  testWidgets(
    'loads Web draft, saves incomplete fields, and blocks an account change',
    (tester) async {
      SharedPreferences.setMockInitialValues({});
      FlutterSecureStorage.setMockInitialValues({});
      final template = ApplicationDocumentTemplate.fromJson({
        'id': 'study-plan',
        'version': 'v1',
        'title': '讀書計畫',
        'fields': [
          {
            'id': 'reason',
            'label': '交換目標',
            'field_type': 'text',
            'required': true,
          },
          {
            'id': 'other',
            'label': '尚未填寫',
            'field_type': 'text',
            'required': true,
          },
        ],
      });
      JsonMap remote = {
        'home_school': '長庚大學',
        'template_id': 'study-plan',
        'template_version': 'v1',
        'revision': 1,
        'profile': {},
        'answers': {'reason': '電腦上的交換目標'},
        'attachments': {},
      };
      final api = ExchangeApi(
        baseUrl: 'https://form-ui.test/',
        client: MockClient((request) async {
          if (request.method == 'PUT') {
            remote = {
              ...jsonMap(jsonDecode(request.body)),
              'template_id': 'study-plan',
              'revision': 2,
            };
            return http.Response.bytes(utf8.encode(jsonEncode(remote)), 200);
          }
          return http.Response.bytes(
            utf8.encode(
              jsonEncode({
                'items': [remote],
              }),
            ),
            200,
          );
        }),
      );
      final store = ExchangeStore(api: api)
        ..account = AccountProfile.fromJson({
          'id': 'student',
          'display_name': '學生',
        })
        ..accessToken = 'token'
        ..applicationTemplates = [template];
      await tester.pumpWidget(
        ExchangeStoreScope(
          store: store,
          child: MaterialApp(
            home: ApplicationDocumentFormScreen(template: template),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('電腦上的交換目標'), findsOneWidget);
      await tester.enterText(find.byType(TextFormField).first, '手機接續的交換目標');
      await tester.ensureVisible(find.text('儲存草稿'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('儲存草稿'));
      await tester.pumpAndSettle();
      expect(remote['answers']['reason'], '手機接續的交換目標');
      expect(remote['answers']['other'], '');
      expect(
        store.applicationSelections[template.id]?.status,
        ApplicationDocumentProgress.draft,
      );
      expect(find.text('一般欄位已加密同步，電腦可接續填寫。'), findsOneWidget);
      store.account = AccountProfile.fromJson({'id': 'different'});
      store.selectMainTab(0);
      await tester.pumpAndSettle();
      expect(find.byType(TextFormField), findsNothing);
      expect(find.text('帳號或學校已變更，請返回文件清單重新開啟。'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
      store.dispose();
    },
  );
}
