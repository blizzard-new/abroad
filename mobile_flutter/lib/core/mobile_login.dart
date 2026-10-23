import 'dart:convert';
import 'dart:math';

import 'package:crypto/crypto.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:url_launcher/url_launcher.dart';

import '../data/exchange_api.dart';
import '../data/models.dart';

class MobileLogin {
  MobileLogin(this.api);
  final ExchangeApi api;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  bool _exchanging = false;
  String get _key => 'mobile_login:${Uri.encodeComponent(api.baseUrl)}';

  String _random() => base64Url
      .encode(List.generate(32, (_) => Random.secure().nextInt(256)))
      .replaceAll('=', '');

  Future<void> start(String provider) async {
    final config = await api.mobileAuthConfig();
    if (config['enabled'] != true ||
        config['pkce_method'] != 'S256' ||
        config['redirect_uri'] != 'tw.uniway.app://auth') {
      throw const ExchangeApiException('網站目前不支援安全的手機登入。');
    }
    final verifier = _random();
    final state = _random();
    final challenge = base64Url
        .encode(sha256.convert(ascii.encode(verifier)).bytes)
        .replaceAll('=', '');
    await _storage.write(
      key: _key,
      value: jsonEncode({
        'verifier': verifier,
        'state': state,
        'expires_at': DateTime.now()
            .add(const Duration(minutes: 10))
            .toIso8601String(),
      }),
    );
    final uri = Uri.parse(api.resolveUrl('auth/oauth/$provider/start')).replace(
      queryParameters: {
        'terms': textValue(config['terms_version']),
        'mobile_challenge': challenge,
        'mobile_state': state,
      },
    );
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      await clear();
      throw const ExchangeApiException('無法開啟瀏覽器，請確認手機已安裝瀏覽器。');
    }
  }

  Future<AccountSession?> complete(Uri uri) async {
    if (uri.scheme != 'tw.uniway.app' ||
        uri.host != 'auth' ||
        uri.path.isNotEmpty ||
        _exchanging) {
      return null;
    }
    final saved = await _storage.read(key: _key);
    if (saved == null) return null;
    final flow = jsonMap(jsonDecode(saved));
    final expiry = DateTime.tryParse(textValue(flow['expires_at']));
    if (expiry == null || expiry.isBefore(DateTime.now())) {
      await clear();
      throw const ExchangeApiException('登入已超時，請重新操作。');
    }
    if (uri.queryParameters['state'] != flow['state']) {
      throw const ExchangeApiException('登入來源不相符，請從 App 重新登入。');
    }
    final code = uri.queryParameters['code'] ?? '';
    if (!RegExp(r'^[A-Za-z0-9_-]{43,128}$').hasMatch(code)) {
      throw const ExchangeApiException('登入回應無效，請重新登入。');
    }
    _exchanging = true;
    try {
      final result = await api.exchangeMobileCode(
        code,
        textValue(flow['verifier']),
      );
      await clear();
      return result;
    } finally {
      _exchanging = false;
    }
  }

  Future<void> clear() => _storage.delete(key: _key);
}
