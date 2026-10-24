import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/state/application_draft_sync.dart';
import 'package:exchange_guide_flutter/state/workspace_sync.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

final template = ApplicationDocumentTemplate.fromJson({
  'id': 'study-plan',
  'version': 'v1',
  'title': '讀書計畫',
  'fields': [
    {
      'id': 'name',
      'reusable_profile_key': 'student_name_zh',
      'field_type': 'text',
    },
    {'id': 'motivation', 'field_type': 'textarea'},
    {'id': 'confirm', 'field_type': 'checkbox'},
    {'id': 'passport', 'field_type': 'text', 'sensitive': true},
    {
      'id': 'guardian',
      'reusable_profile_key': 'guardian_id_number',
      'sensitive': true,
    },
    {'id': 'files', 'field_type': 'files'},
  ],
});

class DraftServer {
  JsonMap remote = {
    'home_school': '測試母校',
    'template_id': 'study-plan',
    'template_version': 'v1',
    'revision': 1,
    'profile': {'student_name_zh': '原姓名'},
    'answers': {'motivation': '原計畫', 'web_only': '保留'},
    'attachments': {
      'files': [
        {'version_id': 'private-version', 'file_name': 'proof.pdf'},
      ],
    },
  };
  bool offline = false;
  int puts = 0;
  int raceWrites = 0;
  Completer<void>? hold;
  Completer<void>? entered;
  late final api = ExchangeApi(
    baseUrl: 'https://draft.test/',
    client: MockClient((req) async {
      expect(req.headers['Authorization'], 'Bearer token');
      if (offline) throw http.ClientException('offline');
      if (req.method == 'GET') {
        expect(req.url.queryParameters['home_school'], '測試母校');
        return response({
          'items': [remote],
        });
      }
      puts++;
      final sent = jsonMap(jsonDecode(req.body));
      expect(sent.keys.toSet(), {
        'home_school',
        'template_version',
        'revision',
        'profile',
        'answers',
        'attachments',
      });
      if (raceWrites > 0) {
        raceWrites--;
        remote['revision'] = (remote['revision'] as int) + 1;
        jsonMap(remote['answers']);
        remote['answers']['web_race'] = 'new';
        return response({
          'detail': {'current_draft': remote},
        }, status: 409);
      }
      expect(sent['revision'], remote['revision']);
      entered?.complete();
      if (hold != null) await hold!.future;
      remote = {
        ...sent,
        'template_id': 'study-plan',
        'revision': (remote['revision'] as int) + 1,
      };
      return response(remote);
    }),
  );
  http.Response response(Object body, {int status = 200}) =>
      http.Response.bytes(utf8.encode(jsonEncode(body)), status);
  ApplicationDraftSync make({
    String account = 'student',
    ExchangeApi? otherApi,
    String school = '測試母校',
  }) => ApplicationDraftSync(
    api: otherApi ?? api,
    accountId: account,
    accessToken: 'token',
    homeSchool: school,
    template: template,
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  test(
    'Web draft hydrates and only non-sensitive scalar edits leave the device',
    () async {
      final server = DraftServer();
      final sync = server.make();
      await sync.restore();
      await sync.sync();
      expect(sync.draft['answers']['motivation'], '原計畫');
      await sync.editFields({
        'name': '手機姓名',
        'motivation': '',
        'confirm': false,
        'passport': 'PRIVATE',
        'guardian': 'PRIVATE',
        'unknown': 'PRIVATE',
        'files': [
          ApplicationUpload(
            name: 'test.pdf',
            mimeType: 'application/pdf',
            bytes: Uint8List.fromList([1]),
          ),
        ],
      });
      await sync.sync();
      expect(sync.status, WorkspaceSyncStatus.saved);
      expect(server.remote['profile'], {'student_name_zh': '手機姓名'});
      expect(server.remote['answers'], {
        'motivation': '',
        'web_only': '保留',
        'confirm': false,
      });
      expect(
        server.remote['attachments']['files'][0]['version_id'],
        'private-version',
      );
      expect(
        (await const FlutterSecureStorage().readAll()).values.join(),
        isNot(contains('PRIVATE')),
      );
      sync.dispose();
    },
  );

  test(
    'offline draft survives restart and merges independent Web changes',
    () async {
      final server = DraftServer();
      final first = server.make();
      await first.restore();
      await first.sync();
      server.offline = true;
      await first.editFields({'motivation': '離線計畫'});
      await first.sync();
      expect(first.status, WorkspaceSyncStatus.pending);
      first.dispose();
      server.remote['profile']['student_name_zh'] = '電腦姓名';
      server.remote['revision'] = 2;
      final second = server.make();
      await second.restore();
      expect(second.draft['answers']['motivation'], '離線計畫');
      server.offline = false;
      await second.sync();
      expect(second.status, WorkspaceSyncStatus.saved);
      expect(server.remote['profile']['student_name_zh'], '電腦姓名');
      expect(server.remote['answers']['motivation'], '離線計畫');
      second.dispose();
    },
  );

  for (final preferLocal in [true, false]) {
    test(
      'same-field conflict requires a choice ($preferLocal), preserving unrelated edits',
      () async {
        final server = DraftServer();
        final sync = server.make();
        await sync.restore();
        await sync.sync();
        await sync.editFields({'motivation': '手機計畫'});
        server.remote['answers']['motivation'] = '電腦計畫';
        server.remote['answers']['web_only'] = '電腦其他欄位';
        server.remote['revision'] = 2;
        await sync.sync();
        expect(sync.status, WorkspaceSyncStatus.conflict);
        expect(server.puts, 0);
        await sync.resolveConflict(preferLocal: preferLocal);
        expect(sync.status, WorkspaceSyncStatus.saved);
        expect(
          server.remote['answers']['motivation'],
          preferLocal ? '手機計畫' : '電腦計畫',
        );
        expect(server.remote['answers']['web_only'], '電腦其他欄位');
        sync.dispose();
      },
    );
  }

  test(
    '409 between GET and PUT retries without overwriting Web changes',
    () async {
      final server = DraftServer();
      final sync = server.make();
      await sync.restore();
      await sync.sync();
      await sync.editFields({'motivation': '手機計畫'});
      server.raceWrites = 1;
      await sync.sync();
      expect(server.puts, 2);
      expect(sync.status, WorkspaceSyncStatus.saved);
      expect(server.remote['answers']['web_race'], 'new');
      sync.dispose();
    },
  );

  test(
    'edits during a PUT are retained and sent in the next revision',
    () async {
      final server = DraftServer();
      final sync = server.make();
      await sync.restore();
      await sync.sync();
      await sync.editFields({'motivation': '第一次'});
      server.hold = Completer();
      server.entered = Completer();
      final sending = sync.sync();
      await server.entered!.future;
      await sync.editFields({'motivation': '第二次'});
      server.entered = null;
      server.hold!.complete();
      await sending;
      expect(server.remote['answers']['motivation'], '第二次');
      expect(sync.status, WorkspaceSyncStatus.saved);
      sync.dispose();
    },
  );

  test(
    'expired vault links are removed without resurrecting them after save',
    () async {
      final server = DraftServer();
      server.remote['attachments']['files'][0]['expires_at'] =
          '2000-01-01T00:00:00Z';
      final sync = server.make();
      await sync.restore();
      await sync.sync();
      await sync.editFields({'motivation': '新計畫'});
      await sync.sync();
      expect(server.remote['attachments']['files'], isEmpty);
      expect(sync.draft['attachments']['files'], isEmpty);
      expect(sync.hasPendingChanges, isFalse);
      sync.dispose();
    },
  );

  test(
    'an open editor uses its displayed base even after a background refresh',
    () async {
      final server = DraftServer();
      final sync = server.make();
      await sync.restore();
      await sync.sync();
      final snapshot = sync.editorSnapshot;
      server.remote['answers']['motivation'] = '電腦在編輯期間改過';
      server.remote['revision'] = 2;
      await sync.sync();
      await sync.editFields({
        'motivation': '手機還在舊表單編輯',
      }, editorSnapshot: snapshot);
      await sync.sync();
      expect(sync.status, WorkspaceSyncStatus.conflict);
      expect(server.puts, 0);
      sync.dispose();
    },
  );

  test(
    'server/account/school caches are isolated and logout ignores late PUTs',
    () async {
      final server = DraftServer();
      final sync = server.make();
      await sync.restore();
      await sync.sync();
      await sync.editFields({'motivation': '秘密一般草稿'});
      final other = server.make(account: 'other');
      await other.restore();
      final school = server.make(school: '其他母校');
      await school.restore();
      final origin = server.make(
        otherApi: ExchangeApi(baseUrl: 'https://elsewhere.test/'),
      );
      await origin.restore();
      expect(other.draft['answers'], isEmpty);
      expect(school.draft['answers'], isEmpty);
      expect(origin.draft['answers'], isEmpty);
      server.hold = Completer();
      server.entered = Completer();
      final sending = sync.sync();
      await server.entered!.future;
      sync.dispose();
      await ApplicationDraftSync.clearAccountCache(
        server.api.baseUrl,
        'student',
      );
      server.hold!.complete();
      await sending;
      expect(
        await const FlutterSecureStorage().read(key: sync.cacheKey),
        isNull,
      );
      other.dispose();
      school.dispose();
      origin.dispose();
    },
  );
}
