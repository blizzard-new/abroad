import 'dart:async';
import 'dart:convert';

import 'package:exchange_guide_flutter/data/exchange_api.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:exchange_guide_flutter/state/workspace_sync.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => SharedPreferences.setMockInitialValues({}));
  JsonMap initial() => {
    'home_school': '測試母校',
    'revision': 1,
    'favorite_schools': ['A'],
    'application_context': {'school_name': '測試母校'},
    'document_readiness': {'transcript': 'todo'},
    'preparation_tasks': {
      'web-only': {'effort_hours': 6},
    },
  };

  test('merges unrelated changes and explicit favorite removals', () {
    final base = initial();
    final local = copyWorkspace(base)..['favorite_schools'] = ['B'];
    final remote = copyWorkspace(base)
      ..['favorite_schools'] = ['A', 'C']
      ..['document_readiness'] = {'transcript': 'ready'}
      ..['revision'] = 2;
    final merged = mergeWorkspaces(base, local, remote);
    expect(merged.conflicts, isEmpty);
    expect(merged.workspace['favorite_schools'], unorderedEquals(['B', 'C']));
    expect(merged.workspace['document_readiness']['transcript'], 'ready');
    expect(merged.workspace['preparation_tasks'], base['preparation_tasks']);
  });

  test(
    'same-field conflicts are explicit; unrelated fields survive both choices',
    () {
      final base = initial();
      final local = copyWorkspace(base)
        ..['document_readiness'] = {'transcript': 'preparing'};
      final remote = copyWorkspace(base)
        ..['document_readiness'] = {'transcript': 'ready', 'other': 'ready'};
      final result = mergeWorkspaces(base, local, remote);
      expect(result.conflicts, ['document_readiness.transcript']);
      expect(
        mergeWorkspaces(
          base,
          local,
          remote,
          preferLocal: false,
        ).workspace['document_readiness'],
        {'transcript': 'ready', 'other': 'ready'},
      );
      expect(
        mergeWorkspaces(
          base,
          local,
          remote,
          preferLocal: true,
        ).workspace['document_readiness'],
        {'transcript': 'preparing', 'other': 'ready'},
      );
    },
  );

  test(
    'offline change survives app restart and merges the newer web revision',
    () async {
      var remote = initial();
      var offline = false;
      final api = ExchangeApi(
        baseUrl: 'https://test.example/',
        client: MockClient((request) async {
          expect(request.headers['Authorization'], 'Bearer device-token');
          if (offline) throw http.ClientException('offline');
          if (request.method == 'PUT') {
            final sent = jsonMap(jsonDecode(request.body));
            expect(sent['revision'], remote['revision']);
            remote = sent..['revision'] = (remote['revision'] as int) + 1;
          }
          return http.Response.bytes(
            utf8.encode(jsonEncode({'workspace': remote})),
            200,
          );
        }),
      );
      WorkspaceSync make() => WorkspaceSync(
        api: api,
        accountId: 'student',
        accessToken: 'device-token',
        homeSchool: '測試母校',
      );
      final first = make();
      await first.restore();
      await first.sync();
      offline = true;
      await first.edit((value) => value['favorite_schools'] = ['A', 'B']);
      await first.sync();
      expect(first.status, WorkspaceSyncStatus.pending);
      first.dispose();
      remote['document_readiness'] = {'transcript': 'ready'};
      remote['revision'] = 2;
      final second = make();
      await second.restore();
      expect(second.workspace['favorite_schools'], ['A', 'B']);
      offline = false;
      await second.sync();
      expect(second.status, WorkspaceSyncStatus.saved);
      expect(remote['document_readiness']['transcript'], 'ready');
      expect(remote['favorite_schools'], ['A', 'B']);
      expect(remote['preparation_tasks'], initial()['preparation_tasks']);
      second.dispose();
    },
  );

  test('revision race retries without losing either device edit', () async {
    var remote = initial();
    var writes = 0;
    final api = ExchangeApi(
      baseUrl: 'https://test.example/',
      client: MockClient((request) async {
        if (request.method == 'PUT') {
          if (writes++ == 0) {
            remote['revision'] = 2;
            remote['document_readiness'] = {'transcript': 'ready'};
            return http.Response(
              '{"detail":{"code":"workspace_revision_conflict"}}',
              409,
            );
          }
          final sent = jsonMap(jsonDecode(request.body));
          expect(sent['revision'], 2);
          remote = sent..['revision'] = 3;
        }
        return http.Response.bytes(
          utf8.encode(jsonEncode({'workspace': remote})),
          200,
        );
      }),
    );
    final sync = WorkspaceSync(
      api: api,
      accountId: 'one',
      accessToken: 'token',
      homeSchool: '測試母校',
    );
    await sync.restore();
    await sync.sync();
    await sync.edit((value) => value['favorite_schools'] = ['A', 'B']);
    await sync.sync();
    expect(remote['document_readiness']['transcript'], 'ready');
    expect(remote['favorite_schools'], ['A', 'B']);
    expect(sync.status, WorkspaceSyncStatus.saved);
    sync.dispose();
  });

  test(
    'accounts, schools and servers have distinct cache identities',
    () async {
      final api = ExchangeApi(baseUrl: 'https://test.example/');
      WorkspaceSync make(String account, String school) => WorkspaceSync(
        api: api,
        accountId: account,
        accessToken: 'token',
        homeSchool: school,
      );
      final one = make('one', '測試母校');
      await one.restore();
      await one.edit((value) => value['favorite_schools'] = ['private']);
      final otherAccount = make('two', '測試母校');
      await otherAccount.restore();
      final otherSchool = make('one', '其他母校');
      await otherSchool.restore();
      expect(otherAccount.workspace['favorite_schools'], isNull);
      expect(otherSchool.workspace['favorite_schools'], isNull);
      expect(one.cacheKey, isNot(otherSchool.cacheKey));
      one.dispose();
      otherAccount.dispose();
      otherSchool.dispose();
    },
  );

  test('late response after logout cannot recreate erased cache', () async {
    final response = Completer<http.Response>();
    final api = ExchangeApi(
      baseUrl: 'https://test.example/',
      client: MockClient((_) => response.future),
    );
    final sync = WorkspaceSync(
      api: api,
      accountId: 'one',
      accessToken: 'token',
      homeSchool: '測試母校',
    );
    await sync.restore();
    final pending = sync.sync();
    sync.dispose();
    await sync.clearCache();
    response.complete(
      http.Response.bytes(
        utf8.encode(jsonEncode({'workspace': initial()})),
        200,
      ),
    );
    await pending;
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.containsKey(sync.cacheKey), isFalse);
  });
}
