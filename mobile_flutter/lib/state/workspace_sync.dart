import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../data/exchange_api.dart';
import '../data/models.dart';

enum WorkspaceSyncStatus { loading, saved, pending, syncing, conflict, expired }

JsonMap copyWorkspace(JsonMap value) => jsonMap(jsonDecode(jsonEncode(value)));

bool _equal(dynamic a, dynamic b) {
  if (a is Map && b is Map) {
    return a.length == b.length &&
        a.keys.every((key) => b.containsKey(key) && _equal(a[key], b[key]));
  }
  if (a is List && b is List) {
    return a.length == b.length &&
        List.generate(a.length, (i) => i).every((i) => _equal(a[i], b[i]));
  }
  return a == b;
}

class WorkspaceMerge {
  const WorkspaceMerge(this.workspace, this.conflicts);
  final JsonMap workspace;
  final List<String> conflicts;
}

/// Three-way merge. Preserve fields this app does not edit, including Web-only
/// planning metadata. Never silently choose between two changed scalar values.
WorkspaceMerge mergeWorkspaces(
  JsonMap base,
  JsonMap local,
  JsonMap remote, {
  bool? preferLocal,
}) {
  final conflicts = <String>[];
  const absent = _Absent();
  dynamic merge(dynamic b, dynamic l, dynamic r, String path) {
    if (_equal(l, b)) return r;
    if (_equal(r, b) || _equal(l, r)) return l;
    if (path == 'favorite_schools' || path == 'application_schools') {
      final before = b is List ? b.toSet() : <dynamic>{};
      final here = l is List ? l.toSet() : <dynamic>{};
      final there = r is List ? r.toSet() : <dynamic>{};
      return {
        ...there.difference(before.difference(here)),
        ...here.difference(before),
      }.toList();
    }
    if (path == 'deadline_events' && l is List && r is List) {
      JsonMap indexed(dynamic items) => {
        for (final item in items is List ? items : [])
          if (item is Map && item['id'] != null) item['id'].toString(): item,
      };
      return (merge(indexed(b), indexed(l), indexed(r), 'events_by_id') as Map)
          .values
          .toList();
    }
    if (l is Map && r is Map && (b is Map || identical(b, absent))) {
      final before = b is Map ? b : const {};
      final result = <String, dynamic>{};
      for (final key in {...before.keys, ...l.keys, ...r.keys}) {
        final child = merge(
          before.containsKey(key) ? before[key] : absent,
          l.containsKey(key) ? l[key] : absent,
          r.containsKey(key) ? r[key] : absent,
          path.isEmpty ? '$key' : '$path.$key',
        );
        if (!identical(child, absent)) result[key.toString()] = child;
      }
      return result;
    }
    if (path == 'revision' || path == 'updated_at') return r;
    conflicts.add(path);
    return preferLocal == false ? r : l;
  }

  final merged = jsonMap(merge(base, local, remote, ''));
  merged['revision'] = remote['revision'] ?? 0;
  return WorkspaceMerge(merged, conflicts);
}

class _Absent {
  const _Absent();
}

/// One instance is bound to one server, account and university. A disposed
/// instance cannot publish a late HTTP response into the next account's state.
class WorkspaceSync extends ChangeNotifier {
  WorkspaceSync({
    required this.api,
    required this.accountId,
    required this.accessToken,
    required this.homeSchool,
  });

  final ExchangeApi api;
  final String accountId;
  final String accessToken;
  final String homeSchool;
  JsonMap _base = {};
  JsonMap _local = {};
  JsonMap? _conflictingRemote;
  bool _disposed = false;
  Future<void>? _running;
  Future<void> _writes = Future.value();
  WorkspaceSyncStatus status = WorkspaceSyncStatus.loading;
  String? error;
  DateTime? lastSyncedAt;
  List<String> conflicts = [];

  String get cacheKey =>
      'workspace_v2:${Uri.encodeComponent(api.baseUrl)}:${Uri.encodeComponent(accountId)}:${Uri.encodeComponent(homeSchool)}';
  JsonMap get workspace => copyWorkspace(_local);
  bool get hasPendingChanges => !_equal(_base, _local);

  Future<void> restore() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(cacheKey);
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
        await prefs.remove(cacheKey);
      }
    }
    if (_local.isEmpty) {
      _base = {
        'home_school': homeSchool,
        'revision': 0,
        'application_context': {'school_name': homeSchool},
      };
      _local = copyWorkspace(_base);
    }
    status = hasPendingChanges
        ? WorkspaceSyncStatus.pending
        : WorkspaceSyncStatus.saved;
    _emit();
  }

  Future<void> edit(void Function(JsonMap value) mutate) async {
    if (_disposed) return;
    mutate(_local);
    _local['home_school'] = homeSchool;
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
        final prefs = await SharedPreferences.getInstance();
        if (!_disposed) await prefs.setString(cacheKey, serialized);
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
        final remote = await api.workspace(accessToken, homeSchool);
        if (_disposed) return;
        if (remote['home_school'] != homeSchool || remote['revision'] is! int) {
          throw const FormatException('工作區回應無效');
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
        final sent = copyWorkspace(_local);
        try {
          final saved = await api.saveWorkspace(accessToken, sent);
          if (_disposed) return;
          // Preserve edits made while the PUT request was in flight.
          final after = mergeWorkspaces(sent, _local, saved);
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
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(cacheKey);
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
