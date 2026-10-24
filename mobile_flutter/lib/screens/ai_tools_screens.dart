import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/application_calendar.dart';
import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
import '../data/exchange_api.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import 'feature_screens.dart' show FeaturePageScaffold;
import 'school_detail_screen.dart';

class AdvisorScreen extends StatefulWidget {
  const AdvisorScreen({super.key});

  @override
  State<AdvisorScreen> createState() => _AdvisorScreenState();
}

class _AdvisorScreenState extends State<AdvisorScreen> {
  final academicScoreController = TextEditingController();
  final languageScoreController = TextEditingController();
  final budgetController = TextEditingController();
  final departmentController = TextEditingController();
  final questionController = TextEditingController(text: '交換申請需要先準備哪些資料？');

  String college = '';
  String degreeLevel = '';
  String currentYear = '';
  String languageTest = '';
  String targetTerm = '';
  String preferredCountry = '';
  bool needsScholarship = false;
  bool isLoading = false;
  bool showAllSchools = false;
  AdvisorPlan? plan;
  String? error;

  @override
  void dispose() {
    academicScoreController.dispose();
    languageScoreController.dispose();
    budgetController.dispose();
    departmentController.dispose();
    questionController.dispose();
    super.dispose();
  }

  AdvisorProfile _profile() => AdvisorProfile(
    schoolName: ExchangeStoreScope.of(
      context,
      listen: false,
    ).selectedUniversity,
    college: college,
    department: departmentController.text.trim(),
    currentYear: currentYear,
    degreeLevel: degreeLevel,
    academicScore: double.tryParse(academicScoreController.text.trim()),
    languageTest: languageTest,
    languageScore: double.tryParse(languageScoreController.text.trim()),
    targetTerm: targetTerm,
    preferredCountry: preferredCountry,
    monthlyBudget: double.tryParse(budgetController.text.trim()),
    needsScholarship: needsScholarship,
    question: questionController.text.trim(),
  );

  Future<void> _generate() async {
    FocusScope.of(context).unfocus();
    final api = ExchangeStoreScope.of(context, listen: false).api;
    setState(() {
      isLoading = true;
      error = null;
    });
    try {
      final result = await api.advisorPlan(_profile());
      if (!mounted) return;
      setState(() {
        plan = result;
        showAllSchools = false;
      });
    } catch (exception) {
      if (!mounted) return;
      setState(() => error = _errorText(exception));
    } finally {
      if (mounted) setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final colleges = store.activeUniversity.colleges.isNotEmpty
        ? store.activeUniversity.colleges
        : const ['工學院', '智慧運算學院', '管理學院', '醫學院'];
    final countries = {
      ...?store.dashboard?.partnerUniversities.map((school) => school.country),
    }.where((value) => value.isNotEmpty).toList()..sort();

    return FeaturePageScaffold(
      title: '申請顧問',
      bottomBar: StudentActionBar(
        primary: FilledButton.icon(
          onPressed: isLoading ? null : _generate,
          icon: isLoading
              ? const SizedBox.square(
                  dimension: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : const Icon(Icons.auto_awesome_rounded),
          label: Text(isLoading ? '整理中…' : '產生申請方案'),
        ),
      ),
      children: [
        const _ToolHero(
          asset: 'assets/images/destination-tokyo.jpg',
          eyebrow: '依官方資料規劃',
          title: '申請顧問',
          subtitle: '條件、選校與下一步一次整理。',
          icon: Icons.auto_awesome_rounded,
        ),
        const SizedBox(height: 16),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _SectionTitle(
                icon: Icons.tune_rounded,
                title: '我的條件',
                trailing: Text(
                  '未填也能查',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
              const SizedBox(height: 16),
              _TwoColumnFields(
                children: [
                  _DropdownField(
                    label: '學院',
                    value: colleges.contains(college) ? college : '',
                    options: colleges,
                    onChanged: (value) => setState(() => college = value),
                  ),
                  _DropdownField(
                    label: '學制',
                    value: degreeLevel,
                    options: const ['大學部', '研究所'],
                    onChanged: (value) => setState(() => degreeLevel = value),
                  ),
                  _NumberField(
                    controller: academicScoreController,
                    label: '學業平均',
                    hintText: '例如 82',
                  ),
                  _DropdownField(
                    label: '語言測驗',
                    value: languageTest,
                    options: const [
                      'toeic',
                      'ielts',
                      'toefl',
                      'duolingo',
                      'other',
                    ],
                    labels: const {
                      'toeic': 'TOEIC',
                      'ielts': 'IELTS',
                      'toefl': 'TOEFL iBT',
                      'duolingo': 'Duolingo',
                      'other': '其他',
                    },
                    onChanged: (value) => setState(() => languageTest = value),
                  ),
                  _NumberField(
                    controller: languageScoreController,
                    label: '語言分數',
                    hintText: '依測驗填寫',
                  ),
                  _DropdownField(
                    label: '優先國家',
                    value: preferredCountry,
                    options: countries,
                    onChanged: (value) =>
                        setState(() => preferredCountry = value),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              ExpansionTile(
                tilePadding: EdgeInsets.zero,
                childrenPadding: const EdgeInsets.only(bottom: 8),
                shape: const Border(),
                collapsedShape: const Border(),
                title: const Text('更多條件'),
                leading: const Icon(Icons.tune_rounded),
                children: [
                  _TwoColumnFields(
                    children: [
                      TextField(
                        controller: departmentController,
                        decoration: const InputDecoration(
                          labelText: '科系／領域',
                          hintText: '例如人工智慧',
                        ),
                      ),
                      _DropdownField(
                        label: '目前年級',
                        value: currentYear,
                        options: const ['大一', '大二', '大三', '大四', '碩士班', '博士班'],
                        onChanged: (value) =>
                            setState(() => currentYear = value),
                      ),
                      _DropdownField(
                        label: '預計學期',
                        value: targetTerm,
                        options: const [
                          '2027 春季',
                          '2027 秋季',
                          '2028 春季',
                          '2028 秋季',
                        ],
                        onChanged: (value) =>
                            setState(() => targetTerm = value),
                      ),
                      _NumberField(
                        controller: budgetController,
                        label: '每月預算',
                        hintText: '新台幣',
                      ),
                    ],
                  ),
                  SwitchListTile.adaptive(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('需要獎學金'),
                    value: needsScholarship,
                    onChanged: (value) =>
                        setState(() => needsScholarship = value),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              TextField(
                controller: questionController,
                minLines: 2,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: '想問什麼？',
                  hintText: '例如：申請日本交換需要哪些文件？',
                ),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _QuestionChip(
                    label: '必要文件',
                    onTap: () => setState(
                      () => questionController.text = '交換申請需要準備哪些文件？',
                    ),
                  ),
                  _QuestionChip(
                    label: '語言門檻',
                    onTap: () => setState(
                      () => questionController.text = '交換學校的語言門檻怎麼比較？',
                    ),
                  ),
                  _QuestionChip(
                    label: '補助',
                    onTap: () => setState(
                      () => questionController.text = '我可以申請哪些出國補助？',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              const SizedBox(height: 8),
              Text(
                '只依已查核來源整理；符合度不是錄取機率。',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
        if (error != null) ...[
          const SizedBox(height: 12),
          InlineError(message: error!, onRetry: _generate),
        ],
        if (plan != null) ...[
          const SizedBox(height: 20),
          _AdvisorResultHeader(plan: plan!),
          if (plan!.answer != null) ...[
            const SizedBox(height: 12),
            _AdvisorAnswerCard(answer: plan!.answer!),
          ],
          if (plan!.recommendations.isNotEmpty) ...[
            const SizedBox(height: 24),
            ExchangeSectionHeader(
              eyebrow: '公開條件排序',
              title: '優先候選',
              action: Text('${plan!.recommendations.length} 所'),
            ),
            const SizedBox(height: 8),
            ...plan!.recommendations
                .take(showAllSchools ? plan!.recommendations.length : 5)
                .map(
                  (match) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: _AdvisorSchoolCard(match: match, store: store),
                  ),
                ),
            if (plan!.recommendations.length > 5)
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () =>
                      setState(() => showAllSchools = !showAllSchools),
                  icon: Icon(
                    showAllSchools
                        ? Icons.expand_less_rounded
                        : Icons.expand_more_rounded,
                  ),
                  label: Text(showAllSchools ? '收起候選' : '查看全部候選'),
                ),
              ),
          ],
          if (plan!.tasks.isNotEmpty) ...[
            const SizedBox(height: 24),
            const StudentSectionTitle('下一步', icon: Icons.checklist_rounded),
            const SizedBox(height: 8),
            ...plan!.tasks.map(
              (task) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _AdvisorTaskCard(task: task, store: store),
              ),
            ),
          ],
          const SizedBox(height: 12),
          Text(plan!.disclaimer, style: Theme.of(context).textTheme.bodySmall),
        ],
      ],
    );
  }
}

class DocumentCheckScreen extends StatefulWidget {
  const DocumentCheckScreen({super.key});

  @override
  State<DocumentCheckScreen> createState() => _DocumentCheckScreenState();
}

class _DocumentCheckScreenState extends State<DocumentCheckScreen> {
  final wordLimitController = TextEditingController();
  XFile? selectedFile;
  String documentType = 'auto';
  bool requireSignature = false;
  bool useAi = false;
  bool isLoading = false;
  DocumentCheckResult? result;
  String? error;

  @override
  void dispose() {
    wordLimitController.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final file = await openFile(
      acceptedTypeGroups: const [
        XTypeGroup(label: '申請文件', extensions: ['pdf', 'docx', 'txt']),
      ],
    );
    if (file == null || !mounted) return;
    setState(() {
      selectedFile = file;
      result = null;
      error = null;
    });
  }

  Future<void> _check() async {
    final file = selectedFile;
    if (file == null) {
      setState(() => error = '請先選擇 PDF、DOCX 或 TXT 文件。');
      return;
    }
    FocusScope.of(context).unfocus();
    final api = ExchangeStoreScope.of(context, listen: false).api;
    setState(() {
      isLoading = true;
      error = null;
    });
    try {
      final bytes = await file.readAsBytes();
      final checked = await api.reviewDocument(
        fileName: file.name,
        bytes: Uint8List.fromList(bytes),
        documentType: documentType,
        expectedWordLimit: int.tryParse(wordLimitController.text.trim()),
        requireSignature: requireSignature,
        useAi: useAi,
      );
      if (!mounted) return;
      setState(() => result = checked);
    } catch (exception) {
      if (!mounted) return;
      setState(() => error = _errorText(exception));
    } finally {
      if (mounted) setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FeaturePageScaffold(
      title: '文件檢查',
      bottomBar: StudentActionBar(
        primary: FilledButton.icon(
          onPressed: isLoading ? null : _check,
          icon: isLoading
              ? const SizedBox.square(
                  dimension: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : const Icon(Icons.fact_check_outlined),
          label: Text(isLoading ? '檢查中…' : '開始檢查'),
        ),
      ),
      children: [
        const _ToolHero(
          asset: 'assets/images/destination-sydney.jpg',
          eyebrow: '送出前再確認',
          title: '文件檢查',
          subtitle: '漏填、字數與簽名位置集中檢查。',
          icon: Icons.fact_check_outlined,
        ),
        const SizedBox(height: 16),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _SectionTitle(
                icon: Icons.upload_file_rounded,
                title: '選擇文件',
                trailing: selectedFile == null
                    ? null
                    : const Icon(
                        Icons.check_circle_rounded,
                        color: ExchangeColors.success,
                      ),
              ),
              const SizedBox(height: 16),
              InkWell(
                borderRadius: BorderRadius.circular(16),
                onTap: isLoading ? null : _pickFile,
                child: Container(
                  constraints: const BoxConstraints(minHeight: 72),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: .56),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: ExchangeColors.line),
                  ),
                  child: Row(
                    children: [
                      const ExchangeIconBadge(Icons.description_outlined),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          selectedFile?.name ?? 'PDF、DOCX 或 TXT',
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
                      TextButton(
                        onPressed: isLoading ? null : _pickFile,
                        child: Text(selectedFile == null ? '選擇' : '更換'),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              _TwoColumnFields(
                children: [
                  _DropdownField(
                    label: '文件類型',
                    value: documentType,
                    includeEmpty: false,
                    options: const [
                      'auto',
                      'study_plan',
                      'cv',
                      'recommendation',
                      'other',
                    ],
                    labels: const {
                      'auto': '自動判斷',
                      'study_plan': '讀書計畫',
                      'cv': '履歷',
                      'recommendation': '推薦信',
                      'other': '其他',
                    },
                    onChanged: (value) => setState(() => documentType = value),
                  ),
                  TextField(
                    controller: wordLimitController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: '字數上限',
                      hintText: '選填',
                    ),
                  ),
                ],
              ),
              SwitchListTile.adaptive(
                contentPadding: EdgeInsets.zero,
                title: const Text('檢查簽名位置'),
                value: requireSignature,
                onChanged: (value) => setState(() => requireSignature = value),
              ),
              SwitchListTile.adaptive(
                contentPadding: EdgeInsets.zero,
                title: const Text('AI 深度檢查'),
                subtitle: const Text('只傳抽取文字，不傳原檔'),
                value: useAi,
                onChanged: (value) => setState(() => useAi = value),
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
        if (error != null) ...[
          const SizedBox(height: 12),
          InlineError(message: error!, onRetry: _check),
        ],
        if (result != null) ...[
          const SizedBox(height: 20),
          _DocumentCheckResultCard(result: result!),
        ],
      ],
    );
  }
}

class WritingAssistantScreen extends StatefulWidget {
  const WritingAssistantScreen({super.key});

  @override
  State<WritingAssistantScreen> createState() => _WritingAssistantScreenState();
}

class _WritingAssistantScreenState extends State<WritingAssistantScreen> {
  final textController = TextEditingController();
  final wordLimitController = TextEditingController();
  final schoolContextController = TextEditingController();
  String action = 'formalize';
  String documentType = 'study_plan';
  bool isLoading = false;
  DocumentRewriteResult? result;
  String? error;

  @override
  void dispose() {
    textController.dispose();
    wordLimitController.dispose();
    schoolContextController.dispose();
    super.dispose();
  }

  Future<void> _rewrite() async {
    final text = textController.text.trim();
    if (text.length < 20) {
      setState(() => error = '請至少輸入 20 個字。');
      return;
    }
    FocusScope.of(context).unfocus();
    setState(() {
      isLoading = true;
      error = null;
    });
    try {
      final rewritten = await ExchangeStoreScope.of(context, listen: false).api
          .rewriteDocument(
            text: text,
            action: action,
            documentType: documentType,
            targetWordLimit: int.tryParse(wordLimitController.text.trim()),
            schoolContext: schoolContextController.text,
          );
      if (!mounted) return;
      setState(() => result = rewritten);
    } catch (exception) {
      if (!mounted) return;
      setState(() => error = _errorText(exception));
    } finally {
      if (mounted) setState(() => isLoading = false);
    }
  }

  Future<void> _copyDraft() async {
    final draft = result?.draft ?? '';
    if (draft.isEmpty) return;
    await Clipboard.setData(ClipboardData(text: draft));
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('已複製建議稿')));
  }

  @override
  Widget build(BuildContext context) {
    return FeaturePageScaffold(
      title: '文件改寫',
      bottomBar: StudentActionBar(
        primary: FilledButton.icon(
          onPressed: isLoading ? null : _rewrite,
          icon: isLoading
              ? const SizedBox.square(
                  dimension: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : const Icon(Icons.auto_fix_high_rounded),
          label: Text(isLoading ? '整理中…' : '產生建議稿'),
        ),
      ),
      children: [
        const _ToolHero(
          asset: 'assets/images/destination-europe.jpg',
          eyebrow: '保留事實再調整',
          title: '文件改寫',
          subtitle: '正式化、翻譯或精簡你的原文。',
          icon: Icons.auto_fix_high_rounded,
        ),
        const SizedBox(height: 16),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _SectionTitle(icon: Icons.edit_note_rounded, title: '學生原文'),
              const SizedBox(height: 16),
              TextField(
                controller: textController,
                minLines: 7,
                maxLines: 12,
                maxLength: 16000,
                decoration: const InputDecoration(
                  hintText: '貼上你自己撰寫的內容',
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 8),
              _TwoColumnFields(
                children: [
                  _DropdownField(
                    label: '調整方式',
                    value: action,
                    includeEmpty: false,
                    options: const [
                      'formalize',
                      'translate_en',
                      'shorten',
                      'grammar',
                    ],
                    labels: const {
                      'formalize': '正式語氣',
                      'translate_en': '翻成英文',
                      'shorten': '壓縮字數',
                      'grammar': '文法與用字',
                    },
                    onChanged: (value) => setState(() => action = value),
                  ),
                  _DropdownField(
                    label: '文件類型',
                    value: documentType,
                    includeEmpty: false,
                    options: const [
                      'study_plan',
                      'motivation',
                      'resume',
                      'email',
                      'other',
                    ],
                    labels: const {
                      'study_plan': '讀書計畫',
                      'motivation': '申請動機',
                      'resume': '履歷',
                      'email': 'Email',
                      'other': '其他',
                    },
                    onChanged: (value) => setState(() => documentType = value),
                  ),
                  TextField(
                    controller: wordLimitController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: '目標字數',
                      hintText: '選填',
                    ),
                  ),
                  TextField(
                    controller: schoolContextController,
                    decoration: const InputDecoration(
                      labelText: '目標學校／課程',
                      hintText: '選填',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              const SizedBox(height: 8),
              Text(
                '不保存原文；請先移除不必要的個資。',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
        if (error != null) ...[
          const SizedBox(height: 12),
          InlineError(message: error!, onRetry: _rewrite),
        ],
        if (result != null) ...[
          const SizedBox(height: 20),
          _RewriteResultCard(result: result!, onCopy: _copyDraft),
        ],
      ],
    );
  }
}

class _ToolHero extends StatelessWidget {
  const _ToolHero({
    required this.asset,
    required this.eyebrow,
    required this.title,
    required this.subtitle,
    required this.icon,
  });

  final String asset;
  final String eyebrow;
  final String title;
  final String subtitle;
  final IconData icon;

  @override
  Widget build(BuildContext context) => StudentNotice(subtitle, icon: icon);
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.icon, required this.title, this.trailing});

  final IconData icon;
  final String title;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: ExchangeColors.teal, size: 21),
        const SizedBox(width: 8),
        Expanded(
          child: Text(title, style: Theme.of(context).textTheme.titleMedium),
        ),
        ?trailing,
      ],
    );
  }
}

class _TwoColumnFields extends StatelessWidget {
  const _TwoColumnFields({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 620 ? 2 : 1;
        const gap = 10.0;
        final width = (constraints.maxWidth - gap * (columns - 1)) / columns;
        return Wrap(
          spacing: gap,
          runSpacing: 10,
          children: children
              .map((child) => SizedBox(width: width, child: child))
              .toList(),
        );
      },
    );
  }
}

class _DropdownField extends StatelessWidget {
  const _DropdownField({
    required this.label,
    required this.value,
    required this.options,
    required this.onChanged,
    this.labels = const {},
    this.includeEmpty = true,
  });

  final String label;
  final String value;
  final List<String> options;
  final ValueChanged<String> onChanged;
  final Map<String, String> labels;
  final bool includeEmpty;

  @override
  Widget build(BuildContext context) {
    final values = [if (includeEmpty) '', ...options];
    final safeValue = values.contains(value) ? value : values.first;
    return DropdownButtonFormField<String>(
      initialValue: safeValue,
      isExpanded: true,
      decoration: InputDecoration(labelText: label),
      items: values
          .map(
            (item) => DropdownMenuItem(
              value: item,
              child: Text(
                item.isEmpty ? '尚未設定' : labels[item] ?? item,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          )
          .toList(),
      onChanged: (item) => onChanged(item ?? ''),
    );
  }
}

class _NumberField extends StatelessWidget {
  const _NumberField({
    required this.controller,
    required this.label,
    required this.hintText,
  });

  final TextEditingController controller;
  final String label;
  final String hintText;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(labelText: label, hintText: hintText),
    );
  }
}

class _QuestionChip extends StatelessWidget {
  const _QuestionChip({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ActionChip(
      avatar: const Icon(Icons.add_rounded, size: 17),
      label: Text(label),
      onPressed: onTap,
    );
  }
}

class _AdvisorResultHeader extends StatelessWidget {
  const _AdvisorResultHeader({required this.plan});

  final AdvisorPlan plan;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      tint: ExchangeColors.tealSoft,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _SectionTitle(
            icon: Icons.verified_outlined,
            title: '系統資格比對',
            trailing: Container(
              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: .72),
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(
                plan.mode == 'ai_enhanced' ? 'AI 整理' : '規則整理',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(plan.summary, style: Theme.of(context).textTheme.titleMedium),
          if (plan.qualification.isNotEmpty) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 7,
              runSpacing: 7,
              children: plan.qualification
                  .map(
                    (item) => Chip(
                      avatar: const Icon(Icons.check_rounded, size: 16),
                      label: Text(item),
                    ),
                  )
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }
}

class _AdvisorAnswerCard extends StatelessWidget {
  const _AdvisorAnswerCard({required this.answer});

  final AdvisorAnswer answer;

  @override
  Widget build(BuildContext context) {
    final statusLabel = switch (answer.evidenceStatus) {
      'grounded' => '來源完整',
      'limited' => '資料有限',
      _ => '尚無來源',
    };
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _SectionTitle(
            icon: Icons.travel_explore_rounded,
            title: '官方資料回答',
            trailing: Text(
              statusLabel,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: answer.evidenceStatus == 'grounded'
                    ? ExchangeColors.success
                    : ExchangeColors.amber,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(answer.question, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(answer.answer),
          if (answer.keyPoints.isNotEmpty) ...[
            const SizedBox(height: 12),
            ...answer.keyPoints.map(BulletPoint.new),
          ],
          if (answer.sources.isNotEmpty)
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              childrenPadding: EdgeInsets.zero,
              shape: const Border(),
              collapsedShape: const Border(),
              title: Text('官方來源 ${answer.sources.length}'),
              leading: const Icon(Icons.source_outlined),
              children: answer.sources
                  .map(
                    (source) => ListTile(
                      contentPadding: EdgeInsets.zero,
                      minTileHeight: 56,
                      title: Text(source.title),
                      subtitle: Text(
                        [
                          if (source.section.isNotEmpty) source.section,
                          if (source.publishedAt.isNotEmpty)
                            '發布：${source.publishedAt}',
                          if (source.lastChecked.isNotEmpty)
                            '查核：${_dateOnlyText(source.lastChecked)}',
                        ].join(' · '),
                      ),
                      trailing: const Icon(Icons.open_in_new_rounded),
                      onTap: source.sourceUrl.isEmpty
                          ? null
                          : () => _openUrl(source.sourceUrl),
                    ),
                  )
                  .toList(),
            ),
        ],
      ),
    );
  }
}

class _AdvisorSchoolCard extends StatelessWidget {
  const _AdvisorSchoolCard({required this.match, required this.store});

  final AdvisorSchoolMatch match;
  final ExchangeStore store;

  @override
  Widget build(BuildContext context) {
    final school = store.dashboard?.partnerUniversities
        .where((item) => item.schoolName == match.schoolName)
        .firstOrNull;
    final imageUrl = match.imageUrl.isNotEmpty
        ? match.imageUrl
        : school?.imageUrl ?? '';
    return GlassCard(
      padding: EdgeInsets.zero,
      child: ExpansionTile(
        minTileHeight: 88,
        tilePadding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
        childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
        shape: const Border(),
        collapsedShape: const Border(),
        leading: ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: SizedBox.square(
            dimension: 64,
            child: imageUrl.isEmpty
                ? const ColoredBox(
                    color: ExchangeColors.blueSoft,
                    child: Icon(
                      Icons.school_outlined,
                      color: ExchangeColors.blue,
                    ),
                  )
                : Image.network(
                    imageUrl,
                    fit: BoxFit.cover,
                    errorBuilder: (_, _, _) => const ColoredBox(
                      color: ExchangeColors.blueSoft,
                      child: Icon(
                        Icons.school_outlined,
                        color: ExchangeColors.blue,
                      ),
                    ),
                  ),
          ),
        ),
        title: Text(
          match.schoolName,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Text(
          [
            match.country,
            match.fitLabel,
          ].where((value) => value.isNotEmpty).join(' · '),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: SizedBox(
          width: 48,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                '${match.matchScore}',
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(color: ExchangeColors.blue),
              ),
              Text('符合度', style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
        ),
        children: [
          if (match.reasons.isNotEmpty) ...[
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                '符合條件',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
            const SizedBox(height: 8),
            ...match.reasons.map(BulletPoint.new),
          ],
          if (match.gaps.isNotEmpty) ...[
            const SizedBox(height: 4),
            const Align(
              alignment: Alignment.centerLeft,
              child: Text('待確認', style: TextStyle(fontWeight: FontWeight.w600)),
            ),
            const SizedBox(height: 8),
            ...match.gaps.map(BulletPoint.new),
          ],
          if (school != null)
            Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton.icon(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => SchoolDetailScreen(school: school),
                  ),
                ),
                icon: const Icon(Icons.arrow_forward_rounded),
                label: const Text('查看學校'),
              ),
            ),
        ],
      ),
    );
  }
}

class _AdvisorTaskCard extends StatefulWidget {
  const _AdvisorTaskCard({required this.task, required this.store});

  final AdvisorTask task;
  final ExchangeStore store;

  @override
  State<_AdvisorTaskCard> createState() => _AdvisorTaskCardState();
}

class _AdvisorTaskCardState extends State<_AdvisorTaskCard> {
  bool isAdding = false;

  Future<void> _addToCalendar() async {
    var date = parseDateKey(widget.task.dueDate);
    date ??= await showDatePicker(
      context: context,
      initialDate: DateTime.now().add(const Duration(days: 7)),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 730)),
      helpText: '選擇提醒日期',
    );
    if (date == null || !mounted) return;
    setState(() => isAdding = true);
    final event = ApplicationCalendarEvent(
      id: 'advisor-${widget.task.id}',
      title: widget.task.title,
      date: date,
      category: widget.task.category,
      reminderDays: 7,
      note: widget.task.detail,
      sourceUrl: widget.task.sourceUrl,
      isOfficial: false,
    );
    final synced = await widget.store.addCalendarEvent(event);
    if (!mounted) return;
    setState(() => isAdding = false);
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(synced ? '已加入並同步日曆' : '已加入申請日曆')));
  }

  @override
  Widget build(BuildContext context) {
    final eventId = 'advisor-${widget.task.id}';
    final added = widget.store.applicationCalendarEvents.any(
      (event) => event.id == eventId,
    );
    final accent = widget.task.priority == 'high'
        ? ExchangeColors.coral
        : ExchangeColors.blue;
    return GlassCard(
      padding: const EdgeInsets.all(14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ExchangeIconBadge(
            widget.task.dueDate.isEmpty
                ? Icons.task_alt_rounded
                : Icons.schedule_rounded,
            color: accent,
            background: accent.withValues(alpha: .11),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.task.title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 4),
                Text(
                  widget.task.detail,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          IconButton(
            tooltip: added ? '已加入日曆' : '加入日曆',
            onPressed: added || isAdding ? null : _addToCalendar,
            icon: isAdding
                ? const SizedBox.square(
                    dimension: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Icon(
                    added
                        ? Icons.event_available_rounded
                        : Icons.event_outlined,
                  ),
          ),
        ],
      ),
    );
  }
}

class _DocumentCheckResultCard extends StatelessWidget {
  const _DocumentCheckResultCard({required this.result});

  final DocumentCheckResult result;

  @override
  Widget build(BuildContext context) {
    final scoreColor = result.completenessScore >= 80
        ? ExchangeColors.success
        : result.completenessScore >= 60
        ? ExchangeColors.amber
        : ExchangeColors.coral;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ExchangeSectionHeader(
          eyebrow: result.aiEnhanced ? 'AI 深度檢查' : '系統基本檢查',
          title: '檢查結果',
        ),
        const SizedBox(height: 8),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  SizedBox.square(
                    dimension: 72,
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        CircularProgressIndicator(
                          value: result.completenessScore / 100,
                          strokeWidth: 7,
                          strokeCap: StrokeCap.round,
                          color: scoreColor,
                          backgroundColor: ExchangeColors.line,
                        ),
                        Text(
                          '${result.completenessScore}',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          result.fileName,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${result.pageCount} 頁 · ${result.wordCount} 字',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Text(result.summary),
            ],
          ),
        ),
        if (result.issues.isNotEmpty) ...[
          const SizedBox(height: 8),
          GlassCard(
            padding: EdgeInsets.zero,
            child: ExpansionTile(
              initiallyExpanded: true,
              minTileHeight: 64,
              shape: const Border(),
              collapsedShape: const Border(),
              leading: const ExchangeIconBadge(
                Icons.warning_amber_rounded,
                color: ExchangeColors.amber,
                background: ExchangeColors.amberSoft,
              ),
              title: Text('待確認 ${result.issues.length} 項'),
              childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
              children: result.issues
                  .map((issue) => _IssueRow(issue: issue))
                  .toList(),
            ),
          ),
        ],
        if (result.suggestions.isNotEmpty ||
            result.checksPassed.isNotEmpty) ...[
          const SizedBox(height: 8),
          GlassCard(
            padding: EdgeInsets.zero,
            child: ExpansionTile(
              minTileHeight: 64,
              shape: const Border(),
              collapsedShape: const Border(),
              leading: const ExchangeIconBadge(Icons.checklist_rounded),
              title: const Text('完整檢查內容'),
              childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
              children: [
                ...result.suggestions.map(BulletPoint.new),
                ...result.checksPassed.map(
                  (item) => ListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(
                      Icons.check_circle_outline_rounded,
                      color: ExchangeColors.success,
                    ),
                    title: Text(item),
                  ),
                ),
              ],
            ),
          ),
        ],
        if (result.extractedPreview.isNotEmpty) ...[
          const SizedBox(height: 8),
          GlassCard(
            padding: EdgeInsets.zero,
            child: ExpansionTile(
              minTileHeight: 64,
              shape: const Border(),
              collapsedShape: const Border(),
              leading: const ExchangeIconBadge(Icons.preview_outlined),
              title: const Text('抽取文字預覽'),
              childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              children: [Text(result.extractedPreview)],
            ),
          ),
        ],
        const SizedBox(height: 8),
        Text(result.privacyNote, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}

class _IssueRow extends StatelessWidget {
  const _IssueRow({required this.issue});

  final DocumentCheckIssue issue;

  @override
  Widget build(BuildContext context) {
    final color = switch (issue.severity) {
      'error' => ExchangeColors.danger,
      'warning' => ExchangeColors.amber,
      _ => ExchangeColors.blue,
    };
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.circle, size: 8, color: color),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  issue.title,
                  style: Theme.of(
                    context,
                  ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
                ),
                if (issue.detail.isNotEmpty)
                  Text(
                    issue.detail,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _RewriteResultCard extends StatelessWidget {
  const _RewriteResultCard({required this.result, required this.onCopy});

  final DocumentRewriteResult result;
  final VoidCallback onCopy;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const ExchangeSectionHeader(eyebrow: 'AI 建議稿', title: '調整結果'),
        const SizedBox(height: 8),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const ExchangeIconBadge(Icons.auto_fix_high_rounded),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      _actionLabel(result.action),
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  OutlinedButton.icon(
                    onPressed: onCopy,
                    icon: const Icon(Icons.copy_rounded),
                    label: const Text('複製'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              SelectableText(result.draft),
            ],
          ),
        ),
        if (result.warnings.isNotEmpty) ...[
          const SizedBox(height: 8),
          GlassCard(
            padding: EdgeInsets.zero,
            tint: ExchangeColors.amberSoft,
            child: ExpansionTile(
              initiallyExpanded: true,
              minTileHeight: 64,
              shape: const Border(),
              collapsedShape: const Border(),
              leading: const ExchangeIconBadge(
                Icons.warning_amber_rounded,
                color: ExchangeColors.amber,
                background: Colors.white,
              ),
              title: const Text('送出前確認'),
              childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
              children: result.warnings.map(BulletPoint.new).toList(),
            ),
          ),
        ],
        if (result.changes.isNotEmpty) ...[
          const SizedBox(height: 8),
          GlassCard(
            padding: EdgeInsets.zero,
            child: ExpansionTile(
              minTileHeight: 64,
              shape: const Border(),
              collapsedShape: const Border(),
              leading: const ExchangeIconBadge(Icons.rule_rounded),
              title: const Text('調整內容'),
              childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
              children: result.changes.map(BulletPoint.new).toList(),
            ),
          ),
        ],
        const SizedBox(height: 8),
        Text(result.disclaimer, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}

String _errorText(Object exception) {
  if (exception is ExchangeApiException) return exception.message;
  return '目前無法完成，請稍後再試。';
}

String _dateOnlyText(String value) =>
    value.length >= 10 ? value.substring(0, 10) : value;

String _actionLabel(String action) => switch (action) {
  'translate_en' => '英文版本',
  'shorten' => '精簡版本',
  'grammar' => '文法與用字',
  _ => '正式語氣',
};

Future<void> _openUrl(String value) async {
  final uri = Uri.tryParse(value);
  if (uri == null) return;
  await launchUrl(uri, mode: LaunchMode.externalApplication);
}
