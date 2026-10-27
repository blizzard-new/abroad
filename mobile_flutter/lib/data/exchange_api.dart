import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import 'models.dart';
import 'forum_models.dart';

class ExchangeApiException implements Exception {
  const ExchangeApiException(this.message, {this.statusCode, this.detail});

  final String message;
  final int? statusCode;
  final dynamic detail;

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
              defaultValue: 'https://app.uniway-tw.com/',
            ),
      );

  final http.Client _client;
  final String baseUrl;

  Future<List<ForumBoard>> forumBoards(String token) async {
    final response = await _client
        .get(
          _uri('community/boards'),
          headers: token.isEmpty ? null : _bearer(token),
        )
        .timeout(const Duration(seconds: 15));
    return jsonMapList(_decode(response)).map(ForumBoard.fromJson).toList();
  }

  Future<ForumPage<ForumPost>> forumFeed(
    String token, {
    String board = '',
    String topic = '',
    String query = '',
    String? cursor,
  }) async {
    final response = await _client
        .get(
          _uri('community/feed', {
            'boards': board,
            'topic': topic,
            'q': query,
            'cursor': cursor,
            'limit': '20',
          }),
          headers: token.isEmpty ? null : _bearer(token),
        )
        .timeout(const Duration(seconds: 15));
    final row = jsonMap(_decode(response));
    return ForumPage(
      jsonMapList(row['items']).map(ForumPost.fromJson).toList(),
      row['next_cursor'] as String?,
    );
  }

  Future<ForumPost> forumPost(String token, String id) async {
    final response = await _client
        .get(
          _uri('community/posts/${Uri.encodeComponent(id)}'),
          headers: token.isEmpty ? null : _bearer(token),
        )
        .timeout(const Duration(seconds: 15));
    return ForumPost.fromJson(_decode(response));
  }

  Future<ForumPage<ForumReply>> forumReplies(
    String token,
    String postId, {
    String? parentId,
    String? cursor,
  }) async {
    final response = await _client
        .get(
          _uri('community/posts/${Uri.encodeComponent(postId)}/comments', {
            'parent_id': parentId,
            'cursor': cursor,
            'limit': '20',
          }),
          headers: token.isEmpty ? null : _bearer(token),
        )
        .timeout(const Duration(seconds: 15));
    final row = jsonMap(_decode(response));
    return ForumPage(
      jsonMapList(row['items']).map(ForumReply.fromJson).toList(),
      row['next_cursor'] as String?,
    );
  }

  Future<void> writeForum(
    String token,
    AnonymousIdentity identity, {
    required String body,
    String? postId,
    String? parentId,
    String? boardId,
    String? title,
    String topic = 'application',
    String postType = 'discussion',
  }) async {
    final response = await _client
        .post(
          _uri(
            postId == null
                ? 'community/posts'
                : 'community/posts/${Uri.encodeComponent(postId)}/comments',
          ),
          headers: {..._auth(identity), ..._bearer(token)},
          body: jsonEncode({
            'body': body,
            'identity_mode': 'anonymous',
            if (postId == null) ...{
              'board_id': boardId,
              'title': title,
              'topic': topic,
              'post_type': postType,
            },
            'parent_id': ?parentId,
          }),
        )
        .timeout(const Duration(seconds: 20));
    _decode(response);
  }

  Future<void> deleteForum(
    String token,
    AnonymousIdentity identity,
    String postId, {
    String? commentId,
  }) async {
    final response = await _client
        .delete(
          _uri(
            'community/posts/${Uri.encodeComponent(postId)}${commentId == null ? '' : '/comments/${Uri.encodeComponent(commentId)}'}',
          ),
          headers: {..._auth(identity), ..._bearer(token)},
        )
        .timeout(const Duration(seconds: 15));
    _decode(response);
  }

  Future<void> registerMobileDevice(
    String token,
    String installation,
    String fid,
  ) async {
    final response = await _client
        .put(
          _uri('/account/mobile-devices'),
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
          body: jsonEncode({'installation_id': installation, 'fid': fid}),
        )
        .timeout(const Duration(seconds: 15));
    if (response.statusCode != 204) _decode(response);
  }

  Future<void> removeMobileDevice(String token, String installation) async {
    final response = await _client
        .delete(
          _uri('/account/mobile-devices/$installation'),
          headers: {'Authorization': 'Bearer $token'},
        )
        .timeout(const Duration(seconds: 8));
    if (response.statusCode != 204) _decode(response);
  }

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
      dynamic detail;
      try {
        final decoded = jsonDecode(body);
        if (decoded is Map && decoded['detail'] != null) {
          detail = decoded['detail'];
          message = detail is Map
              ? (detail['message']?.toString() ?? '資料已在其他裝置更新，請重新同步。')
              : detail.toString();
        }
      } catch (_) {
        if (body.trim().isNotEmpty) message = body.trim();
      }
      throw ExchangeApiException(
        message,
        statusCode: response.statusCode,
        detail: detail,
      );
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

  Future<List<JsonMap>> applicationDrafts(
    String token,
    String homeSchool,
  ) async {
    final response = await _client
        .get(
          _uri('account/application-drafts', {'home_school': homeSchool}),
          headers: _bearer(token),
        )
        .timeout(const Duration(seconds: 15));
    return jsonMapList(jsonMap(_decode(response))['items']);
  }

  Future<JsonMap> saveApplicationDraft(
    String token,
    String templateId,
    JsonMap payload,
  ) async {
    final response = await _client
        .put(
          _uri('account/application-drafts/${Uri.encodeComponent(templateId)}'),
          headers: _bearer(token),
          body: jsonEncode(payload),
        )
        .timeout(const Duration(seconds: 15));
    return jsonMap(_decode(response));
  }

  Future<JsonMap> workspace(String accessToken, String homeSchool) async {
    final response = await _client
        .get(
          _uri('account/workspace', {'home_school': homeSchool}),
          headers: _bearer(accessToken),
        )
        .timeout(const Duration(seconds: 25));
    return jsonMap(jsonMap(_decode(response))['workspace']);
  }

  Future<JsonMap> mobileAuthConfig() async {
    final response = await _client
        .get(_uri('auth/mobile/config'))
        .timeout(const Duration(seconds: 20));
    if (response.statusCode == 404) {
      throw const ExchangeApiException('網站尚未啟用手機登入連接，請先部署手機版後端更新。');
    }
    return jsonMap(_decode(response));
  }

  Future<JsonMap> notifications(String token) async {
    final response = await _client
        .get(_uri('account/notifications'), headers: _bearer(token))
        .timeout(const Duration(seconds: 25));
    return jsonMap(_decode(response));
  }

  Future<void> readNotification(String token, String id) async {
    final response = await _client
        .patch(
          _uri('account/notifications/${Uri.encodeComponent(id)}/read'),
          headers: _bearer(token),
        )
        .timeout(const Duration(seconds: 20));
    _decode(response);
  }

  Future<AccountSession> exchangeMobileCode(
    String code,
    String verifier,
  ) async {
    final response = await _client
        .post(
          _uri('auth/mobile/exchange'),
          headers: const {'Content-Type': 'application/json'},
          body: jsonEncode({'code': code, 'code_verifier': verifier}),
        )
        .timeout(const Duration(seconds: 25));
    return AccountSession.fromJson(_decode(response));
  }

  Future<JsonMap> saveWorkspace(String accessToken, JsonMap workspace) async {
    final response = await _client
        .put(
          _uri('account/workspace'),
          headers: _bearer(accessToken),
          body: jsonEncode(workspace),
        )
        .timeout(const Duration(seconds: 25));
    return jsonMap(jsonMap(_decode(response))['workspace']);
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

  Future<List<SupportedUniversity>> universities() async {
    final response = await _client.get(_uri('universities'));
    return jsonMapList(
      _decode(response),
    ).map(SupportedUniversity.fromJson).toList();
  }

  Future<StudentDashboard> dashboard({
    String school = defaultHomeUniversity,
  }) async {
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

  Future<List<DeadlineRecord>> deadlines({String? school}) async {
    final response = await _client.get(_uri('deadlines', {'school': school}));
    final decoded = _decode(response);
    return jsonMapList(decoded).map(DeadlineRecord.fromJson).toList();
  }

  Future<ApplicationWorkflow> workflow(
    String schoolName, {
    String? homeSchool,
  }) async {
    final response = await _client.get(
      _uri('application-workflow', {
        'school': schoolName,
        'home_school': homeSchool,
      }),
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
      _uri('advisor/ask'),
      headers: const {'Content-Type': 'application/json; charset=utf-8'},
      body: jsonEncode({
        'question': question,
        if (profile != null) 'profile': profile.toJson(),
      }),
    );
    return AdvisorAnswer.fromJson(_decode(response));
  }

  Future<ExperienceDigest> experiences(
    String schoolName, {
    String? homeSchool,
  }) async {
    final response = await _client.get(
      _uri('student-experiences', {
        'school': schoolName,
        'home_school': homeSchool,
      }),
    );
    return ExperienceDigest.fromJson(_decode(response));
  }

  Future<List<ApplicationDocumentTemplate>> applicationTemplates({
    String school = defaultHomeUniversity,
    required String programType,
    List<String> flags = const [],
  }) async {
    final response = await _client.get(
      _uri('application-center/templates', {
        'school': school,
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

  Future<List<ChatMessage>> chat(
    String schoolName, {
    String? homeSchool,
  }) async {
    final response = await _client.get(
      _uri('community/chat', {'school': schoolName, 'home_school': homeSchool}),
    );
    return jsonMapList(_decode(response)).map(ChatMessage.fromJson).toList();
  }

  Future<void> publishChat({
    required AnonymousIdentity identity,
    required String schoolName,
    required String body,
    String? homeSchool,
  }) async {
    final response = await _client.post(
      _uri('community/chat'),
      headers: _auth(identity),
      body: jsonEncode({
        'school_name': schoolName,
        'body': body,
        if (homeSchool != null && homeSchool.trim().isNotEmpty)
          'home_school': homeSchool.trim(),
      }),
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
