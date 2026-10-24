import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:printing/printing.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import '../state/workspace_sync.dart';

class ApplicationDocumentFormScreen extends StatefulWidget {
  const ApplicationDocumentFormScreen({required this.template, super.key});

  final ApplicationDocumentTemplate template;

  @override
  State<ApplicationDocumentFormScreen> createState() =>
      _ApplicationDocumentFormScreenState();
}

class _ApplicationDocumentFormScreenState
    extends State<ApplicationDocumentFormScreen> {
  final formKey = GlobalKey<FormState>();
  final controllers = <String, TextEditingController>{};
  final values = <String, dynamic>{};
  bool initialized = false;
  bool started = false;
  String? boundAccount;
  String? boundSchool;
  String? loadError;
  JsonMap? draftSnapshot;

  bool _current(ExchangeStore store) =>
      store.account?.id == boundAccount &&
      store.selectedUniversity == boundSchool;
  bool saving = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (started) return;
    started = true;
    final store = ExchangeStoreScope.of(context);
    boundAccount = store.account?.id;
    boundSchool = store.selectedUniversity;
    Future.microtask(() async {
      try {
        await store.openApplicationDraft(widget.template);
      } catch (_) {
        loadError = '無法讀取安全草稿，請稍後重開此頁。';
      }
      if (!mounted || !_current(store)) return;
      _fillValues(store);
      setState(() => initialized = true);
    });
  }

  void _fillValues(ExchangeStore store) {
    draftSnapshot = store.applicationDraft(widget.template.id)?.editorSnapshot;
    for (final field in widget.template.fields) {
      final value = store.applicationValue(widget.template, field);
      if (field.kind == ApplicationFieldKind.checkbox) {
        values[field.id] = value == true;
      } else if (field.kind == ApplicationFieldKind.files) {
        values[field.id] = value is List
            ? value.whereType<ApplicationUpload>().toList()
            : <ApplicationUpload>[];
      } else {
        (controllers[field.id] ??= TextEditingController()).text =
            value?.toString() ?? '';
      }
    }
  }

  @override
  void dispose() {
    for (final controller in controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _pickDate(ApplicationFormField field) async {
    final controller = controllers[field.id]!;
    final initial = DateTime.tryParse(controller.text) ?? DateTime.now();
    final selected = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2020),
      lastDate: DateTime(2040),
      helpText: field.label,
    );
    if (selected == null) return;
    controller.text = _isoDate(selected);
    setState(() {});
  }

  Future<void> _pickFiles(ApplicationFormField field) async {
    final photosOnly = field.id.contains('photo');
    final typeGroups = photosOnly
        ? const [_imageTypeGroup]
        : const [_pdfTypeGroup, _imageTypeGroup];
    final picked = field.maxFiles > 1
        ? await openFiles(acceptedTypeGroups: typeGroups)
        : [?await openFile(acceptedTypeGroups: typeGroups)];
    if (picked.isEmpty || !mounted) return;
    final selected = picked.take(field.maxFiles).toList();
    final sizes = await Future.wait(selected.map((file) => file.length()));
    if (sizes.any((size) => size > 8 * 1024 * 1024)) {
      _showMessage('每個附件不可超過 8 MB');
      return;
    }
    final uploads = <ApplicationUpload>[];
    for (final file in selected) {
      try {
        final bytes = await file.readAsBytes();
        uploads.add(
          ApplicationUpload(
            name: file.name,
            mimeType: _mimeType(file.name.split('.').last),
            bytes: bytes,
          ),
        );
      } catch (_) {
        _showMessage('無法讀取 ${file.name}');
        return;
      }
    }
    setState(() => values[field.id] = uploads);
    if (picked.length > field.maxFiles) {
      _showMessage('這個欄位最多選擇 ${field.maxFiles} 個檔案');
    }
  }

  bool _validate() {
    if (formKey.currentState?.validate() != true) return false;
    for (final field in widget.template.fields) {
      if (field.kind == ApplicationFieldKind.checkbox &&
          field.required &&
          values[field.id] != true) {
        _showMessage('請確認「${field.label}」');
        return false;
      }
      if (field.kind == ApplicationFieldKind.files) {
        final files = values[field.id] is List
            ? values[field.id] as List
            : const [];
        final minimum = field.minFiles > (field.required ? 1 : 0)
            ? field.minFiles
            : (field.required ? 1 : 0);
        if (files.length < minimum) {
          _showMessage('「${field.label}」至少需要 $minimum 個檔案');
          return false;
        }
      }
    }
    const datePairs = [
      ('planned_start_date', 'planned_end_date'),
      ('course_start_date', 'course_end_date'),
    ];
    for (final pair in datePairs) {
      final start = controllers[pair.$1]?.text ?? '';
      final end = controllers[pair.$2]?.text ?? '';
      if (start.isNotEmpty && end.isNotEmpty && end.compareTo(start) < 0) {
        _showMessage('結束日期不可早於開始日期');
        return false;
      }
    }
    return true;
  }

  Map<String, dynamic> _collectValues() {
    final result = <String, dynamic>{...values};
    for (final entry in controllers.entries) {
      result[entry.key] = entry.value.text.trim();
    }
    return result;
  }

  Future<bool> _save({bool announce = true, bool validate = false}) async {
    final store = ExchangeStoreScope.of(context);
    if (!_current(store) || loadError != null) return false;
    if (validate && !_validate()) return false;
    FocusScope.of(context).unfocus();
    setState(() => saving = true);
    try {
      await store.saveApplicationDocument(
        widget.template,
        _collectValues(),
        markReady: validate,
        draftSnapshot: draftSnapshot,
      );
      if (!mounted || !_current(store)) return false;
      final sync = store.applicationDraft(widget.template.id);
      if (sync?.status == WorkspaceSyncStatus.conflict) {
        final useMobile = await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('草稿在兩個裝置都有修改'),
            content: const Text('同一欄位有不同內容。選擇這些衝突欄位要保留的版本；其他欄位會合併。'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('稍後處理'),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('保留雲端內容'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('保留手機內容'),
              ),
            ],
          ),
        );
        if (useMobile != null && mounted && _current(store)) {
          await sync!.resolveConflict(preferLocal: useMobile);
          if (mounted && _current(store)) setState(() => _fillValues(store));
        }
      }
      if (!mounted || !_current(store)) return false;
      if (announce) {
        _showMessage(
          sync == null
              ? '已暫存於本次使用；登入後可儲存一般欄位草稿。'
              : sync.status == WorkspaceSyncStatus.saved
              ? '一般欄位已加密同步，電腦可接續填寫。'
              : sync.error ?? '草稿已保留在手機，等待同步。',
        );
      }
      if (sync?.status == WorkspaceSyncStatus.saved) {
        setState(() => _fillValues(store));
      }
      return true;
    } catch (_) {
      if (mounted) _showMessage('儲存未完成，請保留此頁並重試。');
      return false;
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  Future<void> _preview() async {
    if (!await _save(announce: false, validate: true) || !mounted) return;
    final store = ExchangeStoreScope.of(context);
    try {
      final bytes = await store.generateApplicationPdf(
        singleTemplateId: widget.template.id,
      );
      await Printing.layoutPdf(
        name: '${widget.template.shortTitle}.pdf',
        onLayout: (_) async => bytes,
      );
    } catch (exception) {
      if (mounted) _showMessage(exception.toString());
    }
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    if (!_current(store)) {
      return Scaffold(
        appBar: AppBar(title: const Text('填寫文件')),
        body: const Center(child: Text('帳號或學校已變更，請返回文件清單重新開啟。')),
      );
    }
    if (!initialized) {
      return Scaffold(
        appBar: AppBar(title: const Text('讀取草稿')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    final draft = store.applicationDraft(widget.template.id);
    final draftStatus = draft == null
        ? '登入後可同步一般欄位草稿。'
        : switch (draft.status) {
            WorkspaceSyncStatus.saved =>
              (draft.draft['revision'] ?? 0) == 0 ? '一般欄位可加密儲存' : '一般欄位已同步',
            WorkspaceSyncStatus.syncing ||
            WorkspaceSyncStatus.loading => '草稿同步中…',
            _ => draft.error ?? '草稿已保留在手機，等待同步。',
          };
    final attachmentNames = jsonMap(draft?.draft['attachments']).values
        .expand((value) => jsonMapList(value))
        .map((item) => textValue(item['file_name']))
        .where((name) => name.isNotEmpty)
        .toList();
    final autofillCount = store.applicationAutofillCount(widget.template);
    return StudentPage(
      title: '填寫文件',
      retainChildren: true,
      leading: IconButton(
        tooltip: '文件清單',
        onPressed: () => Navigator.of(context).maybePop(),
        icon: const Icon(Icons.arrow_back_rounded),
      ),
      actions: [
        IconButton(
          tooltip: '在網頁開啟雲端文件工作台',
          icon: const Icon(Icons.cloud_outlined),
          onPressed: () => launchUrl(
            Uri.parse(store.api.resolveUrl('#application-center')),
            mode: LaunchMode.externalApplication,
          ),
        ),
      ],
      bottomBar: StudentActionBar(
        primary: FilledButton.icon(
          onPressed: saving || loadError != null ? null : _save,
          icon: saving
              ? const SizedBox.square(
                  dimension: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.save_outlined),
          label: const Text('儲存草稿'),
        ),
        secondary: OutlinedButton.icon(
          onPressed:
              saving || loadError != null || store.isGeneratingApplicationPdf
              ? null
              : _preview,
          icon: const Icon(Icons.picture_as_pdf_outlined),
          label: const Text('下載 PDF'),
        ),
      ),
      children: [
        StudentHeading(widget.template.title),
        const SizedBox(height: 12),
        Wrap(
          spacing: 16,
          runSpacing: 8,
          children: [
            StudentIconLabel(Icons.folder_outlined, widget.template.stage),
            StudentIconLabel(
              Icons.description_outlined,
              widget.template.officialLayout ? '官方格式' : '申請整理',
            ),
            if (autofillCount > 0)
              StudentIconLabel(
                Icons.auto_awesome_outlined,
                '已帶入 $autofillCount 欄',
              ),
          ],
        ),
        const SizedBox(height: 16),
        StudentNotice(
          loadError ?? draftStatus,
          icon: loadError != null
              ? Icons.cloud_off_outlined
              : Icons.cloud_done_outlined,
          color: loadError != null
              ? ExchangeColors.danger
              : ExchangeColors.teal,
        ),
        const SizedBox(height: 8),
        const StudentNotice(
          '敏感欄位與新附件只保留於本次使用。',
          icon: Icons.lock_outline_rounded,
          detail: '未填完也能儲存一般欄位草稿。敏感欄位與新選的附件不會保存在手機草稿；私人文件保存與授權請由右上角開啟網頁工作台。',
        ),
        if (attachmentNames.isNotEmpty) ...[
          const SizedBox(height: 8),
          StudentNotice(
            '雲端附件 ${attachmentNames.length} 個；匯出前請重新選檔。',
            icon: Icons.attach_file_rounded,
            detail: '雲端已有附件：${attachmentNames.join('、')}。儲存會保留引用，也可在網頁工作台匯出。',
          ),
        ],
        if (widget.template.description.isNotEmpty) ...[
          const SizedBox(height: 16),
          GlassCard(
            padding: EdgeInsets.zero,
            child: ExpansionTile(
              leading: const Icon(Icons.help_outline_rounded),
              title: const Text('填寫說明'),
              childrenPadding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
              children: [
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(widget.template.description),
                ),
              ],
            ),
          ),
        ],
        const SizedBox(height: 24),
        AbsorbPointer(
          absorbing: saving,
          child: Form(
            key: formKey,
            child: _ApplicationFields(
              template: widget.template,
              controllers: controllers,
              values: values,
              onValueChanged: (field, value) =>
                  setState(() => values[field.id] = value),
              onPickDate: _pickDate,
              onPickFiles: _pickFiles,
              onRemoveFile: (field, index) {
                final files = List<ApplicationUpload>.from(
                  values[field.id] as List? ?? const [],
                )..removeAt(index);
                setState(() => values[field.id] = files);
              },
            ),
          ),
        ),
        const SizedBox(height: 24),
        _PrintGuide(template: widget.template, store: store),
      ],
    );
  }
}

class _ApplicationFields extends StatelessWidget {
  const _ApplicationFields({
    required this.template,
    required this.controllers,
    required this.values,
    required this.onValueChanged,
    required this.onPickDate,
    required this.onPickFiles,
    required this.onRemoveFile,
  });

  final ApplicationDocumentTemplate template;
  final Map<String, TextEditingController> controllers;
  final Map<String, dynamic> values;
  final void Function(ApplicationFormField field, dynamic value) onValueChanged;
  final ValueChanged<ApplicationFormField> onPickDate;
  final ValueChanged<ApplicationFormField> onPickFiles;
  final void Function(ApplicationFormField field, int index) onRemoveFile;

  @override
  Widget build(BuildContext context) {
    final groups = <String, List<ApplicationFormField>>{
      '填寫內容': template.fields
          .where(
            (f) =>
                f.kind != ApplicationFieldKind.files &&
                f.kind != ApplicationFieldKind.checkbox,
          )
          .toList(),
      '附件': template.fields
          .where((f) => f.kind == ApplicationFieldKind.files)
          .toList(),
      '確認事項': template.fields
          .where((f) => f.kind == ApplicationFieldKind.checkbox)
          .toList(),
    };
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final group in groups.entries)
          if (group.value.isNotEmpty) ...[
            StudentSectionTitle(
              group.key,
              icon: group.key == '附件'
                  ? Icons.attach_file_rounded
                  : group.key == '確認事項'
                  ? Icons.checklist_rounded
                  : Icons.edit_note_rounded,
              detail: group.key == '填寫內容' ? '＊ 必填；未填完也能儲存草稿' : null,
            ),
            for (final field in group.value)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: _ApplicationFieldInput(
                  field: field,
                  controller: controllers[field.id],
                  value: values[field.id],
                  onChanged: (value) => onValueChanged(field, value),
                  onPickDate: () => onPickDate(field),
                  onPickFiles: () => onPickFiles(field),
                  onRemoveFile: (index) => onRemoveFile(field, index),
                ),
              ),
          ],
      ],
    );
  }
}

class _ApplicationFieldInput extends StatelessWidget {
  const _ApplicationFieldInput({
    required this.field,
    required this.controller,
    required this.value,
    required this.onChanged,
    required this.onPickDate,
    required this.onPickFiles,
    required this.onRemoveFile,
  });

  final ApplicationFormField field;
  final TextEditingController? controller;
  final dynamic value;
  final ValueChanged<dynamic> onChanged;
  final VoidCallback onPickDate;
  final VoidCallback onPickFiles;
  final ValueChanged<int> onRemoveFile;

  @override
  Widget build(BuildContext context) {
    final label = '${field.label}${field.required ? ' *' : ''}';
    if (field.kind == ApplicationFieldKind.select) {
      final current = field.options.contains(controller?.text)
          ? controller!.text
          : null;
      return DropdownButtonFormField<String>(
        initialValue: current,
        isExpanded: true,
        decoration: InputDecoration(
          labelText: label,
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
        onChanged: (selected) {
          controller?.text = selected ?? '';
          onChanged(selected ?? '');
        },
      );
    }
    if (field.kind == ApplicationFieldKind.checkbox) {
      return GlassCard(
        padding: EdgeInsets.zero,
        child: CheckboxListTile(
          minTileHeight: 56,
          value: value == true,
          title: Text(label),
          secondary: field.helpText.isEmpty
              ? null
              : FieldHelpButton(title: field.label, message: field.helpText),
          onChanged: (selected) => onChanged(selected == true),
        ),
      );
    }
    if (field.kind == ApplicationFieldKind.files) {
      final files = value is List<ApplicationUpload>
          ? value as List<ApplicationUpload>
          : <ApplicationUpload>[];
      final minimum = field.minFiles > (field.required ? 1 : 0)
          ? field.minFiles
          : (field.required ? 1 : 0);
      return GlassCard(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    label,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                if (field.helpText.isNotEmpty)
                  FieldHelpButton(title: field.label, message: field.helpText),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              'PDF、JPG、PNG · 8 MB',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            if (minimum > 1) ...[
              const SizedBox(height: 4),
              Text(
                '至少 $minimum 個，最多 ${field.maxFiles} 個',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: ExchangeColors.amber,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: onPickFiles,
              icon: const Icon(Icons.upload_file_rounded),
              label: Text(files.isEmpty ? '選擇附件' : '重新選擇'),
            ),
            if (files.isNotEmpty) ...[
              const SizedBox(height: 8),
              ...List.generate(
                files.length,
                (index) => ListTile(
                  minTileHeight: 48,
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(
                    files[index].mimeType == 'application/pdf'
                        ? Icons.picture_as_pdf_outlined
                        : Icons.image_outlined,
                  ),
                  title: Text(
                    files[index].name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  trailing: IconButton(
                    tooltip: '移除附件',
                    onPressed: () => onRemoveFile(index),
                    icon: const Icon(Icons.close_rounded),
                  ),
                ),
              ),
            ],
          ],
        ),
      );
    }
    return TextFormField(
      controller: controller,
      readOnly: field.kind == ApplicationFieldKind.date,
      onTap: field.kind == ApplicationFieldKind.date ? onPickDate : null,
      keyboardType: _keyboardType(field.kind),
      maxLines: field.kind == ApplicationFieldKind.textarea ? 5 : 1,
      maxLength: field.maxLength,
      obscureText: false,
      decoration: InputDecoration(
        labelText: label,
        hintText: field.placeholder.isEmpty ? null : field.placeholder,
        prefixIcon: Icon(applicationFieldIcon(field), size: 20),
        suffixIcon:
            field.kind == ApplicationFieldKind.date || field.helpText.isNotEmpty
            ? Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (field.helpText.isNotEmpty)
                    FieldHelpButton(
                      title: field.label,
                      message: field.helpText,
                    ),
                  if (field.kind == ApplicationFieldKind.date)
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 14),
                      child: Icon(Icons.calendar_today_outlined, size: 20),
                    ),
                ],
              )
            : null,
      ),
      validator: field.required
          ? (text) =>
                text == null || text.trim().isEmpty ? '請填寫${field.label}' : null
          : null,
    );
  }
}

class _PrintGuide extends StatelessWidget {
  const _PrintGuide({required this.template, required this.store});

  final ApplicationDocumentTemplate template;
  final ExchangeStore store;

  @override
  Widget build(BuildContext context) {
    final selection =
        store.applicationSelections[template.id] ??
        ApplicationDocumentSelectionState.initial(template.defaultCopies);
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const ExchangeIconBadge(Icons.route_outlined),
              const SizedBox(width: 12),
              Text('送件資訊', style: Theme.of(context).textTheme.titleLarge),
            ],
          ),
          const SizedBox(height: 16),
          _GuideRow(label: '份數', value: '${selection.copies} 份'),
          _GuideRow(label: '送件', value: _listText(template.destinations)),
          _GuideRow(label: '簽名', value: _listText(template.signatures)),
          _GuideRow(label: '核章', value: _listText(template.stamps)),
          _GuideRow(
            label: '下一步',
            value: _applicationDocumentNextStep(template, selection.status),
          ),
          const SizedBox(height: 8),
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
            onChanged: (status) =>
                store.updateApplicationSelection(template.id, status: status),
          ),
          if (template.conditionalNote.isNotEmpty) ...[
            const SizedBox(height: 12),
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              childrenPadding: const EdgeInsets.only(bottom: 10),
              minTileHeight: 52,
              shape: const Border(),
              collapsedShape: const Border(),
              leading: const Icon(Icons.info_outline_rounded),
              title: const Text('注意事項'),
              children: [
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(template.conditionalNote),
                ),
              ],
            ),
          ],
          if (template.sourceUrl.isNotEmpty) ...[
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () => launchUrl(
                Uri.parse(template.sourceUrl),
                mode: LaunchMode.externalApplication,
              ),
              icon: const Icon(Icons.open_in_new_rounded),
              label: const Text('官方來源'),
            ),
          ],
        ],
      ),
    );
  }
}

class _GuideRow extends StatelessWidget {
  const _GuideRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 2),
          Text(
            value,
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}

String _listText(List<String> values) =>
    values.isEmpty ? '不需要' : values.join('、');

String _applicationDocumentNextStep(
  ApplicationDocumentTemplate template,
  ApplicationDocumentProgress status,
) => switch (status) {
  ApplicationDocumentProgress.draft => '完成必填欄位，再產生 PDF。',
  ApplicationDocumentProgress.readyToPrint => '下載 PDF，依份數列印並核對附件。',
  ApplicationDocumentProgress.pendingSignature =>
    template.signatures.isEmpty
        ? '確認是否需要親筆簽名。'
        : '請完成：${template.signatures.join('、')}',
  ApplicationDocumentProgress.pendingDepartmentStamp =>
    template.stamps.isEmpty
        ? '向承辦單位確認核章流程。'
        : '請完成：${template.stamps.join('、')}',
  ApplicationDocumentProgress.pendingSubmission =>
    template.destinations.isEmpty
        ? '依公告送件並保留副本。'
        : '交至：${template.destinations.join('、')}',
  ApplicationDocumentProgress.completed => '保留 PDF 與收件證明。',
};

String _isoDate(DateTime value) =>
    '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';

String _mimeType(String? extension) => switch (extension?.toLowerCase()) {
  'pdf' => 'application/pdf',
  'png' => 'image/png',
  _ => 'image/jpeg',
};

const _imageTypeGroup = XTypeGroup(
  label: '圖片',
  extensions: ['jpg', 'jpeg', 'png'],
  mimeTypes: ['image/jpeg', 'image/png'],
  uniformTypeIdentifiers: ['public.jpeg', 'public.png'],
);

const _pdfTypeGroup = XTypeGroup(
  label: 'PDF',
  extensions: ['pdf'],
  mimeTypes: ['application/pdf'],
  uniformTypeIdentifiers: ['com.adobe.pdf'],
);

TextInputType _keyboardType(ApplicationFieldKind kind) => switch (kind) {
  ApplicationFieldKind.email => TextInputType.emailAddress,
  ApplicationFieldKind.tel => TextInputType.phone,
  ApplicationFieldKind.number => const TextInputType.numberWithOptions(
    decimal: true,
  ),
  _ => TextInputType.text,
};

IconData applicationFieldIcon(ApplicationFormField field) => field.sensitive
    ? Icons.lock_outline_rounded
    : switch (field.kind) {
        ApplicationFieldKind.email => Icons.mail_outline_rounded,
        ApplicationFieldKind.tel => Icons.phone_outlined,
        ApplicationFieldKind.date => Icons.event_outlined,
        ApplicationFieldKind.number => Icons.numbers_rounded,
        ApplicationFieldKind.textarea => Icons.notes_rounded,
        ApplicationFieldKind.select => Icons.list_alt_rounded,
        ApplicationFieldKind.files => Icons.attach_file_rounded,
        ApplicationFieldKind.checkbox => Icons.check_box_outlined,
        ApplicationFieldKind.text => Icons.edit_outlined,
      };
