import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../data/models.dart';

class AccountSessionStorage {
  AccountSessionStorage(String server)
    : key = 'uniway_session:${Uri.encodeComponent(server)}';
  final String key;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<JsonMap?> read() async {
    final value = await _storage.read(key: key);
    if (value == null) return null;
    try {
      return jsonMap(jsonDecode(value));
    } on FormatException {
      await clear();
      return null;
    }
  }

  Future<void> save(String token, AccountProfile profile) => _storage.write(
    key: key,
    value: jsonEncode({
      'access_token': token,
      'profile': {
        'id': profile.id,
        'email': profile.email,
        'display_name': profile.displayName,
        'avatar_url': profile.avatarUrl,
        'home_university': profile.homeUniversity,
        'target_countries': profile.targetCountries,
        'application_stage': profile.applicationStage,
        'school_email_verified': profile.schoolEmailVerified,
        'student_status_verified': profile.studentStatusVerified,
        'verified_university': profile.verifiedUniversity,
        'student_verified_at': profile.studentVerifiedAt,
        'providers': profile.providers,
        'followed_boards': profile.followedBoards,
        'product_tier': profile.productTier.name,
        'email_verified': profile.emailVerified,
      },
    }),
  );

  Future<void> clear() => _storage.delete(key: key);
}
