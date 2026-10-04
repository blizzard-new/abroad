import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import 'models.dart';

class ExchangeApiException implements Exception {
  const ExchangeApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class ExchangeApi {
  ExchangeApi({http.Client? client, String? baseUrl})
    : _client = client ?? http.Client(),
      baseUrl = _normalizedBaseUrl(
        baseUrl ??
            const String.fromEnvironment(
              'API_BASE_URL',
              defaultValue: 'http://10.0.2.2:8000/',
            ),
      );

  final http.Client _client;
  final String baseUrl;

  String resolveUrl(String value) {
    final uri = Uri.tryParse(value);
    if (uri?.hasScheme == true) return value;
    return Uri.parse(baseUrl).resolve(value).toString();
  }

  static String _normalizedBaseUrl(String value) =>
      value.endsWith('/') ? value : '$value/';

  Uri _uri(String path, [Map<String, String?> query = const {}]) {
    final cleaned = query.map(
      (key, value) =>
          MapEntry(key, value?.trim().isEmpty == true ? null : value),
    )..removeWhere((key, value) => value == null);
    return Uri.parse(
      '$baseUrl${path.startsWith('/') ? path.substring(1) : path}',
    ).replace(queryParameters: cleaned.cast<String, String>());
  }

  dynamic _decode(http.Response response) {
    final body = utf8.decode(response.bodyBytes);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      String message = '伺服器暫時無法完成要求';
      try {
        final decoded = jsonDecode(body);
        if (decoded is Map && decoded['detail'] != null) {
          message = decoded['detail'].toString();
        }
      } catch (_) {
        if (body.trim().isNotEmpty) message = body.trim();
      }
      throw ExchangeApiException(message, statusCode: response.statusCode);
    }
    return body.trim().isEmpty ? null : jsonDecode(body);
  }

  Map<String, String> _auth(AnonymousIdentity identity) => {
    'Content-Type': 'application/json; charset=utf-8',
    'X-Anonymous-ID': identity.id,
    'X-Anonymous-Token': identity.accessToken,
  };

  Map<String, String> _bearer(String accessToken) => {
    'Content-Type': 'application/json; charset=utf-8',
    'Authorization': 'Bearer $accessToken',
  };

  Uri oauthStartUrl(String provider, {String? studentVerificationToken}) =>
      _uri('auth/oauth/$provider/start', {
        'student_verification_token': studentVerificationToken,
      });

  Future<List<AuthProviderStatus>> authProviders() async {
    final response = await _client.get(_uri('auth/providers'));
    return jsonMapList(
      _decode(response),
    ).map(AuthProviderStatus.fromJson).toList();
  }

  Future<AccountSession> register({
    required String email,
    required String password,
    required String displayName,
    required String studentVerificationToken,
  }) async {
    final response = await _client.post(
      _uri('auth/register'),
      headers: const {'Content-Type': 'application/json; charset=utf-8'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'display_name': displayName,
        'student_verification_token': studentVerificationToken,
        'accept_terms': true,
      }),
    );
    return AccountSession.fromJson(_decode(response));
  }

  Future<StudentVerificationResult> verifyStudentCards({
    required String frontPath,
    required String backPath,
    String schoolName = '長庚大學',
  }) async {
    final request =
        http.MultipartRequest('POST', _uri('auth/student-verification'))
          ..fields['school_name'] = schoolName
          ..fields['consent'] = 'true'
          ..files.add(
            await http.MultipartFile.fromPath(
              'front',
              frontPath,
              contentType: _imageMediaType(frontPath),
            ),
          )
          ..files.add(
            await http.MultipartFile.fromPath(
              'back',
              backPath,
              contentType: _imageMediaType(backPath),
            ),
          );
    final streamed = await _client.send(request);
    final response = await http.Response.fromStream(streamed);
    return StudentVerificationResult.fromJson(_decode(response));
  }

  MediaType _imageMediaType(String path) {
    final extension = path.split('.').last.toLowerCase();
    return switch (extension) {
      'png' => MediaType('image', 'png'),
      'webp' => MediaType('image', 'webp'),
      _ => MediaType('image', 'jpeg'),
    };
  }

  Future<AccountSession> login({
    required String email,
    required String password,
  }) async {
    final response = await _client.post(
      _uri('auth/login'),
      headers: const {'Content-Type': 'application/json; charset=utf-8'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    return AccountSession.fromJson(_decode(response));
  }

  Future<AccountProfile> profile(String accessToken) async {
    final response = await _client.get(
      _uri('auth/me'),
      headers: _bearer(accessToken),
    );
    return AccountProfile.fromJson(_decode(response));
  }

  Future<AccountProfile> updateProfile({
    required String accessToken,
    required String displayName,
    required String homeUniversity,
    required List<String> targetCountries,
    required String applicationStage,
  }) async {
    final response = await _client.patch(
      _uri('auth/me'),
      headers: _bearer(accessToken),
      body: jsonEncode({
        'display_name': displayName,
        'home_university': homeUniversity,
        'target_countries': targetCountries,
        'application_stage': applicationStage,
      }),
    );
    return AccountProfile.fromJson(_decode(response));
  }

  Future<AccountProfile> updateFollowedBoards({
    required String accessToken,
    required List<String> followedBoards,
  }) async {
    final response = await _client.patch(
      _uri('auth/me'),
      headers: _bearer(accessToken),
      body: jsonEncode({'followed_boards': followedBoards}),
    );
    return AccountProfile.fromJson(_decode(response));
  }

  Future<void> logout(String accessToken) async {
    final response = await _client.post(
      _uri('auth/logout'),
      headers: _bearer(accessToken),
    );
    _decode(response);
  }

  Future<void> deleteAccount(String accessToken) async {
    final response = await _client.delete(
      _uri('auth/me'),
      headers: _bearer(accessToken),
    );
    _decode(response);
  }

  Future<AnonymousIdentity> accountCommunityIdentity(String accessToken) async {
    final response = await _client.post(
      _uri('auth/community-identity'),
      headers: _bearer(accessToken),
    );
    return AnonymousIdentity.fromJson(_decode(response));
  }

  Future<StudentDashboard> dashboard({String school = '長庚大學'}) async {
    final response = await _client.get(
      _uri('student-dashboard', {'school': school}),
    );
    return StudentDashboard.fromJson(_decode(response));
  }

  Future<Map<String, SchoolVisual>> schoolVisuals() async {
    final response = await _client.get(
      _uri('static/assets/school-images.json'),
    );
    final payload = jsonMap(_decode(response));
    final visuals = jsonMapList(payload['schools'])
        .map(SchoolVisual.fromJson)
        .where((visual) => visual.schoolName.isNotEmpty);
    return {for (final visual in visuals) visual.schoolName: visual};
  }

  Future<List<DeadlineRecord>> deadlines() async {
    final response = await _client.get(_uri('deadlines'));
    final decoded = _decode(response);
    return jsonMapList(decoded).map(DeadlineRecord.fromJson).toList();
  }

  Future<ApplicationWorkflow> workflow(String schoolName) async {
    final response = await _client.get(
      _uri('application-workflow', {'school': schoolName}),
    );
    return ApplicationWorkflow.fromJson(_decode(response));
  }

  Future<AdvisorPlan> advisorPlan(AdvisorProfile profile) async {
    final response = await _client.post(
      _uri('advisor/plan'),
      headers: const {'Content-Type': 'application/json; charset=utf-8'},
      body: jsonEncode(profile.toJson()),
    );
    return AdvisorPlan.fromJson(_decode(response));
  }

  Future<AdvisorAnswer> advisorAsk({
    required String question,
    AdvisorProfile? profile,
  }) async {
    final response = await _client.post(
      _uri('ai/chat'),
      headers: const {'Content-Type': 'application/json; charset=utf-8'},
      body: jsonEncode({
        'question': question,
        if (profile != null) 'profile': profile.toJson(),
      }),
    );
    return AdvisorAnswer.fromJson(_decode(response));
  }

  Future<ExperienceDigest> experiences(String schoolName) async {
    final response = await _client.get(
      _uri('student-experiences', {'school': schoolName}),
    );
    return ExperienceDigest.fromJson(_decode(response));
  }

  Future<List<ApplicationDocumentTemplate>> applicationTemplates({
    required String programType,
    List<String> flags = const [],
  }) async {
    final response = await _client.get(
      _uri('application-center/templates', {
        'program_type': programType,
        'flags': flags.isEmpty ? null : flags.join(','),
      }),
    );
    return jsonMapList(
      _decode(response),
    ).map(ApplicationDocumentTemplate.fromJson).toList();
  }

  Future<Uint8List> applicationPacketPdf(JsonMap payload) async {
    final response = await _client.post(
      _uri('application-center/pdf'),
      headers: const {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/pdf',
      },
      body: jsonEncode(payload),
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final body = utf8.decode(response.bodyBytes);
      var message = 'PDF 產生失敗（${response.statusCode}）';
      try {
        final decoded = jsonDecode(body);
        if (decoded is Map && decoded['detail'] != null) {
          message = decoded['detail'].toString();
        }
      } catch (_) {
        if (body.trim().isNotEmpty) message = body.trim();
      }
      throw ExchangeApiException(message, statusCode: response.statusCode);
    }
    return response.bodyBytes;
  }

  Future<DocumentCheckResult> reviewDocument({
    required String fileName,
    required Uint8List bytes,
    String documentType = 'auto',
    int? expectedWordLimit,
    bool requireSignature = false,
    bool useAi = false,
    bool aiConsentGranted = false,
  }) async {
    final request = http.MultipartRequest('POST', _uri('ai/review-document'))
      ..fields['document_type'] = documentType
      ..fields['require_signature'] = requireSignature.toString()
      ..fields['use_ai'] = useAi.toString()
      ..files.add(
        http.MultipartFile.fromBytes(
          'file',
          bytes,
          filename: fileName,
          contentType: _documentMediaType(fileName),
        ),
      );
    if (expectedWordLimit != null) {
      request.fields['expected_word_limit'] = expectedWordLimit.toString();
    }
    request.fields['ai_consent_granted'] = aiConsentGranted.toString();
    final response = await http.Response.fromStream(
      await _client.send(request),
    );
    return DocumentCheckResult.fromJson(_decode(response));
  }

  Future<DocumentRewriteResult> rewriteDocument({
    required String text,
    required String action,
    required String documentType,
    int? targetWordLimit,
    String schoolContext = '',
    bool aiConsentGranted = false,
  }) async {
    final response = await _client.post(
      _uri('ai/rewrite-document'),
      headers: const {'Content-Type': 'application/json; charset=utf-8'},
      body: jsonEncode({
        'text': text,
        'action': action,
        'document_type': documentType,
        'target_word_limit': ?targetWordLimit,
        'ai_consent_granted': aiConsentGranted,
        if (schoolContext.trim().isNotEmpty)
          'school_context': schoolContext.trim(),
      }),
    );
    return DocumentRewriteResult.fromJson(_decode(response));
  }

  MediaType _documentMediaType(String fileName) {
    final extension = fileName.split('.').last.toLowerCase();
    return switch (extension) {
      'pdf' => MediaType('application', 'pdf'),
      'docx' => MediaType(
        'application',
        'vnd.openxmlformats-officedocument.wordprocessingml.document',
      ),
      _ => MediaType('text', 'plain'),
    };
  }

  Future<AnonymousIdentity> createIdentity(String displayName) async {
    final response = await _client.post(
      _uri('community/identities'),
      headers: const {'Content-Type': 'application/json; charset=utf-8'},
      body: jsonEncode({'display_name': displayName}),
    );
    return AnonymousIdentity.fromJson(_decode(response));
  }

  Future<List<CommunityThread>> posts({
    String? schoolName,
    String? topic,
    String? query,
  }) async {
    final response = await _client.get(
      _uri('community/posts', {
        'school': schoolName,
        'topic': topic,
        'q': query,
      }),
    );
    return jsonMapList(
      _decode(response),
    ).map(CommunityThread.fromJson).toList();
  }

  Future<void> publishPost({
    required AnonymousIdentity identity,
    required String schoolName,
    required String postType,
    required String topic,
    required String country,
    required String academicYear,
    required String applicationStage,
    required String title,
    required String body,
  }) async {
    final response = await _client.post(
      _uri('community/posts'),
      headers: _auth(identity),
      body: jsonEncode({
        'school_name': schoolName,
        'post_type': postType,
        'topic': topic,
        if (country.isNotEmpty) 'country': country,
        if (academicYear.isNotEmpty) 'academic_year': academicYear,
        if (applicationStage.isNotEmpty) 'application_stage': applicationStage,
        'title': title,
        'body': body,
      }),
    );
    _decode(response);
  }

  Future<void> publishComment({
    required AnonymousIdentity identity,
    required String postId,
    required String body,
  }) async {
    final response = await _client.post(
      _uri('community/posts/$postId/comments'),
      headers: _auth(identity),
      body: jsonEncode({'body': body}),
    );
    _decode(response);
  }

  Future<List<ChatMessage>> chat(String schoolName) async {
    final response = await _client.get(
      _uri('community/chat', {'school': schoolName}),
    );
    return jsonMapList(_decode(response)).map(ChatMessage.fromJson).toList();
  }

  Future<void> publishChat({
    required AnonymousIdentity identity,
    required String schoolName,
    required String body,
  }) async {
    final response = await _client.post(
      _uri('community/chat'),
      headers: _auth(identity),
      body: jsonEncode({'school_name': schoolName, 'body': body}),
    );
    _decode(response);
  }

  Future<List<PrivateConversation>> conversations(
    AnonymousIdentity identity,
  ) async {
    final response = await _client.get(
      _uri('community/conversations'),
      headers: _auth(identity),
    );
    return jsonMapList(
      _decode(response),
    ).map(PrivateConversation.fromJson).toList();
  }

  Future<void> inviteConversation({
    required AnonymousIdentity identity,
    required String schoolName,
    required String recipientId,
    required String initialMessage,
  }) async {
    final response = await _client.post(
      _uri('community/conversations'),
      headers: _auth(identity),
      body: jsonEncode({
        'school_name': schoolName,
        'recipient_id': recipientId,
        'initial_message': initialMessage,
      }),
    );
    _decode(response);
  }

  Future<void> acceptConversation({
    required AnonymousIdentity identity,
    required String conversationId,
  }) async {
    final response = await _client.post(
      _uri('community/conversations/$conversationId/accept'),
      headers: _auth(identity),
    );
    _decode(response);
  }

  Future<List<PrivateMessage>> privateMessages({
    required AnonymousIdentity identity,
    required String conversationId,
  }) async {
    final response = await _client.get(
      _uri('community/conversations/$conversationId/messages'),
      headers: _auth(identity),
    );
    return jsonMapList(_decode(response)).map(PrivateMessage.fromJson).toList();
  }

  Future<void> sendPrivateMessage({
    required AnonymousIdentity identity,
    required String conversationId,
    required String body,
  }) async {
    final response = await _client.post(
      _uri('community/conversations/$conversationId/messages'),
      headers: _auth(identity),
      body: jsonEncode({'body': body}),
    );
    _decode(response);
  }

  Future<void> blockIdentity({
    required AnonymousIdentity identity,
    required String targetId,
  }) async {
    final response = await _client.post(
      _uri('community/blocks'),
      headers: _auth(identity),
      body: jsonEncode({'target_id': targetId}),
    );
    _decode(response);
  }

  Future<void> report({
    required AnonymousIdentity identity,
    required String resourceType,
    required String resourceId,
    required String reason,
  }) async {
    final response = await _client.post(
      _uri('community/reports'),
      headers: _auth(identity),
      body: jsonEncode({
        'resource_type': resourceType,
        'resource_id': resourceId,
        'reason': reason,
      }),
    );
    _decode(response);
  }
}
