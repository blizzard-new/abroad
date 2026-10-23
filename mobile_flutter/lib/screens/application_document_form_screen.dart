import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:printing/printing.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';

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
  bool saving = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (initialized) return;
    final store = ExchangeStoreScope.of(context);
    for (final field in widget.template.fields) {
      final value = store.applicationValue(widget.template, field);
      if (field.kind == ApplicationFieldKind.checkbox) {
        values[field.id] = value == true;
      } else if (field.kind == ApplicationFieldKind.files) {
        values[field.id] = value is List
            ? value.whereType<ApplicationUpload>().toList()
            : <ApplicationUpload>[];
      } else {
        controllers[field.id] = TextEditingController(
          text: value?.toString() ?? '',
        );
      }
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

  Future<bool> _save({bool announce = true}) async {
    if (!_validate()) return false;
    setState(() => saving = true);
    try {
      await ExchangeStoreScope.of(
        context,
      ).saveApplicationDocument(widget.template, _collectValues());
      if (announce && mounted) _showMessage('已暫存於本次使用；完整答案請匯出 PDF 或在網頁工作台保存。');
      return true;
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  Future<void> _preview() async {
    if (!await _save(announce: false) || !mounted) return;
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
    final autofillCount = store.applicationAutofillCount(widget.template);
    return ExchangePageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          backgroundColor: Colors.white.withValues(alpha: .72),
          surfaceTintColor: Colors.transparent,
          title: const Text('填寫文件'),
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
          leading: IconButton(
            tooltip: '文件清單',
            onPressed: () => Navigator.of(context).pop(),
            icon: const Icon(Icons.folder_copy_outlined),
          ),
        ),
        body: SafeArea(
          top: false,
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(18, 18, 18, 40),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 7,
                  runSpacing: 6,
                  children: [
                    _FormBadge(label: widget.template.stage),
                    _FormBadge(
                      label: widget.template.officialLayout ? '官方格式' : '申請整理',
                      color: widget.template.officialLayout
                          ? ExchangeColors.success
                          : ExchangeColors.blue,
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  widget.template.title,
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 8),
                const Text('此頁完整答案只暫存在本次使用，關閉 App 後不保留。雲端草稿與私密附件請由右上角開啟網頁工作台。'),
                if (autofillCount > 0) ...[
                  const SizedBox(height: 10),
                  Semantics(
                    liveRegion: true,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: ExchangeColors.tealSoft.withValues(alpha: .78),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color: ExchangeColors.teal.withValues(alpha: .2),
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.auto_awesome_rounded,
                            color: ExchangeColors.teal,
                            size: 18,
                          ),
                          const SizedBox(width: 7),
                          Text('已帶入 $autofillCount 欄'),
                        ],
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 14),
                GlassCard(
                  padding: EdgeInsets.zero,
                  child: ExpansionTile(
                    minTileHeight: 56,
                    shape: const Border(),
                    collapsedShape: const Border(),
                    title: const Text('填寫說明'),
                    childrenPadding: const EdgeInsets.fromLTRB(18, 0, 18, 16),
                    children: [
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Text(widget.template.description),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final wide = constraints.maxWidth >= 820;
                    final form = Form(
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
                    );
                    final guide = _PrintGuide(
                      template: widget.template,
                      store: store,
                    );
                    if (!wide) {
                      return Column(
                        children: [form, const SizedBox(height: 16), guide],
                      );
                    }
                    return Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(flex: 2, child: form),
                        const SizedBox(width: 16),
                        Expanded(child: guide),
                      ],
                    );
                  },
                ),
                const SizedBox(height: 22),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final buttons = [
                      FilledButton.icon(
                        onPressed: saving ? null : _save,
                        icon: saving
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.save_outlined),
                        label: const Text('暫存'),
                      ),
                      OutlinedButton.icon(
                        onPressed: saving || store.isGeneratingApplicationPdf
                            ? null
                            : _preview,
                        icon: const Icon(Icons.print_outlined),
                        label: const Text('下載 PDF'),
                      ),
                    ];
                    if (constraints.maxWidth >= 520) {
                      return Row(
                        children: [
                          Expanded(child: buttons[0]),
                          const SizedBox(width: 10),
                          Expanded(child: buttons[1]),
                        ],
                      );
                    }
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        buttons[0],
                        const SizedBox(height: 10),
                        buttons[1],
                      ],
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
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
    return LayoutBuilder(
      builder: (context, constraints) {
        final twoColumns = constraints.maxWidth >= 650;
        final columnWidth = twoColumns
            ? (constraints.maxWidth - 12) / 2
            : constraints.maxWidth;
        return Wrap(
          spacing: 12,
          runSpacing: 12,
          children: template.fields.map((field) {
            final wideField =
                field.kind == ApplicationFieldKind.textarea ||
                field.kind == ApplicationFieldKind.files ||
                field.kind == ApplicationFieldKind.checkbox;
            return SizedBox(
              width: wideField ? constraints.maxWidth : columnWidth,
              child: _ApplicationFieldInput(
                field: field,
                controller: controllers[field.id],
                value: values[field.id],
                onChanged: (value) => onValueChanged(field, value),
                onPickDate: () => onPickDate(field),
                onPickFiles: () => onPickFiles(field),
                onRemoveFile: (index) => onRemoveFile(field, index),
              ),
            );
          }).toList(),
        );
      },
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
            const SizedBox(height: 5),
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
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
            const SizedBox(height: 10),
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
        prefixIcon: field.sensitive
            ? const Icon(Icons.lock_outline_rounded, size: 20)
            : null,
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
          const SizedBox(height: 10),
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
            ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700),
          ),
        ],
      ),
    );
  }
}

class _FormBadge extends StatelessWidget {
  const _FormBadge({required this.label, this.color = ExchangeColors.teal});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .1),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: color,
          fontWeight: FontWeight.w700,
        ),
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
