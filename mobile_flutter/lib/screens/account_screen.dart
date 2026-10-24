import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import 'app_update_prompt.dart';

enum _AuthMode { login, register }

class AccountScreen extends StatefulWidget {
  const AccountScreen({super.key, this.embedded = false});

  final bool embedded;

  @override
  State<AccountScreen> createState() => _AccountScreenState();
}

class _AccountScreenState extends State<AccountScreen> {
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  final displayNameController = TextEditingController();
  final homeUniversityController = TextEditingController();
  final targetCountriesController = TextEditingController();
  final imagePicker = ImagePicker();

  _AuthMode mode = _AuthMode.login;
  String applicationStage = 'exploring';
  String? error;
  String? verificationMessage;
  bool profileInitialized = false;
  bool verificationConsent = false;
  bool termsAccepted = false;
  XFile? frontCard;
  XFile? backCard;

  @override
  void dispose() {
    unawaited(_removeTemporaryImage(frontCard));
    unawaited(_removeTemporaryImage(backCard));
    emailController.dispose();
    passwordController.dispose();
    displayNameController.dispose();
    homeUniversityController.dispose();
    targetCountriesController.dispose();
    super.dispose();
  }

  void _loadProfile(AccountProfile profile) {
    if (profileInitialized) return;
    profileInitialized = true;
    displayNameController.text = profile.displayName;
    homeUniversityController.text = profile.homeUniversity;
    targetCountriesController.text = profile.targetCountries.join('、');
    applicationStage = profile.applicationStage;
  }

  Future<void> _submitAuth(ExchangeStore store) async {
    final email = emailController.text.trim();
    final password = passwordController.text;
    final displayName = displayNameController.text.trim();
    if (mode == _AuthMode.register && store.studentVerification == null) {
      setState(() => error = '請先完成學生證正反面驗證。');
      return;
    }
    if (!email.contains('@')) {
      setState(() => error = '請輸入有效的 Email。');
      return;
    }
    if (password.length < 8) {
      setState(() => error = '密碼至少需要 8 個字元。');
      return;
    }
    if (mode == _AuthMode.register && displayName.length < 2) {
      setState(() => error = '公開暱稱至少需要 2 個字元。');
      return;
    }
    setState(() => error = null);
    try {
      if (mode == _AuthMode.login) {
        await store.login(email: email, password: password);
      } else {
        await store.register(
          email: email,
          password: password,
          displayName: displayName,
        );
      }
      passwordController.clear();
      profileInitialized = false;
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('帳號已登入。')));
      }
    } catch (exception) {
      if (mounted) setState(() => error = exception.toString());
    }
  }

  Future<void> _pickCard({required bool front}) async {
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      useSafeArea: true,
      showDragHandle: true,
      builder: (sheetContext) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              front ? '加入學生證正面' : '加入學生證反面',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 14),
            FilledButton.icon(
              onPressed: () => Navigator.pop(sheetContext, ImageSource.camera),
              icon: const Icon(Icons.photo_camera_outlined),
              label: const Text('直接拍攝'),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: () => Navigator.pop(sheetContext, ImageSource.gallery),
              icon: const Icon(Icons.photo_library_outlined),
              label: const Text('從照片選擇'),
            ),
          ],
        ),
      ),
    );
    if (source == null) return;
    final picked = await imagePicker.pickImage(
      source: source,
      imageQuality: 88,
      maxWidth: 2200,
      requestFullMetadata: false,
    );
    if (picked == null || !mounted) return;
    final previous = front ? frontCard : backCard;
    setState(() {
      if (front) {
        frontCard = picked;
      } else {
        backCard = picked;
      }
      error = null;
      verificationMessage = null;
    });
    unawaited(_removeTemporaryImage(previous));
  }

  Future<void> _verifyStudentCards(ExchangeStore store) async {
    if (frontCard == null || backCard == null) {
      setState(() => error = '請先加入學生證正面與反面。');
      return;
    }
    if (!verificationConsent) {
      setState(() => error = '請先同意一次性學生身分辨識。');
      return;
    }
    setState(() {
      error = null;
      verificationMessage = null;
    });
    try {
      final result = await store.verifyStudentCards(
        frontPath: frontCard!.path,
        backPath: backCard!.path,
      );
      final oldFront = frontCard;
      final oldBack = backCard;
      if (mounted) {
        setState(() {
          frontCard = null;
          backCard = null;
          verificationMessage = '${result.schoolName}學生身分已驗證';
        });
      }
      await Future.wait([
        _removeTemporaryImage(oldFront),
        _removeTemporaryImage(oldBack),
      ]);
    } catch (exception) {
      if (mounted) setState(() => error = exception.toString());
    }
  }

  Future<void> _removeTemporaryImage(XFile? image) async {
    if (image == null) return;
    try {
      final tempPath = (await getTemporaryDirectory()).absolute.path;
      final file = File(image.path);
      if (file.absolute.path.startsWith(tempPath) && await file.exists()) {
        await file.delete();
      }
    } catch (_) {
      // The operating system may already have cleared the image-picker cache.
    }
  }

  Future<void> _saveProfile(ExchangeStore store) async {
    setState(() => error = null);
    try {
      await store.updateAccount(
        displayName: displayNameController.text.trim(),
        homeUniversity: homeUniversityController.text.trim(),
        targetCountries: targetCountriesController.text
            .split(RegExp(r'[,，、]'))
            .map((value) => value.trim())
            .where((value) => value.isNotEmpty)
            .toList(),
        applicationStage: applicationStage,
      );
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('個人設定已儲存。')));
      }
    } catch (exception) {
      if (mounted) setState(() => error = exception.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final content = store.account == null
        ? _buildAuth(context, store)
        : _buildProfile(context, store, store.account!);

    if (widget.embedded) return content;
    return SafeArea(
      bottom: false,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 18, 20, 118),
        children: [content, const SizedBox(height: 20), const AppUpdateTile()],
      ),
    );
  }

  Widget _buildAuth(BuildContext context, ExchangeStore store) {
    if (!store.authProviders.any((p) => p.provider == 'email' && p.enabled)) {
      return _buildGoogleAuth(context, store);
    }
    final verified = store.studentVerification != null;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          children: [
            ExchangeIconBadge(Icons.explore_outlined),
            SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '交換指南帳號',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
                  ),
                  Text('收藏、時程與留學社群都能同步'),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 28),
        Text(
          mode == _AuthMode.login ? '歡迎回來' : '建立你的交換檔案',
          style: Theme.of(context).textTheme.displaySmall,
        ),
        const SizedBox(height: 8),
        Text(
          mode == _AuthMode.login
              ? '登入後繼續追蹤收藏、申請時程與社群討論。'
              : '先確認在學身分，再建立不公開真實姓名的個人檔案。',
          style: Theme.of(
            context,
          ).textTheme.bodyLarge?.copyWith(color: ExchangeColors.secondaryInk),
        ),
        const SizedBox(height: 22),
        SegmentedButton<_AuthMode>(
          segments: const [
            ButtonSegment(value: _AuthMode.login, label: Text('登入')),
            ButtonSegment(value: _AuthMode.register, label: Text('建立帳號')),
          ],
          selected: {mode},
          showSelectedIcon: false,
          onSelectionChanged: (value) {
            setState(() {
              mode = value.first;
              error = null;
              verificationMessage = null;
            });
          },
        ),
        const SizedBox(height: 18),
        if (mode == _AuthMode.register && !verified)
          _StudentVerificationCard(
            frontCard: frontCard,
            backCard: backCard,
            consent: verificationConsent,
            isLoading: store.isVerifyingStudent,
            error: error,
            onPickFront: () => _pickCard(front: true),
            onPickBack: () => _pickCard(front: false),
            onConsentChanged: (value) =>
                setState(() => verificationConsent = value ?? false),
            onVerify: () => _verifyStudentCards(store),
          )
        else
          GlassCard(
            child: Column(
              children: [
                if (mode == _AuthMode.register) ...[
                  _VerificationSuccess(
                    message:
                        verificationMessage ??
                        '${store.selectedUniversity}學生身分已驗證',
                  ),
                  const SizedBox(height: 16),
                ],
                CheckboxListTile(
                  value: termsAccepted,
                  onChanged: (value) =>
                      setState(() => termsAccepted = value ?? false),
                  title: const Text('我同意 UniWay 服務條款與隱私權政策'),
                  contentPadding: EdgeInsets.zero,
                ),
                ...store.authProviders
                    .where(
                      (provider) => const {
                        'google',
                        'facebook',
                        'apple',
                      }.contains(provider.provider),
                    )
                    .map(
                      (provider) => Padding(
                        padding: const EdgeInsets.only(bottom: 9),
                        child: _ProviderButton(
                          provider: provider,
                          onLogin: () =>
                              _providerLogin(store, provider.provider),
                        ),
                      ),
                    ),
                const Row(
                  children: [
                    Expanded(child: Divider()),
                    Padding(
                      padding: EdgeInsets.symmetric(horizontal: 12),
                      child: Text('或使用 Email'),
                    ),
                    Expanded(child: Divider()),
                  ],
                ),
                const SizedBox(height: 16),
                if (mode == _AuthMode.register) ...[
                  TextField(
                    controller: displayNameController,
                    textInputAction: TextInputAction.next,
                    decoration: const InputDecoration(
                      labelText: '公開暱稱',
                      prefixIcon: Icon(Icons.badge_outlined),
                    ),
                  ),
                  const SizedBox(height: 12),
                ],
                TextField(
                  controller: emailController,
                  keyboardType: TextInputType.emailAddress,
                  autofillHints: const [AutofillHints.email],
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    prefixIcon: Icon(Icons.alternate_email_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: passwordController,
                  obscureText: true,
                  autofillHints: mode == _AuthMode.login
                      ? const [AutofillHints.password]
                      : const [AutofillHints.newPassword],
                  onSubmitted: (_) => _submitAuth(store),
                  decoration: const InputDecoration(
                    labelText: '密碼',
                    helperText: '至少 8 個字元',
                    prefixIcon: Icon(Icons.lock_outline_rounded),
                  ),
                ),
                if (error != null) ...[
                  const SizedBox(height: 12),
                  _FormError(message: error!),
                ],
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: store.isAuthenticating
                        ? null
                        : () => _submitAuth(store),
                    icon: store.isAuthenticating
                        ? const SizedBox.square(
                            dimension: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Icon(
                            mode == _AuthMode.login
                                ? Icons.login_rounded
                                : Icons.arrow_forward_rounded,
                          ),
                    label: Text(mode == _AuthMode.login ? '登入' : '建立帳號'),
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  '登入信箱與學生證資料不會顯示在公開貼文中。',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildProfile(
    BuildContext context,
    ExchangeStore store,
    AccountProfile profile,
  ) {
    _loadProfile(profile);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            CircleAvatar(
              radius: 32,
              backgroundColor: ExchangeColors.blueSoft,
              foregroundColor: ExchangeColors.blue,
              child: Text(
                profile.displayName.characters.first.toUpperCase(),
                style: Theme.of(context).textTheme.headlineMedium,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    profile.displayName,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 3),
                  Text(
                    profile.email,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
          ],
        ),
        if (profile.studentStatusVerified) ...[
          const SizedBox(height: 14),
          _VerificationSuccess(message: '${profile.verifiedUniversity}學生身分已驗證'),
        ],
        const SizedBox(height: 26),
        const ExchangeSectionHeader(title: '個人設定'),
        const SizedBox(height: 14),
        GlassCard(
          child: Column(
            children: [
              TextField(
                controller: displayNameController,
                decoration: const InputDecoration(
                  labelText: '公開暱稱',
                  prefixIcon: Icon(Icons.badge_outlined),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: homeUniversityController,
                decoration: const InputDecoration(
                  labelText: '目前就讀大學',
                  prefixIcon: Icon(Icons.school_outlined),
                ),
              ),
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerLeft,
                child: Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: store.universities
                      .map(
                        (university) => ActionChip(
                          label: Text(university.shortName),
                          onPressed: () {
                            setState(() {
                              homeUniversityController.text =
                                  university.schoolName;
                            });
                          },
                        ),
                      )
                      .toList(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: targetCountriesController,
                decoration: const InputDecoration(
                  labelText: '目標國家',
                  helperText: '例如：日本、法國、澳洲',
                  prefixIcon: Icon(Icons.public_rounded),
                ),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: applicationStage,
                decoration: const InputDecoration(
                  labelText: '目前申請階段',
                  prefixIcon: Icon(Icons.route_outlined),
                ),
                items: _stageLabels.entries
                    .map(
                      (entry) => DropdownMenuItem(
                        value: entry.key,
                        child: Text(entry.value),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  if (value != null) setState(() => applicationStage = value);
                },
              ),
              if (error != null) ...[
                const SizedBox(height: 12),
                _FormError(message: error!),
              ],
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: () => _saveProfile(store),
                  icon: const Icon(Icons.save_outlined),
                  label: const Text('儲存設定'),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: () {
            profileInitialized = false;
            store.logout();
          },
          icon: const Icon(Icons.logout_rounded),
          label: const Text('登出'),
        ),
        const SizedBox(height: 8),
        TextButton.icon(
          style: TextButton.styleFrom(foregroundColor: ExchangeColors.danger),
          onPressed: () async {
            final confirmed = await showDialog<bool>(
              context: context,
              builder: (dialogContext) => AlertDialog(
                title: const Text('刪除帳號？'),
                content: const Text('帳號、收藏與社群身分會永久刪除，這個動作無法復原。'),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.of(dialogContext).pop(false),
                    child: const Text('取消'),
                  ),
                  FilledButton(
                    style: FilledButton.styleFrom(
                      backgroundColor: ExchangeColors.danger,
                    ),
                    onPressed: () => Navigator.of(dialogContext).pop(true),
                    child: const Text('刪除'),
                  ),
                ],
              ),
            );
            if (confirmed == true) {
              profileInitialized = false;
              await store.deleteAccount();
            }
          },
          icon: const Icon(Icons.delete_outline_rounded),
          label: const Text('刪除帳號'),
        ),
      ],
    );
  }

  Future<void> _providerLogin(ExchangeStore store, String provider) async {
    if (!termsAccepted) {
      setState(() => error = '請先閱讀並同意服務條款與隱私權政策。');
      return;
    }
    setState(() => error = null);
    try {
      await store.startMobileLogin(provider);
    } catch (exception) {
      if (mounted) setState(() => error = exception.toString());
    }
  }

  Widget _buildGoogleAuth(BuildContext context, ExchangeStore store) {
    final google = store.authProviders
        .where((p) => p.provider == 'google' && p.enabled)
        .firstOrNull;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 28),
        const ExchangeIconBadge(Icons.flight_takeoff_rounded),
        const SizedBox(height: 28),
        Text(
          '同一個你，\n同一份交換計畫。',
          style: Theme.of(context).textTheme.displaySmall?.copyWith(
            fontWeight: FontWeight.w800,
            height: 1.25,
          ),
        ),
        const SizedBox(height: 16),
        const Text('使用電腦版相同的 Google 帳號。你的收藏、文件進度與申請日期，會接著同步到這裡。'),
        const SizedBox(height: 28),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                value: termsAccepted,
                onChanged: (value) =>
                    setState(() => termsAccepted = value ?? false),
                title: const Text('我已閱讀並同意服務條款與隱私權政策'),
              ),
              Wrap(
                spacing: 8,
                children: [
                  TextButton(
                    onPressed: () => launchUrl(
                      Uri.parse(store.api.resolveUrl('terms')),
                      mode: LaunchMode.externalApplication,
                    ),
                    child: const Text('服務條款'),
                  ),
                  TextButton(
                    onPressed: () => launchUrl(
                      Uri.parse(store.api.resolveUrl('privacy')),
                      mode: LaunchMode.externalApplication,
                    ),
                    child: const Text('隱私權政策'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: google == null || store.isAuthenticating
                    ? null
                    : () => _providerLogin(store, 'google'),
                icon: const Icon(Icons.g_mobiledata_rounded),
                label: Text(store.isAuthenticating ? '正在登入…' : '使用 Google 繼續'),
              ),
              const SizedBox(height: 12),
              Text(
                '會開啟瀏覽器完成登入，再返回 UniWay。',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              if (google == null)
                TextButton(
                  onPressed: store.refresh,
                  child: const Text('重新取得登入方式'),
                ),
              if (error != null || store.mobileLoginError != null)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: _FormError(message: error ?? store.mobileLoginError!),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class _StudentVerificationCard extends StatelessWidget {
  const _StudentVerificationCard({
    required this.frontCard,
    required this.backCard,
    required this.consent,
    required this.isLoading,
    required this.error,
    required this.onPickFront,
    required this.onPickBack,
    required this.onConsentChanged,
    required this.onVerify,
  });

  final XFile? frontCard;
  final XFile? backCard;
  final bool consent;
  final bool isLoading;
  final String? error;
  final VoidCallback onPickFront;
  final VoidCallback onPickBack;
  final ValueChanged<bool?> onConsentChanged;
  final VoidCallback onVerify;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const ExchangeIconBadge(Icons.verified_user_outlined),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '驗證在學身分',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    Text(
                      '正反面只用於本次辨識',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _StudentCardPicker(
            title: '學生證正面',
            hint: '校名、姓名與學號需清楚',
            image: frontCard,
            icon: Icons.center_focus_strong_rounded,
            onTap: onPickFront,
          ),
          const SizedBox(height: 10),
          _StudentCardPicker(
            title: '學生證反面',
            hint: '完整拍攝，不裁切卡片邊緣',
            image: backCard,
            icon: Icons.credit_card_rounded,
            onTap: onPickBack,
          ),
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: ExchangeColors.tealSoft.withValues(alpha: .58),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.shield_outlined,
                  size: 20,
                  color: ExchangeColors.success,
                ),
                SizedBox(width: 9),
                Expanded(child: Text('不保存證件照片、姓名、學號或 OCR 全文；只留下已驗證、學校與時間。')),
              ],
            ),
          ),
          const SizedBox(height: 10),
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            value: consent,
            onChanged: onConsentChanged,
            title: const Text('我同意系統進行一次性學生身分辨識。'),
          ),
          if (error != null) ...[
            const SizedBox(height: 8),
            _FormError(message: error!),
          ],
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: isLoading ? null : onVerify,
              icon: isLoading
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.document_scanner_outlined),
              label: Text(isLoading ? '安全辨識中…' : '開始安全驗證'),
            ),
          ),
        ],
      ),
    );
  }
}

class _StudentCardPicker extends StatelessWidget {
  const _StudentCardPicker({
    required this.title,
    required this.hint,
    required this.image,
    required this.icon,
    required this.onTap,
  });

  final String title;
  final String hint;
  final XFile? image;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: '$title，$hint',
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Ink(
          height: 142,
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: .5),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: image == null
                  ? ExchangeColors.blue.withValues(alpha: .42)
                  : ExchangeColors.success.withValues(alpha: .5),
              style: BorderStyle.solid,
            ),
            image: image == null
                ? null
                : DecorationImage(
                    image: FileImage(File(image!.path)),
                    fit: BoxFit.cover,
                    colorFilter: ColorFilter.mode(
                      Colors.black.withValues(alpha: .2),
                      BlendMode.darken,
                    ),
                  ),
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  image == null ? icon : Icons.check_circle_rounded,
                  color: image == null ? ExchangeColors.blue : Colors.white,
                  size: 30,
                ),
                const SizedBox(height: 8),
                Text(
                  image == null ? title : '已加入 $title',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: image == null ? ExchangeColors.ink : Colors.white,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  image == null ? hint : '點一下可重新選擇',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: image == null
                        ? ExchangeColors.secondaryInk
                        : Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _VerificationSuccess extends StatelessWidget {
  const _VerificationSuccess({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFE5F4EC),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: ExchangeColors.success.withValues(alpha: .22),
        ),
      ),
      child: Row(
        children: [
          const Icon(Icons.verified_rounded, color: ExchangeColors.success),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '建立你的交換檔案',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Text('$message · 請在 15 分鐘內完成註冊'),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ProviderButton extends StatelessWidget {
  const _ProviderButton({required this.provider, required this.onLogin});

  final AuthProviderStatus provider;
  final VoidCallback onLogin;

  @override
  Widget build(BuildContext context) {
    final icon = switch (provider.provider) {
      'google' => Icons.g_mobiledata_rounded,
      'facebook' => Icons.facebook_rounded,
      _ => Icons.apple_rounded,
    };
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: provider.enabled ? onLogin : null,
        icon: Icon(icon),
        label: Text(
          provider.enabled ? provider.label : '${provider.label} · 尚未設定',
        ),
      ),
    );
  }
}

class _FormError extends StatelessWidget {
  const _FormError({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: ExchangeColors.coralSoft,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        message,
        style: const TextStyle(
          color: ExchangeColors.danger,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

const _stageLabels = {
  'exploring': '尋找學校',
  'eligibility': '確認資格',
  'documents': '準備文件',
  'submitted': '已送出申請',
  'accepted': '已錄取',
  'abroad': '正在海外',
  'returned': '已返國',
};
