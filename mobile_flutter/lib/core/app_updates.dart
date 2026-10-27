import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AppRelease {
  const AppRelease(this.version, this.downloadUrl, this.pageUrl, this.bytes);
  final String version;
  final Uri downloadUrl;
  final Uri pageUrl;
  final int bytes;

  static int compareVersions(String a, String b) {
    final left = a.split('.').map(int.parse).toList();
    final right = b.split('.').map(int.parse).toList();
    for (var i = 0; i < 3; i++) {
      final result = left[i].compareTo(right[i]);
      if (result != 0) return result;
    }
    return 0;
  }

  static AppRelease? newest(dynamic data, String installed) {
    if (data is! List || !RegExp(r'^\d+\.\d+\.\d+$').hasMatch(installed)) {
      throw const FormatException(
        'Invalid release response or installed version',
      );
    }
    AppRelease? newest;
    for (final row in data) {
      if (row is! Map || row['draft'] != false || row['published_at'] == null) {
        continue;
      }
      final tag = row['tag_name']?.toString() ?? '';
      final match = RegExp(
        r'^android-v(\d+\.\d+\.\d+)(-preview)?$',
      ).firstMatch(tag);
      if (match == null) continue;
      final version = match.group(1)!;
      if (compareVersions(version, installed) <= 0) continue;
      final assets = row['assets'];
      if (assets is! List) continue;
      final filename = 'UniWay-$version${match.group(2) ?? ''}.apk';
      for (final asset in assets) {
        if (asset is! Map ||
            asset['name'] != filename ||
            asset['state'] != 'uploaded') {
          continue;
        }
        final size = asset['size'];
        final url = Uri.tryParse(
          asset['browser_download_url']?.toString() ?? '',
        );
        final expected = Uri.https(
          'github.com',
          '/blizzard-new/abroad/releases/download/$tag/$filename',
        );
        if (size is! int || size <= 0 || url != expected) continue;
        if (newest == null || compareVersions(version, newest.version) > 0) {
          newest = AppRelease(
            version,
            expected,
            Uri.https('github.com', '/blizzard-new/abroad/releases/tag/$tag'),
            size,
          );
        }
      }
    }
    return newest;
  }
}

class AppUpdateController extends ChangeNotifier {
  AppUpdateController({
    http.Client? client,
    Future<String> Function()? installedVersion,
    DateTime Function()? clock,
  }) : _client = client ?? http.Client(),
       _installedVersion =
           installedVersion ??
           (() async => (await PackageInfo.fromPlatform()).version),
       _clock = clock ?? DateTime.now;

  static final releasesUri = Uri.https(
    'api.github.com',
    '/repos/blizzard-new/abroad/releases',
    {'per_page': '100'},
  );
  final http.Client _client;
  final Future<String> Function() _installedVersion;
  final DateTime Function() _clock;
  Future<AppRelease?>? _inFlight;
  bool _disposed = false;
  bool checking = false;
  bool promptOpen = false;
  String version = '';
  String? error;
  AppRelease? available;
  DateTime? _failedAt;

  Future<AppRelease?> check({bool manual = false}) {
    return _inFlight ??= _check(manual).whenComplete(() => _inFlight = null);
  }

  Future<AppRelease?> _check(bool manual) async {
    checking = true;
    error = null;
    _notify();
    try {
      version = await _installedVersion();
      final prefs = await SharedPreferences.getInstance();
      final last = prefs.getInt('app_update_checked:$version');
      final now = _clock();
      if (!manual &&
          ((last != null &&
                  now.difference(DateTime.fromMillisecondsSinceEpoch(last)) <
                      const Duration(hours: 6)) ||
              (_failedAt != null &&
                  now.difference(_failedAt!) < const Duration(minutes: 15)))) {
        return available;
      }
      // This public client never receives an account token or private app data.
      final response = await _client
          .get(
            releasesUri,
            headers: {
              'Accept': 'application/vnd.github+json',
              'User-Agent': 'UniWay-Android',
            },
          )
          .timeout(const Duration(seconds: 12));
      if (response.statusCode != 200) {
        throw const FormatException('Release service unavailable');
      }
      final release = AppRelease.newest(
        jsonDecode(utf8.decode(response.bodyBytes)),
        version,
      );
      if (_disposed) return null;
      available = release;
      _failedAt = null;
      await prefs.setInt(
        'app_update_checked:$version',
        now.millisecondsSinceEpoch,
      );
      return available;
    } catch (_) {
      _failedAt = _clock();
      error = '暫時無法檢查版本，請確認網路後再試。';
      return null;
    } finally {
      checking = false;
      _notify();
    }
  }

  Future<bool> shouldPrompt(AppRelease release) async {
    final prefs = await SharedPreferences.getInstance();
    final until = prefs.getInt('app_update_later:${release.version}');
    return until == null || _clock().millisecondsSinceEpoch >= until;
  }

  Future<void> remindTomorrow(AppRelease release) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(
      'app_update_later:${release.version}',
      _clock().add(const Duration(hours: 24)).millisecondsSinceEpoch,
    );
  }

  void _notify() {
    if (!_disposed) notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _client.close();
    super.dispose();
  }
}
