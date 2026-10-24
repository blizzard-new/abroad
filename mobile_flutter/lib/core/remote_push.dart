import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:crypto/crypto.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../data/exchange_api.dart';
import 'account_session_storage.dart';
import 'mobile_notifications.dart';

const _project = String.fromEnvironment('FIREBASE_PROJECT_ID');
const _appId = String.fromEnvironment('FIREBASE_APP_ID');
const _apiKey = String.fromEnvironment('FIREBASE_API_KEY');
const _sender = String.fromEnvironment('FIREBASE_SENDER_ID');
const _storage = FlutterSecureStorage();
const _bindingKey = 'uniway_push_binding';
bool get remotePushConfigured =>
    _project.isNotEmpty &&
    _appId.isNotEmpty &&
    _apiKey.isNotEmpty &&
    _sender.isNotEmpty;

Future<void> _initializeFirebase() async {
  if (Firebase.apps.isEmpty) {
    await Firebase.initializeApp(
      options: const FirebaseOptions(
        apiKey: _apiKey,
        appId: _appId,
        messagingSenderId: _sender,
        projectId: _project,
      ),
    );
  }
}

@pragma('vm:entry-point')
Future<void> uniwayBackgroundMessage(RemoteMessage message) async {
  if (!remotePushConfigured) return;
  await _initializeFirebase();
  await _displayMessage(message);
}

Future<void> _displayMessage(
  RemoteMessage message, {
  bool background = true,
}) async {
  final encoded = await _storage.read(key: _bindingKey);
  if (encoded == null) return;
  final binding = jsonDecode(encoded) as Map<String, dynamic>;
  final accountId = message.data['account_id'];
  final notificationId = message.data['notification_id'];
  if (binding['enabled'] != true ||
      accountId != binding['account_id'] ||
      notificationId == null ||
      notificationId.isEmpty) {
    return;
  }
  final session = await AccountSessionStorage(
    binding['server'] as String,
  ).read();
  if (session?['profile']?['id'] != accountId) return;
  final plugin = FlutterLocalNotificationsPlugin();
  // Foreground initialization already owns the navigation callback.
  if (background) {
    await plugin.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('@drawable/ic_notification'),
      ),
    );
  }
  final digest = sha256
      .convert(utf8.encode('$accountId:$notificationId'))
      .bytes;
  final id =
      ((digest[0] << 24) | (digest[1] << 16) | (digest[2] << 8) | digest[3]) &
      0x7fffffff;
  await plugin.show(
    id: id,
    title: 'UniWay · 申請規定更新',
    body: '你的交換計畫有相關更新，打開查看。',
    notificationDetails: MobileNotifications.details,
    payload: MobileNotificationTarget(
      accountId: accountId!,
      homeSchool: binding['home_school'] as String,
      notificationId: notificationId,
    ).encode(),
  );
}

class RemotePush extends ChangeNotifier {
  RemotePush(this.api);
  final ExchangeApi api;
  StreamSubscription<String>? _registration;
  StreamSubscription<RemoteMessage>? _foreground;
  String? _account;
  String _token = '';
  String? _fid;
  String? error;
  bool registered = false;
  bool _initialized = false;
  bool _disposed = false;
  void _notify() {
    if (!_disposed) notifyListeners();
  }

  int _generation = 0;

  Future<String> _installation() async {
    var id = await _storage.read(key: 'uniway_push_installation');
    if (id == null) {
      final random = Random.secure();
      id = List.generate(
        32,
        (_) => random.nextInt(256).toRadixString(16).padLeft(2, '0'),
      ).join();
      await _storage.write(key: 'uniway_push_installation', value: id);
    }
    return id;
  }

  Future<void> bind({
    required String accountId,
    required String token,
    required String homeSchool,
    required bool enabled,
  }) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) return;
    if (!enabled || !remotePushConfigured) {
      if (_account != null) await disable();
      return;
    }
    if (_account != null && _account != accountId) await disable();
    _account = accountId;
    _token = token;
    await _storage.write(
      key: _bindingKey,
      value: jsonEncode({
        'server': api.baseUrl,
        'account_id': accountId,
        'home_school': homeSchool,
        'enabled': true,
      }),
    );
    try {
      if (!_initialized) {
        await _initializeFirebase();
        FirebaseMessaging.onBackgroundMessage(uniwayBackgroundMessage);
        _registration = FirebaseMessaging.instance.onRegistered.listen((fid) {
          _fid = fid;
          unawaited(_register());
        });
        _foreground = FirebaseMessaging.onMessage.listen((message) {
          unawaited(_displayMessage(message, background: false));
        });
        _initialized = true;
      }
      await FirebaseMessaging.instance.register();
      if (_fid != null) await _register();
    } catch (_) {
      error = '遠端推播暫時無法連線，本機提醒仍可使用。';
      _notify();
    }
  }

  Future<void> _register() async {
    final generation = _generation;
    final fid = _fid;
    if (fid == null || _account == null) return;
    try {
      final installation = await _installation();
      if (generation != _generation || _account == null) return;
      await api.registerMobileDevice(_token, installation, fid);
      if (generation == _generation) {
        error = null;
        registered = true;
        _notify();
      }
    } catch (_) {
      if (generation == _generation) {
        error = '遠端推播尚未連接後端，本機提醒仍可使用。';
        registered = false;
        _notify();
      }
    }
  }

  Future<void> disable() async {
    _generation++;
    final token = _token;
    _account = null;
    _token = '';
    _fid = null;
    registered = false;
    error = null;
    _notify();
    await _storage.delete(key: _bindingKey);
    if (_initialized) {
      try {
        await FirebaseMessaging.instance.unregister();
      } catch (_) {
        /* Retry on next login. */
      }
    }
    if (token.isNotEmpty) {
      try {
        await api.removeMobileDevice(token, await _installation());
      } catch (_) {
        /* Signed-out binding prevents delivery. */
      }
    }
  }

  @override
  void dispose() {
    _disposed = true;
    _generation++;
    _registration?.cancel();
    _foreground?.cancel();
    super.dispose();
  }
}
