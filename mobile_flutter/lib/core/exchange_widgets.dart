import 'package:flutter/material.dart';

import 'exchange_theme.dart';
import 'daylight_surface.dart';

class ExchangePageBackground extends StatelessWidget {
  const ExchangePageBackground({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DaylightBackground(child: child);
  }
}

class GlassCard extends StatelessWidget {
  const GlassCard({
    required this.child,
    super.key,
    this.padding = const EdgeInsets.all(24),
    this.margin = EdgeInsets.zero,
    this.tint,
    this.onTap,
  });

  final Widget child;
  final EdgeInsets padding;
  final EdgeInsets margin;
  final Color? tint;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(24);
    return Padding(
      padding: margin,
      child: Semantics(
        button: onTap == null ? null : true,
        child: Material(
          color: tint ?? ExchangeColors.surface,
          shape: RoundedRectangleBorder(borderRadius: radius),
          clipBehavior: Clip.antiAlias,
          child: onTap == null
              ? Padding(padding: padding, child: child)
              : InkWell(
                  onTap: onTap,
                  borderRadius: radius,
                  child: Padding(padding: padding, child: child),
                ),
        ),
      ),
    );
  }
}

class ExchangeSectionHeader extends StatelessWidget {
  const ExchangeSectionHeader({
    required this.title,
    super.key,
    this.eyebrow,
    this.action,
  });

  final String title;
  final String? eyebrow;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (eyebrow != null) ...[
                Text(
                  eyebrow!,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: ExchangeColors.teal,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
              ],
              Text(title, style: Theme.of(context).textTheme.titleLarge),
            ],
          ),
        ),
        ?action,
      ],
    );
  }
}

class ExchangeIconBadge extends StatelessWidget {
  const ExchangeIconBadge(
    this.icon, {
    super.key,
    this.color = ExchangeColors.teal,
    this.background = ExchangeColors.tealSoft,
  });

  final IconData icon;
  final Color color;
  final Color background;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 44,
      height: 44,
      alignment: Alignment.center,
      decoration: BoxDecoration(color: background, shape: BoxShape.circle),
      child: Icon(icon, color: color, size: 22),
    );
  }
}

class FieldHelpButton extends StatelessWidget {
  const FieldHelpButton({
    required this.title,
    required this.message,
    super.key,
  });

  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: '$title 填寫提示',
      constraints: const BoxConstraints.tightFor(width: 48, height: 48),
      onPressed: () => showModalBottomSheet<void>(
        context: context,
        showDragHandle: true,
        useSafeArea: true,
        builder: (sheetContext) => Padding(
          padding: const EdgeInsets.fromLTRB(24, 4, 24, 28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const ExchangeIconBadge(Icons.help_outline_rounded),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      title,
                      style: Theme.of(sheetContext).textTheme.titleLarge,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Text(message),
            ],
          ),
        ),
      ),
      icon: const Icon(Icons.help_outline_rounded, size: 20),
    );
  }
}

class BulletPoint extends StatelessWidget {
  const BulletPoint(this.text, {super.key, this.strong = false});

  final String text;
  final bool strong;

  @override
  Widget build(BuildContext context) {
    final displayText = studentFacingText(text);
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 6,
            height: 6,
            margin: const EdgeInsets.only(top: 9, right: 11),
            decoration: const BoxDecoration(
              color: ExchangeColors.teal,
              shape: BoxShape.circle,
            ),
          ),
          Expanded(
            child: Text(
              displayText,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: strong ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

String studentFacingText(String value) {
  var text = value.trim();
  text = text.replaceAll(
    RegExp(r'https?://[^\s\uff09)]+', caseSensitive: false),
    '',
  );
  text = text.replaceAll(RegExp(r'\(\s*\)'), '');
  text = text.replaceAll('Option A Entry Requirements:', '方案 A 語言門檻：');
  text = text.replaceAll('Option B Entry Requirements:', '方案 B 語言門檻：');
  text = text.replaceAllMapped(
    RegExp(
      r'IELTS\s*([\d.]+)\s*overall,?\s*with no individual band less than\s*([\d.]+)\s*or equivalent\.?',
      caseSensitive: false,
    ),
    (match) => 'IELTS 總分 ${match.group(1)}，各單項不得低於 ${match.group(2)}（或同等成績）。',
  );
  text = text.replaceAllMapped(
    RegExp(
      r'Study Content:\s*(\d+)\s*or\s*(\d+)\s*courses?\s*in undergraduate level\s*\(100 level recommended\)',
      caseSensitive: false,
    ),
    (match) =>
        '修課要求：選修 ${match.group(1)} 至 ${match.group(2)} 門大學部課程，建議以 100 級課程為主。',
  );
  text = text.replaceAll(
    RegExp(r'B1 in French or English', caseSensitive: false),
    '法文或英文須達 CEFR B1',
  );
  text = text.replaceAll(
    RegExp(r'\(European level\s*\)', caseSensitive: false),
    '（CEFR 歐洲語言分級）',
  );
  text = text.replaceAll(RegExp(r'\s+'), ' ').trim();
  return text;
}

class LoadingCards extends StatelessWidget {
  const LoadingCards({super.key, this.count = 4});

  final int count;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: List.generate(
        count,
        (index) => Container(
          height: index == 0 ? 132 : 104,
          margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
            color: ExchangeColors.surface,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: ExchangeColors.line),
          ),
          child: const Center(
            child: SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2.4),
            ),
          ),
        ),
      ),
    );
  }
}

class EmptyState extends StatelessWidget {
  const EmptyState({
    required this.icon,
    required this.title,
    required this.message,
    super.key,
  });

  final IconData icon;
  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        children: [
          ExchangeIconBadge(icon),
          const SizedBox(height: 14),
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 6),
          Text(
            message,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

class InlineError extends StatelessWidget {
  const InlineError({required this.message, required this.onRetry, super.key});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      tint: ExchangeColors.coralSoft.withValues(alpha: .78),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline_rounded, color: ExchangeColors.danger),
          const SizedBox(width: 12),
          Expanded(child: Text(message)),
          IconButton(
            tooltip: '重新載入',
            onPressed: onRetry,
            constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
    );
  }
}
