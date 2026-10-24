import 'dart:ui';

import 'package:flutter/material.dart';

import 'exchange_theme.dart';

class ExchangePageBackground extends StatelessWidget {
  const ExchangePageBackground({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFAFBFC), Color(0xFFF1F5F6), Color(0xFFF7F4F6)],
          stops: [0, .62, 1],
        ),
      ),
      child: child,
    );
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
    final glassDecoration = BoxDecoration(
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: tint == null
            ? [
                Colors.white.withValues(alpha: .86),
                const Color(0xFFF6F9FA).withValues(alpha: .64),
                Colors.white.withValues(alpha: .58),
              ]
            : [
                tint!.withValues(alpha: .82),
                tint!.withValues(alpha: .6),
                Colors.white.withValues(alpha: .48),
              ],
        stops: const [0, .52, 1],
      ),
      borderRadius: radius,
      border: Border.all(color: Colors.white.withValues(alpha: .94)),
    );
    final surface = Material(
      color: Colors.transparent,
      child: Ink(
        decoration: glassDecoration,
        child: onTap == null
            ? Padding(padding: padding, child: child)
            : InkWell(
                borderRadius: radius,
                onTap: onTap,
                splashColor: ExchangeColors.teal.withValues(alpha: .08),
                highlightColor: Colors.white.withValues(alpha: .12),
                child: Padding(padding: padding, child: child),
              ),
      ),
    );
    final content = Container(
      decoration: BoxDecoration(
        borderRadius: radius,
        boxShadow: const [
          BoxShadow(
            color: Color(0x14132231),
            blurRadius: 30,
            spreadRadius: -8,
            offset: Offset(0, 14),
          ),
          BoxShadow(
            color: Color(0xA6FFFFFF),
            blurRadius: 7,
            spreadRadius: -4,
            offset: Offset(0, -2),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: radius,
        child: BackdropFilter(
          filter: ImageFilter.blur(
            sigmaX:
                MediaQuery.disableAnimationsOf(context) ||
                    MediaQuery.highContrastOf(context)
                ? 0
                : 16,
            sigmaY:
                MediaQuery.disableAnimationsOf(context) ||
                    MediaQuery.highContrastOf(context)
                ? 0
                : 16,
          ),
          child: surface,
        ),
      ),
    );

    return Padding(
      padding: margin,
      child: onTap == null ? content : Semantics(button: true, child: content),
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
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
              ],
              Text(title, style: Theme.of(context).textTheme.headlineMedium),
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
                fontWeight: strong ? FontWeight.w700 : FontWeight.w500,
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
            color: Colors.white.withValues(alpha: .62),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.white),
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
