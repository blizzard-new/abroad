import 'package:flutter/material.dart';
import 'package:printing/printing.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import 'ai_tools_screens.dart';
import 'application_document_form_screen.dart';
import 'feature_screens.dart' show FeaturePageScaffold;

class ApplicationDocumentsScreen extends StatelessWidget {
  const ApplicationDocumentsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final groups = <String, List<ApplicationDocumentTemplate>>{};
    for (final template in store.applicationTemplates) {
      groups.putIfAbsent(template.stage, () => []).add(template);
    }

    return SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: store.loadApplicationTemplates,
        child: ListView(
          key: const PageStorageKey('application-documents'),
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 128),
          children: [
            _ApplicationHeader(store: store),
            const SizedBox(height: 20),
            GlassCard(
              tint: ExchangeColors.blueSoft,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const StudentIconLabel(
                    Icons.checklist_rounded,
                    '一次準備，一步完成',
                    color: ExchangeColors.blue,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    store.applicationTemplates.isEmpty
                        ? '先設定你的申請目標'
                        : '${store.applicationFormReadyCount} / ${store.applicationTemplates.length} 份文件已完成',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  if (store.applicationTemplates.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    LinearProgressIndicator(
                      value:
                          (store.applicationFormReadyCount /
                                  store.applicationTemplates.length)
                              .clamp(0, 1),
                      minHeight: 6,
                      borderRadius: BorderRadius.circular(8),
                      color: ExchangeColors.blue,
                      backgroundColor: ExchangeColors.surface,
                      semanticsLabel: '文件準備進度',
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),
            _ApplicationActions(store: store),
            const SizedBox(height: 24),
            const ExchangeSectionHeader(title: '待辦文件'),
            const SizedBox(height: 12),
            if (store.isApplicationDocumentsLoading)
              const LoadingCards(count: 3)
            else if (store.applicationDocumentsError != null)
              InlineError(
                message: store.applicationDocumentsError!,
                onRetry: store.loadApplicationTemplates,
              )
            else if (groups.isEmpty)
              const EmptyState(
                icon: Icons.task_alt_rounded,
                title: '目前沒有待填文件',
                message: '先到「申請設定」選擇目標。',
              )
            else
              ...groups.entries.expand(
                (group) => [
                  _StageHeader(title: group.key, count: group.value.length),
                  ...group.value.map(
                    (template) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: _TemplateCard(template: template, store: store),
                    ),
                  ),
                  const SizedBox(height: 8),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class _ApplicationHeader extends StatelessWidget {
  const _ApplicationHeader({required this.store});

  final ExchangeStore store;

  @override
  Widget build(BuildContext context) {
    final target = store.applicationContext.targetSchool;
    return StudentHeading(
      '申請文件',
      subtitle: target.isEmpty
          ? _programLabel(store.applicationContext.programType)
          : target,
    );
  }
}

class _ApplicationActions extends StatelessWidget {
  const _ApplicationActions({required this.store});

  final ExchangeStore store;

  void _open(BuildContext context, Widget page) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));
  }

  @override
  Widget build(BuildContext context) {
    final actions = [
      (
        icon: Icons.tune_rounded,
        title: '申請設定',
        detail: _programLabel(store.applicationContext.programType),
        color: ExchangeColors.blue,
        page: const ApplicationSetupScreen(),
      ),
      (
        icon: Icons.badge_outlined,
        title: '共用資料',
        detail:
            '${store.applicationProfileCompletion.completed}/${store.applicationProfileCompletion.total} 欄',
        color: ExchangeColors.teal,
        page: const ApplicationProfileScreen(),
      ),
      (
        icon: Icons.print_outlined,
        title: '列印包',
        detail: '${store.selectedApplicationCopies} 份',
        color: ExchangeColors.coral,
        page: const ApplicationPacketScreen(),
      ),
      (
        icon: Icons.fact_check_outlined,
        title: '文件檢查',
        detail: '送出前確認',
        color: ExchangeColors.success,
        page: const DocumentCheckScreen(),
      ),
      (
        icon: Icons.auto_fix_high_rounded,
        title: '文件改寫',
        detail: '正式化與翻譯',
        color: ExchangeColors.blue,
        page: const WritingAssistantScreen(),
      ),
    ];
    actions.add((
      icon: Icons.help_outline_rounded,
      title: '使用指南',
      detail: '',
      color: ExchangeColors.teal,
      page: const SizedBox(),
    ));
    return GlassCard(
      padding: const EdgeInsets.all(8),
      child: Column(
        children: [
          LayoutBuilder(
            builder: (context, constraints) => Wrap(
              spacing: 4,
              runSpacing: 4,
              children: actions
                  .map(
                    (action) => SizedBox(
                      width: MediaQuery.textScalerOf(context).scale(16) > 24
                          ? (constraints.maxWidth - 4) / 2
                          : (constraints.maxWidth - 8) / 3,
                      child: TextButton(
                        onPressed: () {
                          if (action.title == '使用指南') {
                            showStudentGuide(
                              context,
                              title: '三步完成申請文件',
                              steps: const [
                                (
                                  icon: Icons.tune_rounded,
                                  title: '選申請目標',
                                  detail: '先設定申請類型與學校，再填共用資料。',
                                ),
                                (
                                  icon: Icons.edit_document,
                                  title: '逐份填寫',
                                  detail: '從下方清單開啟文件，儲存後會更新完成進度。',
                                ),
                                (
                                  icon: Icons.print_outlined,
                                  title: '檢查與列印',
                                  detail: '確認文件內容與官方要求，再到列印包匯出。',
                                ),
                              ],
                            );
                          } else {
                            _open(context, action.page);
                          }
                        },
                        child: Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          child: Column(
                            children: [
                              ExchangeIconBadge(
                                action.icon,
                                color: action.color,
                                background: action.color.withValues(alpha: .08),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                action.title,
                                textAlign: TextAlign.center,
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  )
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }
}

class _StageHeader extends StatelessWidget {
  const _StageHeader({required this.title, required this.count});

  final String title;
  final int count;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(2, 8, 2, 10),
      child: Row(
        children: [
          Expanded(
            child: Text(title, style: Theme.of(context).textTheme.titleMedium),
          ),
          Text('$count 份', style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}

class _TemplateCard extends StatelessWidget {
  const _TemplateCard({required this.template, required this.store});

  final ApplicationDocumentTemplate template;
  final ExchangeStore store;

  @override
  Widget build(BuildContext context) {
    final completion = store.applicationTemplateCompletion(template);
    final selection =
        store.applicationSelections[template.id] ??
        ApplicationDocumentSelectionState.initial(template.defaultCopies);
    return GlassCard(
      padding: const EdgeInsets.fromLTRB(14, 13, 10, 13),
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ApplicationDocumentFormScreen(template: template),
        ),
      ),
      child: Row(
        children: [
          ExchangeIconBadge(
            _stageIcon(template.stage),
            color: completion.ready
                ? ExchangeColors.success
                : ExchangeColors.blue,
            background: completion.ready
                ? const Color(0xFFE1F3EA)
                : ExchangeColors.blueSoft,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: [
                    _MiniBadge(label: template.category),
                    if (template.officialLayout)
                      _MiniBadge(label: '官方格式', color: ExchangeColors.teal),
                    _MiniBadge(
                      label: selection.status.label,
                      color: completion.ready
                          ? ExchangeColors.success
                          : ExchangeColors.secondaryInk,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  template.shortTitle,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(999),
                        child: LinearProgressIndicator(
                          minHeight: 5,
                          value: completion.percent / 100,
                          color: completion.ready
                              ? ExchangeColors.success
                              : ExchangeColors.blue,
                          backgroundColor: ExchangeColors.line,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '${completion.percent}% · ${selection.copies} 份',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          const Icon(Icons.chevron_right_rounded),
        ],
      ),
    );
  }
}

class _MiniBadge extends StatelessWidget {
  const _MiniBadge({required this.label, this.color = ExchangeColors.blue});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .09),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: color,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class ApplicationSetupScreen extends StatefulWidget {
  const ApplicationSetupScreen({super.key});

  @override
  State<ApplicationSetupScreen> createState() => _ApplicationSetupScreenState();
}

class _ApplicationSetupScreenState extends State<ApplicationSetupScreen> {
  final yearController = TextEditingController();
  bool initialized = false;
  bool saving = false;
  String programType = 'exchange';
  String targetSchool = '';
  String semester = '';
  final flags = <String>{};

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (initialized) return;
    final contextValue = ExchangeStoreScope.of(context).applicationContext;
    programType = contextValue.programType;
    targetSchool = contextValue.targetSchool;
    semester = contextValue.semester;
    yearController.text = contextValue.academicYear;
    flags.addAll(contextValue.flags);
    initialized = true;
  }

  @override
  void dispose() {
    yearController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final store = ExchangeStoreScope.of(context);
    final school = store.dashboard?.partnerUniversities
        .where((item) => item.schoolName == targetSchool)
        .firstOrNull;
    setState(() => saving = true);
    await store.updateApplicationContext(
      ApplicationCenterContext(
        schoolName: store.selectedUniversity,
        targetSchool: targetSchool,
        targetCountry: school?.country ?? '',
        programType: programType,
        academicYear: yearController.text.trim(),
        semester: semester,
        flags: flags.toList()..sort(),
      ),
    );
    if (!mounted) return;
    setState(() => saving = false);
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('申請文件清單已更新')));
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final schools = [...?store.dashboard?.partnerUniversities]
      ..sort(
        (left, right) => '${left.country}${left.schoolName}'.compareTo(
          '${right.country}${right.schoolName}',
        ),
      );
    if (targetSchool.isNotEmpty &&
        !schools.any((school) => school.schoolName == targetSchool)) {
      targetSchool = '';
    }
    return FeaturePageScaffold(
      title: '申請設定',
      bottomBar: StudentActionBar(
        primary: FilledButton.icon(
          onPressed: saving ? null : _save,
          icon: const Icon(Icons.check_rounded),
          label: Text(saving ? '正在更新' : '更新文件清單'),
        ),
      ),
      children: [
        const StudentSectionTitle('申請目標', icon: Icons.flag_outlined),
        DropdownButtonFormField<String>(
          initialValue: programType,
          isExpanded: true,
          decoration: const InputDecoration(
            labelText: '申請類型',
            prefixIcon: Icon(Icons.school_outlined),
          ),
          items: _programOptions.entries
              .map(
                (entry) => DropdownMenuItem(
                  value: entry.key,
                  child: Text(entry.value),
                ),
              )
              .toList(),
          onChanged: (value) => setState(() => programType = value!),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          initialValue: targetSchool,
          isExpanded: true,
          decoration: const InputDecoration(
            labelText: '交換學校',
            prefixIcon: Icon(Icons.public_rounded),
          ),
          items: [
            const DropdownMenuItem(value: '', child: Text('尚未決定')),
            ...schools.map(
              (school) => DropdownMenuItem(
                value: school.schoolName,
                child: Text(
                  '${school.country} · ${school.schoolName}',
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ),
          ],
          onChanged: (value) => setState(() => targetSchool = value ?? ''),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: yearController,
          textInputAction: TextInputAction.next,
          decoration: const InputDecoration(
            labelText: '申請學年度',
            prefixIcon: Icon(Icons.event_outlined),
            hintText: '例如 116',
          ),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          initialValue: semester,
          decoration: const InputDecoration(
            labelText: '交換學期',
            prefixIcon: Icon(Icons.date_range_outlined),
          ),
          items: const [
            DropdownMenuItem(value: '', child: Text('尚未決定')),
            DropdownMenuItem(value: '第一學期', child: Text('第一學期')),
            DropdownMenuItem(value: '第二學期', child: Text('第二學期')),
            DropdownMenuItem(value: '一學年', child: Text('一學年')),
          ],
          onChanged: (value) => setState(() => semester = value ?? ''),
        ),
        const SizedBox(height: 24),
        const StudentSectionTitle('適用條件', icon: Icons.checklist_rounded),
        GlassCard(
          padding: EdgeInsets.zero,
          child: Column(
            children: [
              _FlagTile(
                title: '申請出國補助',
                value: flags.contains('subsidy'),
                onChanged: (value) => setState(() {
                  value ? flags.add('subsidy') : flags.remove('subsidy');
                }),
              ),
              const Divider(),
              _FlagTile(
                title: '需要役男出境文件',
                value: flags.contains('military_service'),
                onChanged: (value) => setState(() {
                  value
                      ? flags.add('military_service')
                      : flags.remove('military_service');
                }),
              ),
              const Divider(),
              _FlagTile(
                title: '交換期間為一學年',
                value: flags.contains('full_year'),
                onChanged: (value) => setState(() {
                  value ? flags.add('full_year') : flags.remove('full_year');
                }),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _FlagTile extends StatelessWidget {
  const _FlagTile({
    required this.title,
    required this.value,
    required this.onChanged,
  });

  final String title;
  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    return SwitchListTile.adaptive(
      minTileHeight: 56,
      title: Text(title),
      value: value,
      onChanged: onChanged,
    );
  }
}

class ApplicationProfileScreen extends StatefulWidget {
  const ApplicationProfileScreen({super.key});

  @override
  State<ApplicationProfileScreen> createState() =>
      _ApplicationProfileScreenState();
}

class _ApplicationProfileScreenState extends State<ApplicationProfileScreen> {
  final formKey = GlobalKey<FormState>();
  final controllers = <String, TextEditingController>{};
  final values = <String, dynamic>{};
  bool initialized = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (initialized) return;
    final store = ExchangeStoreScope.of(context);
    for (final field in store.applicationProfileFields) {
      final key = field.reusableProfileKey;
      var value = store.applicationProfile[key];
      if (key == 'email' && (value == null || value.toString().isEmpty)) {
        value = store.account?.email ?? '';
      }
      values[key] =
          value ?? (field.kind == ApplicationFieldKind.checkbox ? false : '');
      controllers[key] = TextEditingController(text: value?.toString() ?? '');
    }
    initialized = true;
  }

  @override
  void dispose() {
    for (final controller in controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    if (formKey.currentState?.validate() != true) return;
    final store = ExchangeStoreScope.of(context);
    for (final entry in controllers.entries) {
      values[entry.key] = entry.value.text.trim();
    }
    await store.saveApplicationProfile(values);
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('資料已套用到所有文件')));
    Navigator.of(context).pop();
  }

  Future<void> _toggleMemory(bool enabled) async {
    final store = ExchangeStoreScope.of(context);
    await store.setApplicationProfileMemoryEnabled(enabled);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(enabled ? '已記住常用資料，私密欄位除外' : '已關閉並清除裝置記憶')),
    );
  }

  Future<void> _clearMemory() async {
    final store = ExchangeStoreScope.of(context);
    await store.clearApplicationProfileMemory();
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('已清除裝置記憶，目前資料仍保留')));
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final fields = [...store.applicationProfileFields]
      ..sort((left, right) {
        final leftIndex = _profileOrder.indexOf(left.reusableProfileKey);
        final rightIndex = _profileOrder.indexOf(right.reusableProfileKey);
        return (leftIndex < 0 ? 999 : leftIndex).compareTo(
          rightIndex < 0 ? 999 : rightIndex,
        );
      });
    final commonFields = fields.where((field) => !field.sensitive).toList();
    final sensitiveFields = fields.where((field) => field.sensitive).toList();
    return FeaturePageScaffold(
      title: '共用資料',
      bottomBar: StudentActionBar(
        primary: FilledButton.icon(
          onPressed: fields.isEmpty ? null : _save,
          icon: const Icon(Icons.save_outlined),
          label: const Text('儲存資料'),
        ),
      ),
      children: [
        GlassCard(
          padding: EdgeInsets.zero,
          child: Column(
            children: [
              SwitchListTile.adaptive(
                minTileHeight: 64,
                secondary: const Icon(Icons.auto_awesome_rounded),
                title: const Text('記住常用資料'),
                subtitle: const Text('下次自動帶入，私密資料除外。'),
                value: store.applicationProfileMemoryEnabled,
                onChanged: _toggleMemory,
              ),
              const Divider(),
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 4, 8, 6),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        store.applicationProfileMemoryEnabled
                            ? '已記住 ${store.applicationRememberedProfileCount} 欄'
                            : '僅保留本次使用',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                    TextButton.icon(
                      onPressed: store.applicationProfileMemoryEnabled
                          ? _clearMemory
                          : null,
                      icon: const Icon(Icons.delete_outline_rounded),
                      label: const Text('清除'),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (fields.isEmpty)
          const EmptyState(
            icon: Icons.cloud_off_outlined,
            title: '尚未取得欄位',
            message: '返回文件清單重新整理後再填寫。',
          )
        else
          Form(
            key: formKey,
            child: Column(
              children: [
                const StudentSectionTitle(
                  '基本與聯絡資料',
                  icon: Icons.badge_outlined,
                ),
                ...commonFields.map(
                  (field) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: _ProfileField(
                      field: field,
                      controller: controllers[field.reusableProfileKey]!,
                      value: values[field.reusableProfileKey],
                      onChanged: (value) =>
                          values[field.reusableProfileKey] = value,
                    ),
                  ),
                ),
                if (sensitiveFields.isNotEmpty)
                  GlassCard(
                    padding: EdgeInsets.zero,
                    child: ExpansionTile(
                      minTileHeight: 60,
                      shape: const Border(),
                      collapsedShape: const Border(),
                      leading: const Icon(Icons.lock_outline_rounded),
                      title: const Text('私密資料'),
                      subtitle: const Text('不會存入裝置記憶'),
                      childrenPadding: const EdgeInsets.fromLTRB(14, 4, 14, 4),
                      children: sensitiveFields
                          .map(
                            (field) => Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: _ProfileField(
                                field: field,
                                controller:
                                    controllers[field.reusableProfileKey]!,
                                value: values[field.reusableProfileKey],
                                onChanged: (value) =>
                                    values[field.reusableProfileKey] = value,
                              ),
                            ),
                          )
                          .toList(),
                    ),
                  ),
              ],
            ),
          ),
      ],
    );
  }
}

class _ProfileField extends StatelessWidget {
  const _ProfileField({
    required this.field,
    required this.controller,
    required this.value,
    required this.onChanged,
  });

  final ApplicationFormField field;
  final TextEditingController controller;
  final dynamic value;
  final ValueChanged<dynamic> onChanged;

  @override
  Widget build(BuildContext context) {
    if (field.kind == ApplicationFieldKind.select) {
      final current = field.options.contains(value) ? value as String : null;
      return DropdownButtonFormField<String>(
        initialValue: current,
        isExpanded: true,
        decoration: InputDecoration(
          labelText: _fieldLabel(field),
          prefixIcon: Icon(applicationFieldIcon(field), size: 20),
          suffixIcon: field.helpText.isEmpty
              ? null
              : FieldHelpButton(title: field.label, message: field.helpText),
        ),
        items: field.options
            .map(
              (option) => DropdownMenuItem(value: option, child: Text(option)),
            )
            .toList(),
        validator: field.required
            ? (selected) => selected == null || selected.isEmpty
                  ? '請選擇${field.label}'
                  : null
            : null,
        onChanged: onChanged,
      );
    }
    if (field.kind == ApplicationFieldKind.checkbox) {
      return GlassCard(
        padding: EdgeInsets.zero,
        child: CheckboxListTile(
          minTileHeight: 56,
          value: value == true,
          title: Text(_fieldLabel(field)),
          secondary: field.helpText.isEmpty
              ? null
              : FieldHelpButton(title: field.label, message: field.helpText),
          onChanged: (selected) => onChanged(selected == true),
        ),
      );
    }
    return TextFormField(
      controller: controller,
      keyboardType: _keyboardType(field.kind),
      maxLines: field.kind == ApplicationFieldKind.textarea ? 4 : 1,
      maxLength: field.maxLength,
      decoration: InputDecoration(
        labelText: _fieldLabel(field),
        hintText: field.placeholder.isEmpty ? null : field.placeholder,
        prefixIcon: Icon(applicationFieldIcon(field), size: 20),
        suffixIcon: field.helpText.isEmpty
            ? null
            : FieldHelpButton(title: field.label, message: field.helpText),
      ),
      validator: field.required
          ? (text) =>
                text == null || text.trim().isEmpty ? '請填寫${field.label}' : null
          : null,
    );
  }
}

class ApplicationPacketScreen extends StatelessWidget {
  const ApplicationPacketScreen({super.key});

  Future<void> _preview(BuildContext context, ExchangeStore store) async {
    try {
      final bytes = await store.generateApplicationPdf();
      await Printing.layoutPdf(
        name:
            '${store.applicationContext.targetSchool.isEmpty ? '交換申請' : store.applicationContext.targetSchool}-列印包.pdf',
        onLayout: (_) async => bytes,
      );
    } catch (exception) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(exception.toString())));
    }
  }

  Future<void> _share(BuildContext context, ExchangeStore store) async {
    try {
      final bytes = await store.generateApplicationPdf();
      await Printing.sharePdf(
        bytes: bytes,
        filename:
            '${store.applicationContext.targetSchool.isEmpty ? '交換申請' : store.applicationContext.targetSchool}-列印包.pdf',
      );
    } catch (exception) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(exception.toString())));
    }
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    return FeaturePageScaffold(
      title: '列印包',
      bottomBar: StudentActionBar(
        primary: FilledButton.icon(
          onPressed:
              store.applicationPacketReady && !store.isGeneratingApplicationPdf
              ? () => _preview(context, store)
              : null,
          icon: const Icon(Icons.picture_as_pdf_outlined),
          label: const Text('產生整包 PDF'),
        ),
        secondary: OutlinedButton.icon(
          onPressed:
              store.applicationPacketReady && !store.isGeneratingApplicationPdf
              ? () => _share(context, store)
              : null,
          icon: const Icon(Icons.ios_share_rounded),
          label: const Text('分享 PDF'),
        ),
      ),
      children: [
        _PageLead(
          icon: Icons.print_outlined,
          title: '${store.selectedApplicationCopies} 份待列印',
          detail: '簽名 · 核章 · 送件',
        ),
        const SizedBox(height: 16),
        if (store.applicationTemplates.isEmpty)
          const EmptyState(
            icon: Icons.description_outlined,
            title: '還沒有文件',
            message: '先設定申請條件並完成要填寫的表單。',
          )
        else
          ...store.applicationTemplates.map(
            (template) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: _PacketRow(template: template, store: store),
            ),
          ),
        const SizedBox(height: 8),
        GlassCard(
          padding: EdgeInsets.zero,
          child: ExpansionTile(
            minTileHeight: 56,
            shape: const Border(),
            collapsedShape: const Border(),
            leading: const Icon(Icons.draw_outlined),
            title: const Text('列印提醒'),
            childrenPadding: const EdgeInsets.fromLTRB(18, 0, 18, 16),
            children: const [
              Align(
                alignment: Alignment.centerLeft,
                child: Text('親簽與核章位置會保留空白。'),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _PacketRow extends StatelessWidget {
  const _PacketRow({required this.template, required this.store});

  final ApplicationDocumentTemplate template;
  final ExchangeStore store;

  @override
  Widget build(BuildContext context) {
    final selection =
        store.applicationSelections[template.id] ??
        ApplicationDocumentSelectionState.initial(template.defaultCopies);
    final complete = store.applicationTemplateCompletion(template).ready;
    return GlassCard(
      padding: const EdgeInsets.fromLTRB(8, 6, 10, 10),
      child: Column(
        children: [
          CheckboxListTile(
            minTileHeight: 56,
            contentPadding: const EdgeInsets.symmetric(horizontal: 4),
            value: selection.selected,
            title: Text(
              template.shortTitle,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Text(complete ? '必填欄位已完成' : '尚有必填欄位'),
            secondary: Icon(
              complete ? Icons.check_circle_rounded : Icons.edit_note_rounded,
              color: complete ? ExchangeColors.success : ExchangeColors.amber,
            ),
            onChanged: (value) => store.updateApplicationSelection(
              template.id,
              selected: value == true,
            ),
          ),
          if (selection.selected) ...[
            const Divider(),
            Column(
              children: [
                DropdownButtonFormField<ApplicationDocumentProgress>(
                  initialValue: selection.status,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: '目前進度'),
                  items: ApplicationDocumentProgress.values
                      .map(
                        (status) => DropdownMenuItem(
                          value: status,
                          child: Text(status.label),
                        ),
                      )
                      .toList(),
                  onChanged: (status) => store.updateApplicationSelection(
                    template.id,
                    status: status,
                  ),
                ),
                const SizedBox(height: 12),
                Semantics(
                  label: '${template.shortTitle}列印份數 ${selection.copies}',
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      IconButton(
                        tooltip: '減少一份',
                        onPressed: selection.copies > 1
                            ? () => store.updateApplicationSelection(
                                template.id,
                                copies: selection.copies - 1,
                              )
                            : null,
                        icon: const Icon(Icons.remove_rounded),
                      ),
                      SizedBox(
                        width: 32,
                        child: Text(
                          '${selection.copies}',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
                      IconButton(
                        tooltip: '增加一份',
                        onPressed: selection.copies < 10
                            ? () => store.updateApplicationSelection(
                                template.id,
                                copies: selection.copies + 1,
                              )
                            : null,
                        icon: const Icon(Icons.add_rounded),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _PageLead extends StatelessWidget {
  const _PageLead({
    required this.icon,
    required this.title,
    required this.detail,
  });

  final IconData icon;
  final String title;
  final String detail;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      tint: ExchangeColors.tealSoft,
      child: Row(
        children: [
          ExchangeIconBadge(icon, background: Colors.white),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 4),
                Text(detail, style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

const _programOptions = {
  'exchange': '交換學生',
  'dual_degree': '雙聯學位',
  'internship': '海外實習',
  'short_term_credit': '境外短期學分課程',
};

String _programLabel(String value) => _programOptions[value] ?? '交換學生';

const _profileOrder = [
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
  'id_number',
  'birth_date',
  'passport_number',
  'guardian_id_number',
];

String _fieldLabel(ApplicationFormField field) =>
    '${field.label}${field.required ? ' *' : ''}';

TextInputType _keyboardType(ApplicationFieldKind kind) => switch (kind) {
  ApplicationFieldKind.email => TextInputType.emailAddress,
  ApplicationFieldKind.tel => TextInputType.phone,
  ApplicationFieldKind.number => const TextInputType.numberWithOptions(
    decimal: true,
  ),
  _ => TextInputType.text,
};

IconData _stageIcon(String stage) => switch (stage) {
  '校內申請' => Icons.account_balance_outlined,
  '合作校申請' => Icons.public_rounded,
  '出國前' => Icons.flight_takeoff_rounded,
  '海外期間' => Icons.travel_explore_rounded,
  '返國後' => Icons.home_work_outlined,
  '短期課程申請' => Icons.school_outlined,
  _ => Icons.description_outlined,
};
