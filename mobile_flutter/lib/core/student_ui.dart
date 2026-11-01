import 'package:flutter/material.dart';
import 'exchange_theme.dart';
import 'exchange_widgets.dart';
import 'uniway_brand.dart';

/// A shared reading width and action area for every secondary destination.
class StudentPage extends StatelessWidget {
  const StudentPage({
    required this.title,
    required this.children,
    this.onRefresh,
    this.actions,
    this.bottomBar,
    this.leading,
    this.retainChildren = false,
    super.key,
  });
  final String title;
  final List<Widget> children;
  final Future<void> Function()? onRefresh;
  final List<Widget>? actions;
  final Widget? bottomBar;
  final Widget? leading;
  final bool retainChildren;

  @override
  Widget build(BuildContext context) {
    final list = LayoutBuilder(
      builder: (context, constraints) {
        final padding = EdgeInsets.fromLTRB(
          constraints.maxWidth > 640 ? (constraints.maxWidth - 600) / 2 : 20,
          16,
          constraints.maxWidth > 640 ? (constraints.maxWidth - 600) / 2 : 20,
          32,
        );
        // Form validation must still see fields after scrolling to the print guide.
        if (retainChildren) {
          return SingleChildScrollView(
            keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
            physics: const AlwaysScrollableScrollPhysics(),
            padding: padding,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: children,
            ),
          );
        }
        return ListView(
          keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
          physics: const AlwaysScrollableScrollPhysics(),
          padding: padding,
          children: children,
        );
      },
    );
    return ExchangePageBackground(
      child: Scaffold(
        appBar: AppBar(
          toolbarHeight: MediaQuery.textScalerOf(context).scale(20) > 28
              ? 88
              : 60,
          title: Text(title, maxLines: 2, overflow: TextOverflow.ellipsis),
          leading:
              leading ??
              IconButton(
                tooltip: '返回',
                onPressed: () => Navigator.of(context).maybePop(),
                icon: const Icon(Icons.arrow_back_rounded),
              ),
          actions: actions,
        ),
        body: SafeArea(
          top: false,
          child: onRefresh == null
              ? list
              : RefreshIndicator(onRefresh: onRefresh!, child: list),
        ),
        bottomNavigationBar: bottomBar,
      ),
    );
  }
}

class StudentActionBar extends StatelessWidget {
  const StudentActionBar({required this.primary, this.secondary, super.key});
  final Widget primary;
  final Widget? secondary;
  @override
  Widget build(BuildContext context) => Material(
    color: Theme.of(context).colorScheme.surface,
    child: SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 12),
        child: Center(
          heightFactor: 1,
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 600),
            child: LayoutBuilder(
              builder: (context, constraints) {
                if (secondary == null) {
                  return SizedBox(width: double.infinity, child: primary);
                }
                if (constraints.maxWidth < 320 ||
                    MediaQuery.textScalerOf(context).scale(16) > 24) {
                  return Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [primary, const SizedBox(height: 8), secondary!],
                  );
                }
                return Row(
                  children: [
                    Expanded(child: secondary!),
                    const SizedBox(width: 12),
                    Expanded(child: primary),
                  ],
                );
              },
            ),
          ),
        ),
      ),
    ),
  );
}

class StudentSectionTitle extends StatelessWidget {
  const StudentSectionTitle(
    this.title, {
    required this.icon,
    this.detail,
    super.key,
  });
  final String title;
  final IconData icon;
  final String? detail;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 8, bottom: 16),
    child: Row(
      children: [
        Icon(icon, color: ExchangeColors.teal, size: 24),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: Theme.of(context).textTheme.titleMedium),
              if (detail != null)
                Text(detail!, style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
        ),
      ],
    ),
  );
}

/// Keep important limits visible; optional detail is a labelled help action.
class StudentNotice extends StatelessWidget {
  const StudentNotice(
    this.text, {
    this.icon = Icons.info_outline_rounded,
    this.detail,
    this.color = ExchangeColors.teal,
    super.key,
  });
  final String text;
  final IconData icon;
  final String? detail;
  final Color color;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: color.withValues(alpha: .06),
      borderRadius: BorderRadius.circular(16),
    ),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(width: 12),
        Expanded(
          child: Text(text, style: Theme.of(context).textTheme.bodySmall),
        ),
        if (detail != null) FieldHelpButton(title: text, message: detail!),
      ],
    ),
  );
}

class StudentSummaryCard extends StatelessWidget {
  const StudentSummaryCard({
    required this.icon,
    required this.title,
    this.detail,
    super.key,
  });
  final IconData icon;
  final String title;
  final String? detail;
  @override
  Widget build(BuildContext context) => GlassCard(
    tint: ExchangeColors.tealSoft,
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ExchangeIconBadge(icon, background: Colors.white),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: Theme.of(context).textTheme.titleLarge),
              if (detail != null) ...[
                const SizedBox(height: 8),
                Text(detail!, style: Theme.of(context).textTheme.bodySmall),
              ],
            ],
          ),
        ),
      ],
    ),
  );
}

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
            Text(title, style: Theme.of(context).textTheme.headlineSmall),
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
        const UniWayMascot(size: 88),
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
          Text(title, style: Theme.of(context).textTheme.headlineSmall),
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
