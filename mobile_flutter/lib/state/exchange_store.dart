import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/widgets.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/application_calendar.dart';
import '../core/account_session_storage.dart';
import '../core/mobile_login.dart';
import '../core/mobile_notifications.dart';
import '../core/remote_push.dart';
import '../core/connected_calendar.dart';
import '../core/student_plan.dart';
import '../core/study_plan_widget_service.dart';
import '../data/exchange_api.dart';
import '../data/models.dart';
import 'workspace_sync.dart';
import 'application_draft_sync.dart';

const _applicationProfileMemoryEnabledKey =
    'application_profile_memory_enabled_v1';
const _applicationProfileMemoryKey = 'application_profile_memory_v1';
const _applicationPersistentProfileKeys = <String>{
  'student_name_zh',
  'student_name_en',
  'student_id',
  'college',
  'department',
  'degree_level',
  'year_level',
  'email',
  'phone',
  'mailing_address',
  'emergency_contact',
  'emergency_phone',
  'guardian_name',
  'guardian_relation',
};

class ExchangeStore extends ChangeNotifier {
  ExchangeStore({
    ExchangeApi? api,
    CalendarSyncService? calendarSync,
    StudyPlanWidgetBridge? widgetBridge,
  }) : api = api ?? ExchangeApi(),
       calendarSync = calendarSync ?? CalendarSyncService(),
       widgetBridge = widgetBridge ?? StudyPlanWidgetService();

  final ExchangeApi api;
  final CalendarSyncService calendarSync;
  final StudyPlanWidgetBridge widgetBridge;
  late final AccountSessionStorage sessionStorage = AccountSessionStorage(
    api.baseUrl,
  );
  WorkspaceSync? workspaceSync;
  final Map<String, ApplicationDraftSync> _draftSyncs = {};

  ApplicationDraftSync? applicationDraft(String templateId) =>
      _draftSyncs[templateId];

  Future<ApplicationDraftSync?> openApplicationDraft(
    ApplicationDocumentTemplate template,
  ) async {
    if (account == null || accessToken.isEmpty) return null;
    var sync = _draftSyncs[template.id];
    if (sync == null) {
      sync = ApplicationDraftSync(
        api: api,
        accountId: account!.id,
        accessToken: accessToken,
        homeSchool: selectedUniversity,
        template: template,
      );
      _draftSyncs[template.id] = sync;
      final current = sync;
      sync.addListener(() {
        if (_disposed || _draftSyncs[template.id] != current) return;
        _applyApplicationDraft(template, current);
        notifyListeners();
      });
      await sync.restore();
    }
    await sync.sync();
    return _draftSyncs[template.id] == sync ? sync : null;
  }

  void _applyApplicationDraft(
    ApplicationDocumentTemplate template,
    ApplicationDraftSync sync,
  ) {
    final draft = sync.draft;
    final profile = jsonMap(draft['profile']);
    final answers = jsonMap(draft['answers']);
    final current = applicationAnswers.putIfAbsent(template.id, () => {});
    for (final field in template.fields) {
      if (field.sensitive || field.kind == ApplicationFieldKind.files) continue;
      if (field.reusableProfileKey.isNotEmpty) {
        if (profile.containsKey(field.reusableProfileKey)) {
          applicationProfile[field.reusableProfileKey] =
              profile[field.reusableProfileKey];
        }
      } else if (answers.containsKey(field.id)) {
        current[field.id] = answers[field.id];
      } else {
        current.remove(field.id);
      }
    }
  }

  void _disposeDrafts() {
    for (final sync in _draftSyncs.values) {
      sync.dispose();
    }
    _draftSyncs.clear();
  }

  late final MobileLogin mobileLogin = MobileLogin(api);
  late final MobileNotifications mobileNotifications = MobileNotifications(
    api.baseUrl,
  );
  String? mobileLoginError;
  int navigationTab = 0;

  void selectMainTab(int value) {
    navigationTab = value.clamp(0, 4);
    notifyListeners();
  }

  Timer? _workspaceTimer;
  bool _disposed = false;

  String _localKey(String key) =>
      'local_v2:${Uri.encodeComponent(api.baseUrl)}:${account?.id ?? 'guest'}:${Uri.encodeComponent(selectedUniversity)}:$key';

  List<SupportedUniversity> universities = defaultSupportedUniversities;
  String selectedUniversity = defaultHomeUniversity;
  Map<String, SchoolVisual> _schoolVisualsCache = const {};
  StudentDashboard? dashboard;
  List<DeadlineRecord> deadlines = const [];
  List<AuthProviderStatus> authProviders = const [];
  AccountProfile? account;
  String accessToken = '';
  AnonymousIdentity? identity;
  bool isLoading = false;
  bool isAuthenticating = false;
  bool isVerifyingStudent = false;
  bool isUpdatingBoardFollow = false;
  bool isCalendarSyncing = false;
  String? error;
  String? calendarSyncError;
  String schoolSearchQuery = '';
  final Set<String> favorites = {};
  final Set<int> completedSteps = {};
  final Map<String, DocumentPreparationStatus> documentStatuses = {};
  final Map<String, ExchangeBudgetPlan> budgetPlans = {};
  final List<ApplicationCalendarEvent> personalCalendarEvents = [];
  StudentVerificationResult? studentVerification;
  StudentPlanProfile? planProfile;
  List<ApplicationDocumentTemplate> applicationTemplates = const [];
  ApplicationCenterContext applicationContext =
      const ApplicationCenterContext();
  final Map<String, dynamic> applicationProfile = {};
  final Map<String, Map<String, dynamic>> applicationAnswers = {};
  final Map<String, ApplicationDocumentSelectionState> applicationSelections =
      {};
  bool applicationProfileMemoryEnabled = false;
  bool isApplicationDocumentsLoading = false;
  bool isGeneratingApplicationPdf = false;
  String? applicationDocumentsError;

  SupportedUniversity get activeUniversity =>
      resolveSupportedUniversity(selectedUniversity, universities);

  Future<List<SupportedUniversity>> _loadUniversities() async {
    try {
      final loaded = await api.universities();
      return loaded.isNotEmpty ? loaded : defaultSupportedUniversities;
    } catch (_) {
      return defaultSupportedUniversities;
    }
  }

  Future<void> _loadSelectedUniversity() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString('selected_university_v1');
    final resolved = tryResolveSupportedUniversity(saved, universities);
    if (resolved != null) {
      selectedUniversity = resolved.schoolName;
    }
  }

  Future<void> initialize() async {
    if (isLoading) return;
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      await _loadSelectedUniversity();
      await _restoreAccount();
      await mobileNotifications.initialize();
      await mobileNotifications.bindAccount(account?.id);
      if (account == null) await _syncStudyPlanWidget();
      await _loadApplicationDocumentState();
      final prefs = await SharedPreferences.getInstance();
      if (!prefs.containsKey('selected_university_v1')) {
        final accountUniversity = tryResolveSupportedUniversity(
          account?.homeUniversity,
          universities,
        );
        if (accountUniversity != null) {
          selectedUniversity = accountUniversity.schoolName;
        }
      }
      applicationContext = applicationContext.copyWith(
        schoolName: selectedUniversity,
      );
      await _openWorkspace();
      // Sign-in must remain available even when a catalogue/calendar request fails.
      authProviders = await api.authProviders().timeout(
        const Duration(seconds: 15),
      );
      notifyListeners();
      final results = await Future.wait<dynamic>([
        _loadUniversities(),
        api.dashboard(school: selectedUniversity),
        api.deadlines(school: selectedUniversity),
        Future.value(authProviders),
        _loadLocalProgress(),
        _loadSchoolVisuals(),
        _loadCalendarEvents(),
        calendarSync.initialize(),
        widgetBridge.initialize(),
      ]).timeout(const Duration(seconds: 30));
      universities = results[0] as List<SupportedUniversity>;
      _schoolVisualsCache = results[5] as Map<String, SchoolVisual>;
      dashboard = (results[1] as StudentDashboard).withSchoolVisuals(
        _schoolVisualsCache,
        api.resolveUrl,
      );
      deadlines = results[2] as List<DeadlineRecord>;
      authProviders = results[3] as List<AuthProviderStatus>;
      _applyWorkspace();
      await loadApplicationTemplates(notify: false);
      await _syncStudyPlanWidget();
    } catch (exception) {
      error = exception.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> selectUniversity(String schoolName) async {
    final resolved = resolveSupportedUniversity(schoolName, universities);
    if (selectedUniversity == resolved.schoolName && dashboard != null) {
      return;
    }
    selectedUniversity = resolved.schoolName;
    _resetPrivateState();
    applicationContext = applicationContext.copyWith(
      schoolName: selectedUniversity,
    );
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('selected_university_v1', selectedUniversity);
    await _loadApplicationDocumentState();
    await _loadLocalProgress();
    await _loadCalendarEvents();
    await _openWorkspace();
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      final results = await Future.wait<dynamic>([
        api.dashboard(school: selectedUniversity),
        api.deadlines(school: selectedUniversity),
      ]);
      if (_schoolVisualsCache.isEmpty) {
        _schoolVisualsCache = await _loadSchoolVisuals();
      }
      dashboard = (results[0] as StudentDashboard).withSchoolVisuals(
        _schoolVisualsCache,
        api.resolveUrl,
      );
      deadlines = results[1] as List<DeadlineRecord>;
      await loadApplicationTemplates(notify: false);
      await _syncStudyPlanWidget();
    } catch (exception) {
      error = exception.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refresh() async {
    dashboard = null;
    deadlines = const [];
    await initialize();
  }

  Future<AnonymousIdentity> ensureIdentity() async {
    if (identity != null) return identity!;
    if (account == null || accessToken.isEmpty) {
      throw const ExchangeApiException('請先登入帳號，再參與社群。');
    }
    final token = accessToken;
    final accountId = account!.id;
    final created = await api.accountCommunityIdentity(token);
    if (_disposed || token != accessToken || accountId != account?.id) {
      throw const ExchangeApiException('登入狀態已改變，請重新開啟論壇。');
    }
    identity = created;
    await _saveIdentity(created);
    notifyListeners();
    return created;
  }

  Future<void> _saveIdentity(AnonymousIdentity value) async {
    // Community credentials remain in memory; regenerate from the secure account session.
  }

  Future<void> _restoreAccount() async {
    final prefs = await SharedPreferences.getInstance();
    // Legacy tokens had no server/account scope. Do not send them to a new server.
    await _clearAccountPreferences(prefs);
    final saved = await sessionStorage.read();
    final savedToken = saved?['access_token']?.toString() ?? '';
    if (savedToken.isEmpty) return;
    account = AccountProfile.fromJson(saved?['profile']);
    accessToken = savedToken;
    try {
      account = await api.profile(savedToken);
      await sessionStorage.save(savedToken, account!);
    } on ExchangeApiException catch (exception) {
      if (exception.statusCode == 401) {
        await sessionStorage.clear();
        account = null;
        accessToken = '';
        _resetPrivateState();
      }
    } catch (_) {
      // A temporary offline/server failure must not log out a cached account.
    }
  }

  Future<void> register({
    required String email,
    required String password,
    required String displayName,
  }) async {
    final verification = studentVerification;
    if (verification == null || verification.verificationToken.isEmpty) {
      throw const ExchangeApiException('請先完成學生證正反面驗證。');
    }
    await _authenticate(
      () => api.register(
        email: email,
        password: password,
        displayName: displayName,
        studentVerificationToken: verification.verificationToken,
      ),
    );
    studentVerification = null;
    notifyListeners();
  }

  Future<StudentVerificationResult> verifyStudentCards({
    required String frontPath,
    required String backPath,
    String? schoolName,
  }) async {
    if (isVerifyingStudent) {
      throw const ExchangeApiException('學生證正在辨識中。');
    }
    isVerifyingStudent = true;
    notifyListeners();
    try {
      final result = await api.verifyStudentCards(
        frontPath: frontPath,
        backPath: backPath,
        schoolName: (schoolName == null || schoolName.trim().isEmpty)
            ? selectedUniversity
            : schoolName.trim(),
      );
      studentVerification = result;
      return result;
    } finally {
      isVerifyingStudent = false;
      notifyListeners();
    }
  }

  void clearStudentVerification() {
    studentVerification = null;
    notifyListeners();
  }

  Future<void> login({required String email, required String password}) async {
    await _authenticate(() => api.login(email: email, password: password));
  }

  Future<void> startMobileLogin(String provider) async {
    mobileLoginError = null;
    await mobileLogin.start(provider);
  }

  Future<void> completeMobileLogin(Uri uri) async {
    try {
      final session = await mobileLogin.complete(uri);
      if (session != null && !_disposed) {
        await _authenticate(() async => session);
        await refresh();
      }
    } catch (exception) {
      mobileLoginError = exception.toString();
      if (!_disposed) notifyListeners();
    }
  }

  Future<void> _authenticate(Future<AccountSession> Function() action) async {
    if (isAuthenticating) return;
    isAuthenticating = true;
    notifyListeners();
    try {
      final session = await action();
      _resetPrivateState();
      account = session.profile;
      accessToken = session.accessToken;
      identity = null;
      final prefs = await SharedPreferences.getInstance();
      await sessionStorage.save(session.accessToken, session.profile);
      await prefs.remove('anonymous_id');
      await prefs.remove('anonymous_name');
      await prefs.remove('anonymous_token');
      selectedUniversity = session.profile.homeUniversity;
      await prefs.setString('selected_university_v1', selectedUniversity);
      await _loadApplicationDocumentState();
      await _loadLocalProgress();
      await _loadCalendarEvents();
      await _openWorkspace();
    } finally {
      isAuthenticating = false;
      notifyListeners();
    }
  }

  Future<void> updateAccount({
    required String displayName,
    required String homeUniversity,
    required List<String> targetCountries,
    required String applicationStage,
  }) async {
    if (accessToken.isEmpty) {
      throw const ExchangeApiException('請先登入帳號。');
    }
    account = await api.updateProfile(
      accessToken: accessToken,
      displayName: displayName,
      homeUniversity: homeUniversity,
      targetCountries: targetCountries,
      applicationStage: applicationStage,
    );
    identity = null;
    await ensureIdentity();
    final resolved = tryResolveSupportedUniversity(
      homeUniversity,
      universities,
    );
    if (resolved != null && resolved.schoolName != selectedUniversity) {
      await selectUniversity(resolved.schoolName);
      return;
    }
    notifyListeners();
  }

  Future<void> logout() async {
    await remotePush.disable();
    final token = accessToken;
    if (token.isNotEmpty) {
      try {
        await api.logout(token).timeout(const Duration(seconds: 8));
      } catch (_) {
        // Local sign-out still completes if the server session already expired.
      }
    }
    await _clearAccount();
  }

  Future<void> deleteAccount() async {
    if (accessToken.isEmpty) return;
    await api.deleteAccount(accessToken);
    await _clearAccount();
  }

  Future<void> _clearAccount() async {
    await remotePush.disable();
    final oldAccount = account?.id;
    _disposeDrafts();
    if (oldAccount != null) {
      await ApplicationDraftSync.clearAccountCache(api.baseUrl, oldAccount);
    }
    final oldWorkspace = workspaceSync;
    _workspaceTimer?.cancel();
    workspaceSync = null;
    oldWorkspace?.dispose();
    await oldWorkspace?.clearCache();
    await sessionStorage.clear();
    await mobileLogin.clear();
    await mobileNotifications.bindAccount(null);
    account = null;
    accessToken = '';
    identity = null;
    final prefs = await SharedPreferences.getInstance();
    if (oldAccount != null) {
      final origin = Uri.encodeComponent(api.baseUrl);
      for (final key in prefs.getKeys().toList()) {
        if (key.startsWith('local_v2:$origin:$oldAccount:') ||
            key.startsWith(
              'workspace_v2:$origin:${Uri.encodeComponent(oldAccount)}:',
            )) {
          await prefs.remove(key);
        }
      }
    }
    _resetPrivateState();
    await _clearAccountPreferences(prefs);
    await _syncStudyPlanWidget();
    notifyListeners();
  }

  Future<void> _clearAccountPreferences(SharedPreferences prefs) async {
    await prefs.remove('account_access_token');
    await prefs.remove('anonymous_id');
    await prefs.remove('anonymous_name');
    await prefs.remove('anonymous_token');
  }

  Future<void> _loadLocalProgress() async {
    final prefs = await SharedPreferences.getInstance();
    favorites
      ..clear()
      ..addAll(prefs.getStringList(_localKey('favorite_schools')) ?? const []);
    completedSteps
      ..clear()
      ..addAll(
        (prefs.getStringList(_localKey('completed_steps')) ?? const [])
            .map(int.tryParse)
            .whereType<int>(),
      );

    final profileJson = prefs.getString(_localKey('student_plan_profile_v1'));
    if (profileJson != null) {
      try {
        final decoded = jsonDecode(profileJson);
        if (decoded is Map) {
          planProfile = StudentPlanProfile.fromJson(
            Map<String, dynamic>.from(decoded),
          );
        }
      } catch (_) {
        await prefs.remove(_localKey('student_plan_profile_v1'));
      }
    }

    documentStatuses.clear();
    final statusesJson = prefs.getString(_localKey('document_statuses_v1'));
    if (statusesJson != null) {
      try {
        final decoded = jsonDecode(statusesJson);
        if (decoded is Map) {
          decoded.forEach((key, value) {
            final status = DocumentPreparationStatus.values
                .where((item) => item.name == value.toString())
                .firstOrNull;
            if (status != null) documentStatuses[key.toString()] = status;
          });
        }
      } catch (_) {
        await prefs.remove(_localKey('document_statuses_v1'));
      }
    }
    for (var index = 0; index < applicationDocumentLabels.length; index++) {
      final label = applicationDocumentLabels[index];
      documentStatuses.putIfAbsent(
        label,
        () => completedSteps.contains(index)
            ? DocumentPreparationStatus.ready
            : DocumentPreparationStatus.todo,
      );
    }

    budgetPlans.clear();
    final budgetJson = prefs.getString(_localKey('budget_plans_v1'));
    if (budgetJson != null) {
      try {
        final decoded = jsonDecode(budgetJson);
        if (decoded is Map) {
          decoded.forEach((key, value) {
            if (value is Map) {
              budgetPlans[key.toString()] = ExchangeBudgetPlan.fromJson(
                Map<String, dynamic>.from(value),
              );
            }
          });
        }
      } catch (_) {
        await prefs.remove(_localKey('budget_plans_v1'));
      }
    }
  }

  Future<void> _loadApplicationDocumentState() async {
    final prefs = await SharedPreferences.getInstance();
    applicationProfileMemoryEnabled =
        prefs.getBool(_localKey(_applicationProfileMemoryEnabledKey)) ?? false;
    applicationProfile.clear();
    if (applicationProfileMemoryEnabled) {
      final profileJson = prefs.getString(
        _localKey(_applicationProfileMemoryKey),
      );
      if (profileJson != null) {
        try {
          final decoded = jsonDecode(profileJson);
          if (decoded is Map) {
            applicationProfile.addAll(
              _sanitizeApplicationProfileForMemory(
                Map<String, dynamic>.from(decoded),
              ),
            );
          }
        } catch (_) {
          await prefs.remove(_localKey(_applicationProfileMemoryKey));
        }
      }
    }
    final contextJson = prefs.getString(
      _localKey('application_center_context_v1'),
    );
    if (contextJson != null) {
      try {
        applicationContext = ApplicationCenterContext.fromJson(
          jsonDecode(contextJson),
        );
      } catch (_) {
        await prefs.remove(_localKey('application_center_context_v1'));
      }
    }

    applicationSelections.clear();
    final selectionsJson = prefs.getString(
      _localKey('application_center_selections_v1'),
    );
    if (selectionsJson != null) {
      try {
        final decoded = jsonDecode(selectionsJson);
        if (decoded is Map) {
          decoded.forEach((key, value) {
            applicationSelections[key.toString()] =
                ApplicationDocumentSelectionState.fromJson(value);
          });
        }
      } catch (_) {
        await prefs.remove(_localKey('application_center_selections_v1'));
      }
    }
  }

  Future<void> _persistApplicationDocumentState() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _localKey('application_center_context_v1'),
      jsonEncode(applicationContext.toJson()),
    );
    await prefs.setString(
      _localKey('application_center_selections_v1'),
      jsonEncode(
        applicationSelections.map(
          (key, value) => MapEntry(key, value.toJson()),
        ),
      ),
    );
  }

  Future<void> loadApplicationTemplates({bool notify = true}) async {
    if (isApplicationDocumentsLoading) return;
    isApplicationDocumentsLoading = true;
    applicationDocumentsError = null;
    if (notify) notifyListeners();
    try {
      final loaded = await api.applicationTemplates(
        school: selectedUniversity,
        programType: applicationContext.programType,
        flags: applicationContext.flags,
      );
      applicationTemplates = loaded;
      for (final template in loaded) {
        applicationSelections.putIfAbsent(
          template.id,
          () =>
              ApplicationDocumentSelectionState.initial(template.defaultCopies),
        );
      }
      await _persistApplicationDocumentState();
    } catch (exception) {
      applicationDocumentsError = exception.toString();
      applicationTemplates = const [];
    } finally {
      isApplicationDocumentsLoading = false;
      if (notify) notifyListeners();
    }
  }

  Future<void> updateApplicationContext(
    ApplicationCenterContext context,
  ) async {
    applicationContext = context.copyWith(schoolName: selectedUniversity);
    await _editWorkspace((value) {
      value['application_context'] = {
        ...jsonMap(value['application_context']),
        ...applicationContext.toJson(),
      };
    });
    await _persistApplicationDocumentState();
    await loadApplicationTemplates();
  }

  dynamic applicationValue(
    ApplicationDocumentTemplate template,
    ApplicationFormField field,
  ) {
    final answer = applicationAnswers[template.id]?[field.id];
    if (_applicationValuePresent(answer)) return answer;
    if (field.reusableProfileKey.isNotEmpty) {
      return applicationProfile[field.reusableProfileKey];
    }
    return answer;
  }

  bool _applicationValuePresent(dynamic value) {
    if (value == null || value == false) return false;
    if (value is String) return value.trim().isNotEmpty;
    if (value is Iterable) return value.isNotEmpty;
    if (value is Map) return value.isNotEmpty;
    return true;
  }

  Map<String, dynamic> _sanitizeApplicationProfileForMemory(
    Map<String, dynamic> profile,
  ) => Map<String, dynamic>.fromEntries(
    profile.entries.where(
      (entry) =>
          _applicationPersistentProfileKeys.contains(entry.key) &&
          _applicationValuePresent(entry.value) &&
          entry.value is! ApplicationUpload &&
          entry.value is! Iterable &&
          entry.value is! Map,
    ),
  );

  int get applicationRememberedProfileCount =>
      _sanitizeApplicationProfileForMemory(applicationProfile).length;

  int applicationAutofillCount(ApplicationDocumentTemplate template) => template
      .fields
      .where(
        (field) =>
            field.reusableProfileKey.isNotEmpty &&
            _applicationValuePresent(
              applicationProfile[field.reusableProfileKey],
            ),
      )
      .length;

  Future<void> _persistApplicationProfileMemory() async {
    final prefs = await SharedPreferences.getInstance();
    if (!applicationProfileMemoryEnabled) {
      await prefs.remove(_localKey(_applicationProfileMemoryEnabledKey));
      await prefs.remove(_localKey(_applicationProfileMemoryKey));
      return;
    }
    await prefs.setBool(_localKey(_applicationProfileMemoryEnabledKey), true);
    await prefs.setString(
      _localKey(_applicationProfileMemoryKey),
      jsonEncode(_sanitizeApplicationProfileForMemory(applicationProfile)),
    );
  }

  Future<void> setApplicationProfileMemoryEnabled(bool enabled) async {
    applicationProfileMemoryEnabled = enabled;
    await _persistApplicationProfileMemory();
    notifyListeners();
  }

  Future<void> clearApplicationProfileMemory() async {
    applicationProfileMemoryEnabled = false;
    await _persistApplicationProfileMemory();
    notifyListeners();
  }

  bool applicationFieldHasValue(
    ApplicationDocumentTemplate template,
    ApplicationFormField field,
  ) {
    final value = applicationValue(template, field);
    if (field.kind != ApplicationFieldKind.files) {
      return _applicationValuePresent(value);
    }
    final requiredCount = field.minFiles > (field.required ? 1 : 0)
        ? field.minFiles
        : (field.required ? 1 : 0);
    return value is List && value.length >= requiredCount;
  }

  ApplicationFormCompletion applicationTemplateCompletion(
    ApplicationDocumentTemplate template,
  ) {
    final required = template.fields.where((field) => field.required).toList();
    final completed = required
        .where((field) => applicationFieldHasValue(template, field))
        .length;
    return ApplicationFormCompletion(
      completed: completed,
      total: required.length,
    );
  }

  ApplicationFormCompletion get applicationProfileCompletion {
    const required = [
      'student_name_zh',
      'student_name_en',
      'student_id',
      'college',
      'department',
      'degree_level',
      'year_level',
      'email',
      'phone',
    ];
    return ApplicationFormCompletion(
      completed: required
          .where((key) => _applicationValuePresent(applicationProfile[key]))
          .length,
      total: required.length,
    );
  }

  List<ApplicationFormField> get applicationProfileFields {
    final fields = <String, ApplicationFormField>{};
    for (final template in applicationTemplates) {
      for (final field in template.fields) {
        if (field.reusableProfileKey.isNotEmpty) {
          fields.putIfAbsent(field.reusableProfileKey, () => field);
        }
      }
    }
    return fields.values.toList();
  }

  List<ApplicationDocumentTemplate> get initialApplicationTemplates {
    final stage = applicationContext.programType == 'short_term_credit'
        ? '短期課程申請'
        : '校內申請';
    return applicationTemplates
        .where((template) => template.stage == stage)
        .toList();
  }

  int get initialApplicationReadyCount => initialApplicationTemplates
      .where((template) => applicationTemplateCompletion(template).ready)
      .length;

  int get applicationFormReadyCount => applicationTemplates
      .where((template) => applicationTemplateCompletion(template).ready)
      .length;

  List<ApplicationDocumentTemplate> get selectedApplicationTemplates =>
      applicationTemplates
          .where(
            (template) => applicationSelections[template.id]?.selected == true,
          )
          .toList();

  int get selectedApplicationCopies => selectedApplicationTemplates.fold(
    0,
    (total, template) =>
        total +
        (applicationSelections[template.id]?.copies ?? template.defaultCopies),
  );

  bool get applicationPacketReady =>
      selectedApplicationTemplates.isNotEmpty &&
      selectedApplicationTemplates.every(
        (template) => applicationTemplateCompletion(template).ready,
      );

  Future<void> saveApplicationProfile(Map<String, dynamic> values) async {
    applicationProfile
      ..clear()
      ..addAll(
        values.map(
          (key, value) => MapEntry(key, value is String ? value.trim() : value),
        ),
      );
    await _persistApplicationProfileMemory();
    notifyListeners();
  }

  Future<void> saveApplicationDocument(
    ApplicationDocumentTemplate template,
    Map<String, dynamic> values, {
    bool markReady = true,
    JsonMap? draftSnapshot,
  }) async {
    final draftSync = _draftSyncs[template.id];
    final documentValues = <String, dynamic>{};
    for (final field in template.fields) {
      if (!values.containsKey(field.id)) continue;
      final value = values[field.id];
      if (field.reusableProfileKey.isNotEmpty) {
        applicationProfile[field.reusableProfileKey] = value;
      } else {
        documentValues[field.id] = value;
      }
    }
    applicationAnswers[template.id] = documentValues;
    final current =
        applicationSelections[template.id] ??
        ApplicationDocumentSelectionState.initial(template.defaultCopies);
    applicationSelections[template.id] = current.copyWith(
      selected: true,
      status: markReady && current.status == ApplicationDocumentProgress.draft
          ? ApplicationDocumentProgress.readyToPrint
          : current.status,
    );
    // Persist safe draft values before any network call; keep raw attachments
    // and sensitive answers in memory only.
    await draftSync?.editFields(values, editorSnapshot: draftSnapshot);
    if (draftSync != null && _draftSyncs[template.id] != draftSync) return;
    await draftSync?.sync();
    if (draftSync != null && _draftSyncs[template.id] != draftSync) return;
    await _syncSelections();
    await _persistApplicationProfileMemory();
    await _persistApplicationDocumentState();
    notifyListeners();
  }

  Future<void> updateApplicationSelection(
    String templateId, {
    bool? selected,
    int? copies,
    ApplicationDocumentProgress? status,
  }) async {
    final template = applicationTemplates
        .where((item) => item.id == templateId)
        .firstOrNull;
    if (template == null) return;
    final current =
        applicationSelections[templateId] ??
        ApplicationDocumentSelectionState.initial(template.defaultCopies);
    applicationSelections[templateId] = current.copyWith(
      selected: selected,
      copies: copies,
      status: status,
    );
    await _syncSelections();
    await _persistApplicationDocumentState();
    notifyListeners();
  }

  dynamic _serializeApplicationValue(dynamic value) {
    if (value is ApplicationUpload) return value.toJson();
    if (value is List) {
      return value.map(_serializeApplicationValue).toList();
    }
    if (value is Map) {
      return value.map(
        (key, item) =>
            MapEntry(key.toString(), _serializeApplicationValue(item)),
      );
    }
    return value;
  }

  JsonMap applicationPacketPayload({String singleTemplateId = ''}) {
    final selected = singleTemplateId.isNotEmpty
        ? applicationTemplates
              .where((template) => template.id == singleTemplateId)
              .toList()
        : selectedApplicationTemplates;
    return {
      'context': applicationContext.toJson(),
      'profile': _serializeApplicationValue(applicationProfile),
      'answers': _serializeApplicationValue(applicationAnswers),
      'selections': selected
          .map(
            (template) => {
              'template_id': template.id,
              'copies': singleTemplateId.isNotEmpty
                  ? 1
                  : applicationSelections[template.id]?.copies ??
                        template.defaultCopies,
            },
          )
          .toList(),
    };
  }

  Future<Uint8List> generateApplicationPdf({
    String singleTemplateId = '',
  }) async {
    final templates = singleTemplateId.isNotEmpty
        ? applicationTemplates
              .where((template) => template.id == singleTemplateId)
              .toList()
        : selectedApplicationTemplates;
    if (templates.isEmpty) {
      throw const ExchangeApiException('請先選擇要加入列印包的文件。');
    }
    final incomplete = templates
        .where((template) => !applicationTemplateCompletion(template).ready)
        .toList();
    if (incomplete.isNotEmpty) {
      throw ExchangeApiException('請先完成「${incomplete.first.shortTitle}」的必填欄位。');
    }
    isGeneratingApplicationPdf = true;
    notifyListeners();
    try {
      return await api.applicationPacketPdf(
        applicationPacketPayload(singleTemplateId: singleTemplateId),
      );
    } finally {
      isGeneratingApplicationPdf = false;
      notifyListeners();
    }
  }

  Future<void> _loadCalendarEvents() async {
    final prefs = await SharedPreferences.getInstance();
    final values =
        prefs.getStringList(_localKey('application_calendar_events')) ??
        const [];
    personalCalendarEvents
      ..clear()
      ..addAll(
        values.expand((value) {
          try {
            final decoded = jsonDecode(value);
            if (decoded is Map<String, dynamic>) {
              return [ApplicationCalendarEvent.fromJson(decoded)];
            }
            if (decoded is Map) {
              return [
                ApplicationCalendarEvent.fromJson(
                  Map<String, dynamic>.from(decoded),
                ),
              ];
            }
          } catch (_) {
            // Ignore a single damaged local event and keep the other tasks.
          }
          return const <ApplicationCalendarEvent>[];
        }),
      );
  }

  List<ApplicationCalendarEvent> get applicationCalendarEvents =>
      mergeApplicationEvents([
        ...officialApplicationEvents(dashboard),
        ...personalCalendarEvents,
      ]);

  WritableCalendar? get connectedCalendar => calendarSync.connectedCalendar;

  bool isCalendarEventSynced(String eventId) => calendarSync.isSynced(eventId);

  List<ApplicationCalendarEvent> get _calendarEventsToSync =>
      applicationCalendarEvents
          .where(
            (event) => !event.isOfficial || calendarSync.hasAnyLink(event.id),
          )
          .toList();

  Future<List<WritableCalendar>> requestWritableCalendars() {
    return _runCalendarOperation(calendarSync.requestWritableCalendars);
  }

  Future<void> openCalendarSettings() => calendarSync.openAppSettings();

  Future<void> connectCalendar(WritableCalendar calendar) {
    return _runCalendarOperation(
      () => calendarSync.connect(calendar, _calendarEventsToSync),
    );
  }

  Future<void> disconnectCalendar() async {
    await calendarSync.disconnect();
    calendarSyncError = null;
    notifyListeners();
  }

  Future<void> syncAllCalendarEvents() {
    return _runCalendarOperation(
      () => calendarSync.syncAll(_calendarEventsToSync),
    );
  }

  Future<void> syncCalendarEvent(ApplicationCalendarEvent event) {
    return _runCalendarOperation(() => calendarSync.syncEvent(event));
  }

  Future<bool> addCalendarEvent(ApplicationCalendarEvent event) async {
    personalCalendarEvents.add(event);
    await _saveCalendarEvents();
    notifyListeners();
    var synced = false;
    if (connectedCalendar != null) {
      try {
        await syncCalendarEvent(event);
        synced = true;
      } catch (_) {
        synced = false;
      }
    }
    unawaited(_syncStudyPlanWidget());
    return synced;
  }

  Future<bool> updateCalendarEvent(ApplicationCalendarEvent event) async {
    final index = personalCalendarEvents.indexWhere(
      (value) => value.id == event.id,
    );
    if (index < 0) return false;
    personalCalendarEvents[index] = event;
    await _saveCalendarEvents();
    notifyListeners();
    var synced = false;
    if (connectedCalendar != null) {
      try {
        await syncCalendarEvent(event);
        synced = true;
      } catch (_) {
        synced = false;
      }
    }
    unawaited(_syncStudyPlanWidget());
    return synced;
  }

  Future<void> deleteCalendarEvent(String eventId) async {
    if (connectedCalendar != null && isCalendarEventSynced(eventId)) {
      await _runCalendarOperation(() => calendarSync.deleteEvent(eventId));
    }
    personalCalendarEvents.removeWhere((event) => event.id == eventId);
    await _saveCalendarEvents();
    notifyListeners();
    unawaited(_syncStudyPlanWidget());
  }

  Future<T> _runCalendarOperation<T>(Future<T> Function() operation) async {
    isCalendarSyncing = true;
    calendarSyncError = null;
    notifyListeners();
    try {
      return await operation();
    } catch (exception) {
      calendarSyncError = exception.toString();
      rethrow;
    } finally {
      isCalendarSyncing = false;
      notifyListeners();
    }
  }

  Future<void> _saveCalendarEvents() async {
    final events = personalCalendarEvents.toList();
    await _editWorkspace((value) {
      final previous = {
        for (final item in jsonMapList(value['deadline_events']))
          textValue(item['id']): item,
      };
      value['deadline_events'] = events.map((event) {
        final serialized = event.toJson()..remove('is_official');
        return {
          ...?previous[event.id],
          ...serialized,
          'origin': event.isOfficial ? 'official' : 'personal',
        };
      }).toList();
    });
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(
      _localKey('application_calendar_events'),
      personalCalendarEvents
          .map((event) => jsonEncode(event.toJson()))
          .toList(),
    );
  }

  Future<Map<String, SchoolVisual>> _loadSchoolVisuals() async {
    try {
      return await api.schoolVisuals();
    } catch (_) {
      return const {};
    }
  }

  Future<void> toggleFavorite(String schoolName) async {
    if (!favorites.add(schoolName)) favorites.remove(schoolName);
    await _editWorkspace(
      (value) => value['favorite_schools'] = favorites.toList()..sort(),
    );
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(
      _localKey('favorite_schools'),
      favorites.toList()..sort(),
    );
    notifyListeners();
    await _syncStudyPlanWidget();
  }

  bool followsBoard(String boardName) =>
      account?.followedBoards.contains(boardName) == true;

  Future<void> toggleBoardFollow(String boardName) async {
    if (account == null || accessToken.isEmpty) {
      throw const ExchangeApiException('請先登入帳號，再追蹤看板。');
    }
    if (isUpdatingBoardFollow) return;
    isUpdatingBoardFollow = true;
    notifyListeners();
    try {
      final boards = account!.followedBoards.toSet();
      if (!boards.add(boardName)) boards.remove(boardName);
      account = await api.updateFollowedBoards(
        accessToken: accessToken,
        followedBoards: boards.toList()..sort(),
      );
    } finally {
      isUpdatingBoardFollow = false;
      notifyListeners();
    }
  }

  Future<void> toggleProgress(int index) async {
    if (index < 0 || index >= applicationDocumentLabels.length) return;
    final label = applicationDocumentLabels[index];
    final current = documentStatus(label);
    await setDocumentStatus(
      label,
      current == DocumentPreparationStatus.ready
          ? DocumentPreparationStatus.todo
          : DocumentPreparationStatus.ready,
    );
  }

  Future<void> savePlanProfile(StudentPlanProfile profile) async {
    planProfile = profile;
    await _editWorkspace((value) {
      final existing = jsonMap(
        jsonMap(value['selection_conditions'])['profile'],
      );
      value['selection_conditions'] = {
        'profile': {
          ...existing,
          ...profile.toJson(),
          'language_test': profile.languageTest.isEmpty
              ? null
              : profile.languageTest,
        },
      };
    });
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _localKey('student_plan_profile_v1'),
      jsonEncode(profile.toJson()),
    );
    notifyListeners();
    await _syncStudyPlanWidget();
  }

  Future<void> clearPlanProfile() async {
    planProfile = null;
    await _editWorkspace(
      (value) => value['selection_conditions'] = {'profile': null},
    );
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_localKey('student_plan_profile_v1'));
    notifyListeners();
    await _syncStudyPlanWidget();
  }

  DocumentPreparationStatus documentStatus(String label) =>
      documentStatuses[label] ?? DocumentPreparationStatus.todo;

  Future<void> setDocumentStatus(
    String label,
    DocumentPreparationStatus status,
  ) async {
    documentStatuses[label] = status;
    await _editWorkspace((value) {
      value['document_readiness'] = {
        ...jsonMap(value['document_readiness']),
        _documentId(label): status.name,
      };
    });
    final index = applicationDocumentLabels.indexOf(label);
    if (index >= 0) {
      if (status == DocumentPreparationStatus.ready) {
        completedSteps.add(index);
      } else {
        completedSteps.remove(index);
      }
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _localKey('document_statuses_v1'),
      jsonEncode(
        documentStatuses.map((key, value) => MapEntry(key, value.name)),
      ),
    );
    await prefs.setStringList(
      _localKey('completed_steps'),
      completedSteps.map((value) => value.toString()).toList(),
    );
    notifyListeners();
    await _syncStudyPlanWidget();
  }

  Future<void> saveBudgetPlan(ExchangeBudgetPlan plan) async {
    budgetPlans[plan.schoolName] = plan;
    await _editWorkspace((value) {
      final budgets = jsonMap(value['budget_plans']);
      budgets[plan.schoolName] = {
        ...jsonMap(budgets[plan.schoolName]),
        'currency': plan.currency,
        'months': plan.months,
        'housing': plan.monthlyHousing,
        'food': plan.monthlyFood,
        'transport': plan.monthlyTransport,
        'other': plan.monthlyOther,
        'one_time': plan.oneTimeCosts,
        'scholarship': plan.scholarship,
        'saved_at': DateTime.now().toUtc().toIso8601String(),
      };
      value['budget_plans'] = budgets;
    });
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _localKey('budget_plans_v1'),
      jsonEncode(
        budgetPlans.map((key, value) => MapEntry(key, value.toJson())),
      ),
    );
    notifyListeners();
    await _syncStudyPlanWidget();
  }

  ExchangeBudgetPlan? budgetFor(String schoolName) => budgetPlans[schoolName];

  List<SchoolMatch> get rankedSchoolMatches {
    final profile = planProfile;
    final schools = dashboard?.partnerUniversities;
    if (profile == null || schools == null) return const [];
    return rankPartnerSchools(
      schools,
      profile,
      academicScoreMinimum: activeUniversity.academicScoreMinimum,
    );
  }

  int get documentReadyCount => applicationDocumentLabels
      .where(
        (label) => documentStatus(label) == DocumentPreparationStatus.ready,
      )
      .length;

  int get planCompletionPercent {
    var completed = 0;
    if (planProfile?.isConfigured == true) completed++;
    if (favorites.isNotEmpty) completed++;
    if (budgetPlans.isNotEmpty) completed++;
    if (documentReadyCount >= 3) completed++;
    if (personalCalendarEvents.isNotEmpty || connectedCalendar != null) {
      completed++;
    }
    return completed * 20;
  }

  String get nextPlanAction {
    if (planProfile?.isConfigured != true) return '完成資格與交換目標設定';
    if (favorites.isEmpty) return '從推薦結果收藏候選學校';
    if (budgetPlans.isEmpty) return '估算交換預算與可用補助';
    if (documentReadyCount < 3) return '準備校內申請文件';
    if (personalCalendarEvents.isEmpty && connectedCalendar == null) {
      return '建立申請時程並連接日曆';
    }
    return '核對下一個官方截止日';
  }

  Future<bool> canRequestHomeWidgetPin() => widgetBridge.canRequestPin();

  Future<void> requestHomeWidgetPin({
    StudyPlanWidgetStyle style = StudyPlanWidgetStyle.overview,
  }) => widgetBridge.requestPin(style: style);

  Future<void> _syncStudyPlanWidget() async {
    if (account == null) {
      await widgetBridge.sync(
        const StudyPlanWidgetSnapshot(
          nextTitle: '登入 UniWay，開始你的交換計畫',
          nextDateLabel: '與電腦共用帳號與進度',
          progressLabel: '尚未登入',
        ),
      );
      return;
    }
    try {
      await mobileNotifications.schedule(
        account!.id,
        selectedUniversity,
        personalCalendarEvents,
      );
    } on Exception {
      // A denied notification permission must not prevent saving the student's work.
    }
    final confirmedEvents = personalCalendarEvents.toList()
      ..sort((a, b) => a.date.compareTo(b.date));
    final upcoming = confirmedEvents
        .where(
          (event) => !dateOnly(event.date).isBefore(dateOnly(DateTime.now())),
        )
        .firstOrNull;
    final title = upcoming?.title ?? nextPlanAction;
    final dateLabel = upcoming == null
        ? (planProfile?.goalLabel.isNotEmpty == true
              ? planProfile!.goalLabel
              : '開啟 App 開始規劃')
        : '截止 ${upcoming.date.year}/${upcoming.date.month}/${upcoming.date.day}';
    await widgetBridge.sync(
      StudyPlanWidgetSnapshot(
        nextTitle: title,
        nextDateLabel: dateLabel,
        progressLabel: '準備進度 $planCompletionPercent%',
        deadlineIso: upcoming == null
            ? ''
            : '${upcoming.date.year.toString().padLeft(4, '0')}-${upcoming.date.month.toString().padLeft(2, '0')}-${upcoming.date.day.toString().padLeft(2, '0')}',
        tasks: applicationDocumentLabels
            .where(
              (label) =>
                  documentStatus(label) != DocumentPreparationStatus.ready,
            )
            .take(3)
            .toList(),
        updatedLabel: workspaceSync?.lastSyncedAt == null
            ? '尚未同步'
            : '更新 ${workspaceSync!.lastSyncedAt!.month}/${workspaceSync!.lastSyncedAt!.day} ${workspaceSync!.lastSyncedAt!.hour.toString().padLeft(2, '0')}:${workspaceSync!.lastSyncedAt!.minute.toString().padLeft(2, '0')}',
      ),
    );
  }

  void setSchoolSearchQuery(String value) {
    schoolSearchQuery = value.trim();
    notifyListeners();
  }

  // Match Web's documentChecklistItems(): IDs derive from the displayed title.
  static String _documentId(String label) => label
      .trim()
      .toLowerCase()
      .replaceAll(RegExp(r'[^a-z0-9\u4e00-\u9fff]+'), '-');

  Future<void> _openWorkspace() async {
    _workspaceTimer?.cancel();
    workspaceSync?.dispose();
    workspaceSync = null;
    await mobileNotifications.bindAccount(account?.id);
    if (account == null || accessToken.isEmpty) return;
    await remotePush.bind(
      accountId: account!.id,
      token: accessToken,
      homeSchool: selectedUniversity,
      enabled: mobileNotifications.enabled,
    );
    final sync = WorkspaceSync(
      api: api,
      accountId: account!.id,
      accessToken: accessToken,
      homeSchool: selectedUniversity,
    );
    workspaceSync = sync;
    sync.addListener(() {
      if (_disposed || workspaceSync != sync) return;
      _applyWorkspace();
      notifyListeners();
      unawaited(_syncStudyPlanWidget());
    });
    await sync.restore();
    await sync.sync();
    if (_disposed || workspaceSync != sync) return;
    _workspaceTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      unawaited(sync.sync());
      for (final draft in _draftSyncs.values.toList()) {
        unawaited(draft.sync());
      }
    });
  }

  late final RemotePush remotePush = RemotePush(api)
    ..addListener(_remotePushChanged);
  void _remotePushChanged() {
    if (!_disposed) notifyListeners();
  }

  Future<void> synchronizeWorkspace() async {
    await workspaceSync?.sync();
    await Future.wait(_draftSyncs.values.toList().map((sync) => sync.sync()));
    if (account != null) {
      await remotePush.bind(
        accountId: account!.id,
        token: accessToken,
        homeSchool: selectedUniversity,
        enabled: mobileNotifications.enabled,
      );
    }
  }

  Future<bool> enableMobileNotifications() async {
    if (account == null) return false;
    await mobileNotifications.bindAccount(account!.id);
    final enabled = await mobileNotifications.enable();
    await remotePush.bind(
      accountId: account!.id,
      token: accessToken,
      homeSchool: selectedUniversity,
      enabled: enabled,
    );
    if (enabled) {
      await mobileNotifications.schedule(
        account!.id,
        selectedUniversity,
        personalCalendarEvents,
      );
    }
    notifyListeners();
    return enabled;
  }

  Future<void> disableMobileNotifications() async {
    await remotePush.disable();
    await mobileNotifications.disable();
    notifyListeners();
  }

  Future<void> _editWorkspace(void Function(JsonMap value) mutate) async {
    final sync = workspaceSync;
    if (sync == null) return;
    await sync.edit(mutate);
    unawaited(sync.sync());
  }

  void _resetPrivateState() {
    _disposeDrafts();
    favorites.clear();
    completedSteps.clear();
    documentStatuses.clear();
    budgetPlans.clear();
    personalCalendarEvents.clear();
    planProfile = null;
    applicationProfile.clear();
    applicationAnswers.clear();
    applicationSelections.clear();
    applicationProfileMemoryEnabled = false;
    applicationContext = ApplicationCenterContext(
      schoolName: selectedUniversity,
    );
    applicationTemplates = const [];
    studentVerification = null;
    applicationDocumentsError = null;
  }

  void _applyWorkspace() {
    final sync = workspaceSync;
    if (sync == null) return;
    final value = sync.workspace;
    favorites
      ..clear()
      ..addAll(stringList(value['favorite_schools']));
    final conditions = jsonMap(value['selection_conditions']);
    planProfile = conditions['profile'] is Map
        ? StudentPlanProfile.fromJson(jsonMap(conditions['profile']))
        : null;
    final readiness = jsonMap(value['document_readiness']);
    documentStatuses.clear();
    completedSteps.clear();
    for (final item in readiness.entries) {
      final status = DocumentPreparationStatus.values
          .where((v) => v.name == item.value)
          .firstOrNull;
      if (status != null) documentStatuses[item.key] = status;
    }
    for (var i = 0; i < applicationDocumentLabels.length; i++) {
      final label = applicationDocumentLabels[i];
      final status =
          documentStatuses[_documentId(label)] ??
          DocumentPreparationStatus.todo;
      documentStatuses[label] = status;
      if (status == DocumentPreparationStatus.ready) completedSteps.add(i);
    }
    applicationContext = ApplicationCenterContext.fromJson(
      value['application_context'],
    );
    applicationSelections
      ..clear()
      ..addAll(
        jsonMap(value['application_selections']).map(
          (key, item) =>
              MapEntry(key, ApplicationDocumentSelectionState.fromJson(item)),
        ),
      );
    budgetPlans.clear();
    for (final entry in jsonMap(value['budget_plans']).entries) {
      final budget = jsonMap(entry.value);
      budgetPlans[entry.key] = ExchangeBudgetPlan.fromJson({
        'school_name': entry.key,
        'currency': budget['currency'],
        'months': budget['months'],
        'monthly_housing': budget['housing'],
        'monthly_food': budget['food'],
        'monthly_transport': budget['transport'],
        'monthly_other': budget['other'],
        'one_time_costs': budget['one_time'],
        'scholarship': budget['scholarship'],
      });
    }
    personalCalendarEvents
      ..clear()
      ..addAll(
        jsonMapList(value['deadline_events'])
            .where((event) => parseDateKey(textValue(event['date'])) != null)
            .map(
              (event) => ApplicationCalendarEvent.fromJson({
                ...event,
                'is_official': event['origin'] == 'official',
              }),
            ),
      );
  }

  Future<void> _syncSelections() async {
    final local = Map<String, ApplicationDocumentSelectionState>.from(
      applicationSelections,
    );
    await _editWorkspace((value) {
      final selections = jsonMap(value['application_selections']);
      for (final entry in local.entries) {
        selections[entry.key] = {
          ...jsonMap(selections[entry.key]),
          ...entry.value.toJson(),
        };
      }
      value['application_selections'] = selections;
    });
  }

  @override
  void dispose() {
    remotePush.dispose();
    _disposed = true;
    _workspaceTimer?.cancel();
    workspaceSync?.dispose();
    _disposeDrafts();
    super.dispose();
  }

  bool get hasChosenSchool => favorites.isNotEmpty;

  bool get hasCheckedEligibility =>
      account != null && account!.applicationStage != 'exploring';

  bool get hasPreparedDocuments => completedSteps.length >= 3;

  bool get hasSubmittedApplication => const {
    'submitted',
    'accepted',
    'abroad',
    'returned',
  }.contains(account?.applicationStage);
}

class ExchangeStoreScope extends InheritedNotifier<ExchangeStore> {
  const ExchangeStoreScope({
    required ExchangeStore store,
    required super.child,
    super.key,
  }) : super(notifier: store);

  static ExchangeStore of(BuildContext context, {bool listen = true}) {
    final scope = listen
        ? context.dependOnInheritedWidgetOfExactType<ExchangeStoreScope>()
        : context.getInheritedWidgetOfExactType<ExchangeStoreScope>();
    assert(scope != null, 'ExchangeStoreScope is missing');
    return scope!.notifier!;
  }
}
