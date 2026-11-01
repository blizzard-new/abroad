// Isolated visual fixtures. No production account, dates or school requirements.
import 'dart:convert';
import 'dart:io';
import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/screens/root_shell.dart';
import 'package:exchange_guide_flutter/screens/application_document_form_screen.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('2.1.9 branded destinations and real progress actions', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues({});
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    server.listen((request) async {
      final bytes = await rootBundle.load('assets/schools/f3940610659ece.jpg');
      request.response.headers.contentType = ContentType('image', 'jpeg');
      request.response.add(bytes.buffer.asUint8List());
      await request.response.close();
    });
    addTearDown(() => server.close(force: true));
    final store =
        ExchangeStore(
            api: ExchangeApi(
              baseUrl: 'https://design-fixture.invalid/',
              client: MockClient((request) async {
                final Object body = request.url.path.endsWith('boards')
                    ? [
                        {
                          'id': 'public',
                          'label': '公共留學板',
                          'can_read': true,
                          'can_post': false,
                        },
                      ]
                    : request.url.path.endsWith('feed')
                    ? {
                        'items': [
                          {
                            'id': 'fixture-post',
                            'board_id': 'public',
                            'title': '第一次準備交換，你最想先知道什麼？',
                            'body': '從選校、整理文件到行前準備，分享你的問題和正在探索的方向。',
                            'display_name': '版面測試同學',
                            'topic': 'application',
                            'comment_count': 2,
                          },
                        ],
                      }
                    : [];
                return http.Response.bytes(
                  utf8.encode(jsonEncode(body)),
                  200,
                  headers: {'content-type': 'application/json'},
                );
              }),
            ),
          )
          ..dashboard = StudentDashboard.fromJson({
            'school_name': '長庚大學',
            'partner_universities': [
              {
                'school_name': '林肯大學 Lincoln University',
                'country': '紐西蘭',
                'image_status': 'verified',
                'image_url':
                    'http://127.0.0.1:${server.port}/f3940610659ece.jpg',
              },
            ],
          })
          ..authProviders = [
            const AuthProviderStatus(
              provider: 'google',
              enabled: true,
              label: 'Google',
            ),
          ]
          ..applicationTemplates = [
            for (final row in [
              ('profile', '個人資料'),
              ('study', '讀書計畫'),
              ('courses', '修課規劃'),
            ])
              ApplicationDocumentTemplate.fromJson({
                'id': row.$1,
                'title': row.$2,
                'short_title': row.$2,
                'stage': '測試文件',
                'description': '此為操作測試資料，並非校方要求。',
                'fields': [
                  {
                    'id': 'text',
                    'label': '準備內容',
                    'required': true,
                    'field_type': 'textarea',
                  },
                ],
              }),
          ];
    store.applicationAnswers['profile'] = {'text': '版面測試內容'};
    addTearDown(store.dispose);
    await tester.pumpWidget(
      ExchangeStoreScope(
        store: store,
        child: MaterialApp(
          theme: buildExchangeTheme(),
          debugShowCheckedModeBanner: false,
          home: const RootShell(),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await binding.convertFlutterSurfaceToImage();
    final folder = await getApplicationDocumentsDirectory();
    Future<void> capture(String name) async {
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull, reason: name);
      await File(
        '${folder.path}/$name.png',
      ).writeAsBytes(await binding.takeScreenshot(name));
    }

    await capture('219-home');
    await tester.drag(find.byType(ListView).first, const Offset(0, -450));
    await capture('219-journey');
    await tester.tap(find.byTooltip('學校'));
    await capture('219-schools');
    await tester.tap(find.byKey(const ValueKey('open-school-filters')));
    await capture('219-filters');
    await tester.tap(find.widgetWithText(FilledButton, '顯示 1 間學校'));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('加入收藏'));
    expect(store.favorites, contains('林肯大學 Lincoln University'));
    await tester.tap(find.byTooltip('申請'));
    await tester.pumpAndSettle();
    expect(find.text('33%'), findsOneWidget);
    await capture('219-application');
    await tester.ensureVisible(find.widgetWithText(FilledButton, '繼續準備'));
    await tester.tap(find.widgetWithText(FilledButton, '繼續準備'));
    await tester.pumpAndSettle();
    expect(find.byType(ApplicationDocumentFormScreen), findsOneWidget);
    expect(find.text('讀書計畫'), findsWidgets);
    await capture('219-document');
    await tester.tap(find.byTooltip('文件清單'));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('論壇'));
    await capture('219-forum');
    await tester.tap(find.byTooltip('我的'));
    await capture('219-account');
    await tester.pumpWidget(const SizedBox());
  });
}
