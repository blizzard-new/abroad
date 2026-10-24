import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../data/exchange_api.dart';
import '../data/models.dart';
import 'workspace_sync.dart';

/// One instance is bound to one server, account and university. A disposed
/// instance cannot publish a late HTTP response into the next account's state.
class ApplicationDraftSync extends ChangeNotifier {
  ApplicationDraftSync({
    required this.api,
    required this.accountId,
    required this.accessToken,
    required this.homeSchool,
    required this.template,
  });

  final ExchangeApi api;
  final String accountId;
  final String accessToken;
  final String homeSchool;
  final ApplicationDocumentTemplate template;
  static const _storage = FlutterSecureStorage();
  JsonMap _base = {};
  JsonMap _local = {};
  JsonMap? _conflictingRemote;
  bool _disposed = false;
  Future<void>? _running;
  static Future<void> _writes = Future.value();
  WorkspaceSyncStatus status = WorkspaceSyncStatus.loading;
  String? error;
  DateTime? lastSyncedAt;
  List<String> conflicts = [];

  String get cacheKey =>
      '${accountCachePrefix(api.baseUrl, accountId)}${Uri.encodeComponent(homeSchool)}:${template.id}';
  JsonMap get draft => copyWorkspace(_local);
  JsonMap get editorSnapshot => {
    'base': copyWorkspace(_base),
    'local': copyWorkspace(_local),
  };
  bool get hasPendingChanges => !workspaceValuesEqual(_base, _local);

  Future<void> restore() async {
    final saved = await _storage.read(key: cacheKey);
    if (_disposed) return;
    if (saved != null) {
      try {
        final decoded = jsonMap(jsonDecode(saved));
        _base = jsonMap(decoded['base']);
        _local = jsonMap(decoded['local']);
        lastSyncedAt = DateTime.tryParse(
          decoded['synced_at']?.toString() ?? '',
        );
      } on FormatException {
        await _storage.delete(key: cacheKey);
      }
    }
    if (_local.isEmpty) {
      _base = {
        'home_school': homeSchool,
        'revision': 0,
        'template_id': template.id,
        'template_version': template.version,
        'profile': <String, dynamic>{},
        'answers': <String, dynamic>{},
        'attachments': <String, dynamic>{},
      };
      _local = copyWorkspace(_base);
    }
    status = hasPendingChanges
        ? WorkspaceSyncStatus.pending
        : WorkspaceSyncStatus.saved;
    _emit();
  }

  /// Only known, non-sensitive scalar fields may leave the form. Files and
  /// sensitive values remain in the form's memory; existing vault references
  /// from Web are preserved without uploading anything implicitly.
  Future<void> editFields(
    Map<String, dynamic> values, {
    JsonMap? editorSnapshot,
  }) async {
    if (_disposed) return;
    // Keep the version displayed when editing began. A background refresh must
    // not turn an older open form into a silent overwrite of newer Web fields.
    if (editorSnapshot != null) {
      _base = copyWorkspace(jsonMap(editorSnapshot['base']));
      _local = copyWorkspace(jsonMap(editorSnapshot['local']));
    }
    final profile = jsonMap(_local['profile']);
    final answers = jsonMap(_local['answers']);
    for (final field in template.fields) {
      if (field.sensitive ||
          field.kind == ApplicationFieldKind.files ||
          !values.containsKey(field.id)) {
        continue;
      }
      final value = values[field.id];
      if (value != null &&
          value is! String &&
          value is! bool &&
          value is! num) {
        continue;
      }
      if (field.reusableProfileKey.isNotEmpty) {
        profile[field.reusableProfileKey] = value;
      } else {
        answers[field.id] = value;
      }
    }
    _local['profile'] = profile;
    _local['answers'] = answers;
    _local['template_version'] = template.version;
    status = WorkspaceSyncStatus.pending;
    await _persist();
    _emit();
  }

  Future<void> _persist() {
    final serialized = jsonEncode({
      'base': _base,
      'local': _local,
      'synced_at': lastSyncedAt?.toIso8601String(),
    });
    _writes = _writes.catchError((Object _) {}).then((_) async {
      if (!_disposed) {
        await _storage.write(key: cacheKey, value: serialized);
      }
    });
    return _writes;
  }

  Future<void> sync() {
    if (_disposed) return Future.value();
    return _running ??= _sync().whenComplete(() => _running = null);
  }

  Future<void> _sync() async {
    status = WorkspaceSyncStatus.syncing;
    error = null;
    _emit();
    try {
      for (var attempt = 0; attempt < 4 && !_disposed; attempt++) {
        final drafts = await api.applicationDrafts(accessToken, homeSchool);
        final remote =
            drafts
                .where((item) => item['template_id'] == template.id)
                .firstOrNull ??
            {
              'home_school': homeSchool,
              'template_id': template.id,
              'template_version': template.version,
              'revision': 0,
              'profile': <String, dynamic>{},
              'answers': <String, dynamic>{},
              'attachments': <String, dynamic>{},
            };
        if (_disposed) return;
        if (remote['home_school'] != homeSchool || remote['revision'] is! int) {
          throw const FormatException('草稿回應無效');
        }
        final merged = mergeWorkspaces(_base, _local, remote);
        if (merged.conflicts.isNotEmpty) {
          _conflictingRemote = remote;
          conflicts = merged.conflicts;
          status = WorkspaceSyncStatus.conflict;
          error = '同一項資料也在電腦更新了，請選擇要保留的版本。';
          return;
        }
        _base = copyWorkspace(remote);
        _local = copyWorkspace(merged.workspace);
        await _persist();
        _emit();
        if (!hasPendingChanges) {
          lastSyncedAt = DateTime.now();
          status = WorkspaceSyncStatus.saved;
          await _persist();
          return;
        }
        final beforeSend = copyWorkspace(_local);
        final sent = copyWorkspace(beforeSend);
        sent['attachments'] = {
          for (final entry in jsonMap(sent['attachments']).entries)
            entry.key: jsonMapList(entry.value).where((ref) {
              final expiry = DateTime.tryParse(textValue(ref['expires_at']));
              return expiry == null || expiry.isAfter(DateTime.now());
            }).toList(),
        };
        try {
          final saved = await api.saveApplicationDraft(
            accessToken,
            template.id,
            {
              for (final key in [
                'home_school',
                'template_version',
                'revision',
                'profile',
                'answers',
                'attachments',
              ])
                key: sent[key],
            },
          );
          if (_disposed) return;
          // Preserve edits made while the PUT request was in flight.
          final after = mergeWorkspaces(beforeSend, _local, saved);
          if (after.conflicts.isNotEmpty) {
            _base = beforeSend;
            _conflictingRemote = saved;
            conflicts = after.conflicts;
            status = WorkspaceSyncStatus.conflict;
            error = '草稿也在其他裝置更新，請選擇要保留的版本。';
            await _persist();
            return;
          }
          _base = copyWorkspace(saved);
          _local = after.workspace;
          lastSyncedAt = DateTime.now();
          await _persist();
          if (!hasPendingChanges) {
            status = WorkspaceSyncStatus.saved;
            return;
          }
        } on ExchangeApiException catch (exception) {
          if (exception.statusCode != 409) rethrow;
        }
      }
      status = WorkspaceSyncStatus.pending;
      error = '其他裝置正在更新，手機變更已保留，稍後再同步。';
    } catch (exception) {
      if (_disposed) return;
      status = exception is ExchangeApiException && exception.statusCode == 401
          ? WorkspaceSyncStatus.expired
          : WorkspaceSyncStatus.pending;
      error = status == WorkspaceSyncStatus.expired
          ? '登入已過期，請重新登入。手機變更仍保留在此帳號。'
          : '暫時無法同步，手機變更已保留。';
    } finally {
      _emit();
    }
  }

  Future<void> resolveConflict({required bool preferLocal}) async {
    final remote = _conflictingRemote;
    if (remote == null || _disposed) return;
    _local = mergeWorkspaces(
      _base,
      _local,
      remote,
      preferLocal: preferLocal,
    ).workspace;
    _base = copyWorkspace(remote);
    _conflictingRemote = null;
    conflicts = [];
    await _persist();
    await sync();
  }

  Future<void> clearCache() async {
    await _writes;
    await _storage.delete(key: cacheKey);
  }

  static String accountCachePrefix(String server, String accountId) =>
      'application_draft_v1:${Uri.encodeComponent(server)}:${Uri.encodeComponent(accountId)}:';

  static Future<void> clearAccountCache(String server, String accountId) {
    final prefix = accountCachePrefix(server, accountId);
    _writes = _writes.catchError((Object _) {}).then((_) async {
      for (final key in (await _storage.readAll()).keys.toList()) {
        if (key.startsWith(prefix)) await _storage.delete(key: key);
      }
    });
    return _writes;
  }

  void _emit() {
    if (!_disposed) notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}
