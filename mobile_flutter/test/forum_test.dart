import 'dart:async';
import 'dart:convert';
import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/forum_models.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/screens/forum_screen.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

final board = {
  'id': 'public-study-abroad',
  'label': '公共留學板',
  'can_read': true,
  'can_post': true,
  'can_comment': true,
};
Map<String, dynamic> post(String id, String title) => {
  'id': id,
  'title': title,
  'body': '這是一篇申請與住宿經驗分享。',
  'board_id': 'public-study-abroad',
  'display_name': '匿名同學',
  'topic': 'application',
  'comment_count': 1,
};
http.Response response(Object data) => http.Response(
  jsonEncode(data),
  200,
  headers: {'content-type': 'application/json; charset=utf-8'},
);
ExchangeStore makeStore(
  Future<http.Response> Function(http.Request) handle, {
  bool loggedIn = true,
}) {
  final store = ExchangeStore(
    api: ExchangeApi(
      client: MockClient(handle),
      baseUrl: 'https://test.example/',
    ),
  );
  if (loggedIn) {
    store.account = AccountProfile.fromJson({
      'id': 'u1',
      'email_verified': true,
    });
    store.accessToken = 'account-token';
    store.identity = AnonymousIdentity.fromJson({
      'id': 'a1',
      'access_token': 'anon-token',
      'display_name': '匿名同學',
    });
  }
  return store;
}

Widget app(ExchangeStore store, Widget child) => ExchangeStoreScope(
  store: store,
  child: MaterialApp(
    theme: buildExchangeTheme(),
    home: Scaffold(body: child),
  ),
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => SharedPreferences.setMockInitialValues({}));
  testWidgets('guest browsing is public and login action uses account tab', (
    tester,
  ) async {
    final store = makeStore((request) async {
      expect(request.headers['authorization'], isNull);
      return response(
        request.url.path.endsWith('boards')
            ? [
                {...board, 'can_post': false, 'can_comment': false},
              ]
            : {
                'items': [post('p1', '公共討論')],
                'next_cursor': null,
              },
      );
    }, loggedIn: false);
    addTearDown(store.dispose);
    await tester.pumpWidget(app(store, const ForumScreen()));
    await tester.pumpAndSettle();
    expect(find.text('公共討論'), findsOneWidget);
    expect(find.text('申請'), findsOneWidget);
    expect(find.text('1 則回覆'), findsOneWidget);
    expect(find.text('查看討論 ›'), findsOneWidget);
    expect(
      tester
          .widget<FilledButton>(find.widgetWithText(FilledButton, '發起討論'))
          .onPressed,
      isNull,
    );
    await tester.tap(find.text('登入交流'));
    expect(store.navigationTab, 4);
  });
  testWidgets('search ignores older responses and feed loads next cursor', (
    tester,
  ) async {
    final old = Completer<http.Response>();
    var calls = 0;
    final store = makeStore((request) async {
      if (request.url.path.endsWith('boards')) return response([board]);
      expect(request.headers['authorization'], 'Bearer account-token');
      calls++;
      if (calls == 1) return old.future;
      expect(request.url.queryParameters['q'], '住宿');
      return response({
        'items': [
          post(calls == 2 ? 'p2' : 'p3', calls == 2 ? '新的搜尋結果' : '第二頁'),
        ],
        'next_cursor': calls == 2 ? 'cursor2' : null,
      });
    });
    addTearDown(store.dispose);
    await tester.pumpWidget(app(store, const ForumScreen()));
    await tester.pump();
    await tester.enterText(find.byType(TextField), '住宿');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();
    old.complete(
      response({
        'items': [post('p1', '過期結果')],
      }),
    );
    await tester.pumpAndSettle();
    expect(find.text('新的搜尋結果'), findsOneWidget);
    expect(find.text('過期結果'), findsNothing);
    await tester.ensureVisible(find.text('載入更多討論'));
    await tester.tap(find.text('載入更多討論'));
    await tester.pumpAndSettle();
    expect(find.text('第二頁'), findsOneWidget);
  });
  testWidgets(
    'native composer sends both credentials and retains draft on failure',
    (tester) async {
      Map<String, dynamic>? sent;
      final store = makeStore((request) async {
        expect(request.headers['authorization'], 'Bearer account-token');
        expect(request.headers['x-anonymous-id'], 'a1');
        expect(request.headers['x-anonymous-token'], 'anon-token');
        sent = jsonDecode(request.body) as Map<String, dynamic>;
        return http.Response('{"detail":"Please retry"}', 503);
      });
      addTearDown(store.dispose);
      await tester.pumpWidget(
        app(
          store,
          ForumComposer(store: store, boards: [ForumBoard.fromJson(board)]),
        ),
      );
      await tester.enterText(find.widgetWithText(TextField, '標題'), '住宿申請心得');
      await tester.enterText(
        find.widgetWithText(TextField, '討論內容'),
        '這裡分享準備交換住宿申請的經驗。',
      );
      await tester.ensureVisible(find.text('送出'));
      await tester.tap(find.text('送出'));
      await tester.pumpAndSettle();
      expect(sent?['board_id'], 'public-study-abroad');
      expect(sent?['identity_mode'], 'anonymous');
      expect(find.text('Please retry'), findsOneWidget);
      expect(find.text('住宿申請心得'), findsOneWidget);
    },
  );
  testWidgets('detail renders threaded replies and clears after logout', (
    tester,
  ) async {
    final store = makeStore((request) async {
      if (request.url.path.endsWith('comments')) {
        return response({
          'items': request.url.queryParameters['parent_id'] == 'c1'
              ? [
                  {'id': 'c2', 'body': '樓中樓內容'},
                ]
              : [
                  {'id': 'c1', 'body': '第一則回覆', 'reply_count': 1},
                ],
        });
      }
      return response(post('p1', '校板內容'));
    });
    addTearDown(store.dispose);
    await tester.pumpWidget(
      app(
        store,
        ForumPostScreen(
          store: store,
          postId: 'p1',
          board: ForumBoard.fromJson(board),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('查看 1 則回覆'));
    await tester.tap(find.text('查看 1 則回覆'));
    await tester.pumpAndSettle();
    expect(find.text('樓中樓內容'), findsOneWidget);
    store.account = null;
    store.accessToken = '';
    store.selectMainTab(0);
    await tester.pumpAndSettle();
    expect(find.text('校板內容'), findsNothing);
    expect(find.textContaining('登入狀態已改變'), findsOneWidget);
  });
  test(
    'identity response arriving after logout cannot repopulate identity',
    () async {
      final gate = Completer<http.Response>();
      final store = makeStore((_) => gate.future)..identity = null;
      addTearDown(store.dispose);
      final pending = store.ensureIdentity();
      store.account = null;
      store.accessToken = '';
      gate.complete(response({'id': 'old', 'access_token': 'old-anon'}));
      await expectLater(pending, throwsA(isA<ExchangeApiException>()));
      expect(store.identity, isNull);
    },
  );
  test(
    'reply write includes parent and delete encodes both resource IDs',
    () async {
      final requests = <http.Request>[];
      final store = makeStore((request) async {
        requests.add(request);
        return response({});
      });
      addTearDown(store.dispose);
      await store.api.writeForum(
        store.accessToken,
        store.identity!,
        body: '同學你好',
        postId: 'p1',
        parentId: 'c1',
      );
      expect(jsonDecode(requests.first.body)['parent_id'], 'c1');
      await store.api.deleteForum(
        store.accessToken,
        store.identity!,
        'p1',
        commentId: 'c1',
      );
      expect(requests.last.method, 'DELETE');
      expect(requests.last.url.path, '/community/posts/p1/comments/c1');
    },
  );
}
