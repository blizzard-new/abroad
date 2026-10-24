import 'package:flutter/material.dart';
import 'exchange_theme.dart';
import 'exchange_widgets.dart';

/// Compact, labelled controls: icons support the copy rather than replace it.
class StudentHeading extends StatelessWidget {
  const StudentHeading(this.title, {this.subtitle, this.action, super.key});
  final String title;
  final String? subtitle;
  final Widget? action;
  @override
  Widget build(BuildContext context) => Row(
    children: [
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.headlineMedium),
            if (subtitle != null) ...[
              const SizedBox(height: 4),
              Text(subtitle!, style: Theme.of(context).textTheme.bodySmall),
            ],
          ],
        ),
      ),
      ?action,
    ],
  );
}

class StudentAction {
  const StudentAction(
    this.icon,
    this.label,
    this.onTap, {
    this.detail,
    this.color = ExchangeColors.teal,
  });
  final IconData icon;
  final String label;
  final String? detail;
  final VoidCallback onTap;
  final Color color;
}

class StudentActionGrid extends StatelessWidget {
  const StudentActionGrid(this.actions, {super.key});
  final List<StudentAction> actions;
  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final columns = constraints.maxWidth >= 600 ? 3 : 2;
      final width = (constraints.maxWidth - 12 * (columns - 1)) / columns;
      return Wrap(
        spacing: 12,
        runSpacing: 12,
        children: actions
            .map(
              (action) => SizedBox(
                width: width,
                child: GlassCard(
                  onTap: action.onTap,
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      ExchangeIconBadge(
                        action.icon,
                        color: action.color,
                        background: action.color.withValues(alpha: .08),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        action.label,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      if (action.detail != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          action.detail!,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            )
            .toList(),
      );
    },
  );
}

class StudentActionRow extends StatelessWidget {
  const StudentActionRow({
    required this.icon,
    required this.title,
    required this.onTap,
    this.detail,
    this.leading,
    super.key,
  });
  final IconData icon;
  final String title;
  final String? detail;
  final Widget? leading;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Semantics(
    button: true,
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Row(
          children: [
            leading ?? ExchangeIconBadge(icon),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleMedium),
                  if (detail != null) ...[
                    const SizedBox(height: 4),
                    Text(detail!, style: Theme.of(context).textTheme.bodySmall),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),
            const Icon(Icons.chevron_right_rounded, size: 20),
          ],
        ),
      ),
    ),
  );
}

class StudentIconLabel extends StatelessWidget {
  const StudentIconLabel(
    this.icon,
    this.label, {
    this.color = ExchangeColors.secondaryInk,
    super.key,
  });
  final IconData icon;
  final String label;
  final Color color;
  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Icon(icon, size: 16, color: color),
      const SizedBox(width: 8),
      Flexible(
        child: Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: color),
        ),
      ),
    ],
  );
}

class StudentEmptyState extends StatelessWidget {
  const StudentEmptyState({
    required this.icon,
    required this.title,
    this.detail,
    this.action,
    super.key,
  });
  final IconData icon;
  final String title;
  final String? detail;
  final Widget? action;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 32),
    child: Column(
      children: [
        Container(
          padding: const EdgeInsets.all(24),
          decoration: const BoxDecoration(
            color: ExchangeColors.tealSoft,
            shape: BoxShape.circle,
          ),
          child: Icon(icon, size: 32, color: ExchangeColors.teal),
        ),
        const SizedBox(height: 16),
        Text(
          title,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.titleMedium,
        ),
        if (detail != null) ...[
          const SizedBox(height: 8),
          Text(
            detail!,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
        if (action != null) ...[const SizedBox(height: 16), action!],
      ],
    ),
  );
}

typedef StudentGuideStep = ({IconData icon, String title, String detail});

Future<void> showStudentGuide(
  BuildContext context, {
  String title = '怎麼開始？',
  required List<StudentGuideStep> steps,
}) => showModalBottomSheet<void>(
  context: context,
  useSafeArea: true,
  showDragHandle: true,
  isScrollControlled: true,
  builder: (context) => ConstrainedBox(
    constraints: BoxConstraints(
      maxHeight: MediaQuery.sizeOf(context).height * .8,
    ),
    child: SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(title, style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 24),
          ...steps.indexed.map(
            (entry) => Padding(
              padding: const EdgeInsets.only(bottom: 24),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ExchangeIconBadge(entry.$2.icon),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${entry.$1 + 1}. ${entry.$2.title}',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 8),
                        Text(entry.$2.detail),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('開始吧'),
          ),
        ],
      ),
    ),
  ),
);

const journeyGuide = <StudentGuideStep>[
  (
    icon: Icons.travel_explore_rounded,
    title: '找到學校',
    detail: '選就讀大學，搜尋合作校，再點書籤收藏志願。',
  ),
  (
    icon: Icons.assignment_outlined,
    title: '準備文件',
    detail: '到「申請」設定目標、填寫資料，逐項完成文件。',
  ),
  (icon: Icons.event_outlined, title: '安排時程', detail: '加入確認過的截止日，再到通知頁開啟提醒。'),
];
