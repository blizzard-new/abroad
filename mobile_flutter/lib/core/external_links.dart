import 'package:url_launcher/url_launcher.dart';

/// Opens only well-formed external HTTPS URLs without embedded credentials.
Future<bool> launchSafeExternalHttpsUrl(String rawUrl) async {
  final trimmed = rawUrl.trim();
  if (trimmed.isEmpty) return false;
  final uri = Uri.tryParse(trimmed);
  if (uri == null ||
      uri.scheme.toLowerCase() != 'https' ||
      uri.host.isEmpty ||
      uri.userInfo.isNotEmpty) {
    return false;
  }
  return launchUrl(uri, mode: LaunchMode.externalApplication);
}
