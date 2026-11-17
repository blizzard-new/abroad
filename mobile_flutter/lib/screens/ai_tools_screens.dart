import 'dart:typed_data';

import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
import '../data/exchange_api.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import 'feature_screens.dart' show FeaturePageScaffold;

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
    final store = ExchangeStoreScope.of(context, listen: false);
    setState(() {
      isLoading = true;
      error = null;
    });
    try {
      final bytes = await file.readAsBytes();
      final checked = await store.api.reviewDocument(
        fileName: file.name,
        bytes: Uint8List.fromList(bytes),
        documentType: documentType,
        expectedWordLimit: int.tryParse(wordLimitController.text.trim()),
        requireSignature: requireSignature,
        consent: true,
        accessToken: store.accessToken,
      );
      if (!mounted) return;
      setState(() => result = checked);
    } catch (exception) {
      if (!mounted) return;
      final message = exception is ExchangeApiException
          ? exception.message
          : exception.toString();
      setState(() => error = message);
    } finally {
      if (mounted) setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FeaturePageScaffold(
      title: '格式與字數檢查',
      bottomBar: StudentActionBar(
        primary: FilledButton.icon(
          onPressed: isLoading ? null : _check,
          icon: isLoading
              ? const SizedBox.square(
                  dimension: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: ExchangeColors.surface,
                  ),
                )
              : const Icon(Icons.fact_check_outlined),
          label: Text(isLoading ? '檢查中…' : '開始檢查'),
        ),
      ),
      children: [
        const StudentHeading(
          '格式與字數檢查',
          subtitle: '核對頁數、字數上限、簽名欄與文字可讀性。',
        ),
        const SizedBox(height: 12),
        const StudentNotice(
          '檔案僅用於本次格式、字數與欄位規則檢查，不使用外部 AI，亦不會自動送出申請。',
          icon: Icons.verified_user_outlined,
        ),
        const SizedBox(height: 16),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(
                    Icons.upload_file_rounded,
                    color: ExchangeColors.actionBlue,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '選擇文件',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  if (selectedFile != null)
                    const Icon(
                      Icons.check_circle_rounded,
                      color: ExchangeColors.success,
                      size: 20,
                    ),
                ],
              ),
              const SizedBox(height: 12),
              InkWell(
                borderRadius: BorderRadius.circular(12),
                onTap: isLoading ? null : _pickFile,
                child: Container(
                  constraints: const BoxConstraints(minHeight: 64),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: ExchangeColors.surfaceMuted,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: ExchangeColors.line),
                  ),
                  child: Row(
                    children: [
                      const ExchangeIconBadge(Icons.description_outlined),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          selectedFile?.name ?? '選擇 PDF、DOCX 或 TXT 檔案',
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.titleSmall,
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
              const SizedBox(height: 14),
              DropdownButtonFormField<String>(
                initialValue: documentType,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: '文件類型',
                  prefixIcon: Icon(Icons.category_outlined),
                ),
                items: const [
                  DropdownMenuItem(value: 'auto', child: Text('自動判斷')),
                  DropdownMenuItem(value: 'study_plan', child: Text('讀書計畫')),
                  DropdownMenuItem(value: 'cv', child: Text('履歷')),
                  DropdownMenuItem(value: 'recommendation', child: Text('推薦信')),
                  DropdownMenuItem(value: 'other', child: Text('其他')),
                ],
                onChanged: (value) =>
                    setState(() => documentType = value ?? 'auto'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: wordLimitController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: '字數上限（選填）',
                  hintText: '例如 1000',
                  prefixIcon: Icon(Icons.numbers_rounded),
                ),
              ),
              const SizedBox(height: 4),
              SwitchListTile.adaptive(
                contentPadding: EdgeInsets.zero,
                title: const Text('檢查簽名欄或簽署標記'),
                value: requireSignature,
                onChanged: (value) => setState(() => requireSignature = value),
              ),
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

class _DocumentCheckResultCard extends StatelessWidget {
  const _DocumentCheckResultCard({required this.result});

  final DocumentCheckResult result;

  @override
  Widget build(BuildContext context) {
    final hasErrors = result.issues.any((item) => item.severity == 'error');
    final hasWarnings = result.issues.any((item) => item.severity == 'warning');
    final statusLabel = hasErrors
        ? '需修正 ${result.issues.length} 項'
        : hasWarnings
        ? '待確認 ${result.issues.length} 項'
        : '規則檢查通過';
    final statusColor = hasErrors
        ? ExchangeColors.danger
        : hasWarnings
        ? ExchangeColors.amber
        : ExchangeColors.success;
    final statusBg = hasErrors
        ? ExchangeColors.coralSoft
        : hasWarnings
        ? ExchangeColors.amberSoft
        : ExchangeColors.successSoft;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const ExchangeSectionHeader(title: '檢查結果'),
        const SizedBox(height: 8),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      result.fileName,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: statusBg,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      statusLabel,
                      style: Theme.of(
                        context,
                      ).textTheme.labelMedium?.copyWith(color: statusColor),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: ExchangeColors.surfaceMuted,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: ExchangeColors.line),
                ),
                child: Wrap(
                  spacing: 16,
                  runSpacing: 8,
                  children: [
                    _MetricCell(label: '頁數', value: '${result.pageCount} 頁'),
                    _MetricCell(label: '字數', value: '${result.wordCount} 字'),
                    _MetricCell(
                      label: '字元數',
                      value: '${result.characterCount} 字元',
                    ),
                  ],
                ),
              ),
              if (result.summary.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(result.summary),
              ],
            ],
          ),
        ),
        if (result.issues.isNotEmpty) ...[
          const SizedBox(height: 8),
          GlassCard(
            padding: EdgeInsets.zero,
            child: ExpansionTile(
              initiallyExpanded: true,
              minTileHeight: 56,
              shape: const Border(),
              collapsedShape: const Border(),
              leading: const ExchangeIconBadge(
                Icons.warning_amber_rounded,
                color: ExchangeColors.amber,
                background: ExchangeColors.amberSoft,
              ),
              title: Text('待確認項目（${result.issues.length}）'),
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
              initiallyExpanded: result.issues.isEmpty,
              minTileHeight: 56,
              shape: const Border(),
              collapsedShape: const Border(),
              leading: const ExchangeIconBadge(
                Icons.checklist_rounded,
                color: ExchangeColors.success,
                background: ExchangeColors.successSoft,
              ),
              title: const Text('通過項目與格式提醒'),
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
              minTileHeight: 56,
              shape: const Border(),
              collapsedShape: const Border(),
              leading: const ExchangeIconBadge(Icons.preview_outlined),
              title: const Text('抽取文字預覽'),
              childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              children: [Text(result.extractedPreview)],
            ),
          ),
        ],
        if (result.privacyNote.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(
            result.privacyNote,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ],
    );
  }
}

class _MetricCell extends StatelessWidget {
  const _MetricCell({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(label, style: Theme.of(context).textTheme.labelSmall),
        const SizedBox(height: 2),
        Text(
          value,
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
            fontFeatures: ExchangeColors.tabularFigures,
          ),
        ),
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
      _ => ExchangeColors.actionBlue,
    };
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Icon(Icons.circle, size: 8, color: color),
          ),
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
