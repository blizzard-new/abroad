import 'package:flutter/material.dart';
import '../core/exchange_theme.dart';
import '../core/study_plan_widget_service.dart';

class WidgetStylePreview extends StatelessWidget {
  const WidgetStylePreview({
    required this.style,
    required this.title,
    required this.dateLabel,
    required this.percent,
    required this.tasks,
    this.deadline,
    super.key,
  });
  final StudyPlanWidgetStyle style;
  final String title, dateLabel;
  final int percent;
  final List<String> tasks;
  final DateTime? deadline;

  static IconData icon(StudyPlanWidgetStyle style) => switch (style) {
    StudyPlanWidgetStyle.overview => Icons.flight_takeoff_rounded,
    StudyPlanWidgetStyle.countdown => Icons.auto_awesome_outlined,
    StudyPlanWidgetStyle.checklist => Icons.checklist_rounded,
    StudyPlanWidgetStyle.progress => Icons.donut_large_rounded,
  };
  @override
  Widget build(BuildContext context) {
    final accent = switch (style) {
      StudyPlanWidgetStyle.countdown => const Color(0xFFD1B7FF),
      StudyPlanWidgetStyle.checklist => const Color(0xFF8BE8CE),
      _ => const Color(0xFF9AC9FF),
    };
    final now = DateTime.now();
    final days = deadline == null
        ? null
        : DateTime.utc(
            deadline!.year,
            deadline!.month,
            deadline!.day,
          ).difference(DateTime.utc(now.year, now.month, now.day)).inDays;
    return Container(
      key: ValueKey('widget-preview-${style.name}'),
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color.alphaBlend(
              accent.withValues(alpha: .16),
              ExchangeColors.background,
            ),
            ExchangeColors.background,
          ],
        ),
        border: Border.all(color: accent.withValues(alpha: .4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon(style), color: accent, size: 20),
              const SizedBox(width: 8),
              Text(style.label, style: TextStyle(color: accent, fontSize: 12)),
            ],
          ),
          const SizedBox(height: 20),
          if (style == StudyPlanWidgetStyle.countdown && days != null) ...[
            Text(
              days < 0
                  ? '期限已過'
                  : days == 0
                  ? '今天'
                  : '$days 天後',
              style: Theme.of(context).textTheme.headlineLarge,
            ),
            const SizedBox(height: 8),
            Text(title),
          ] else if (style == StudyPlanWidgetStyle.checklist &&
              tasks.isNotEmpty)
            ...tasks
                .take(3)
                .map(
                  (task) => Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      children: [
                        Icon(
                          Icons.radio_button_unchecked,
                          size: 16,
                          color: accent,
                        ),
                        const SizedBox(width: 8),
                        Expanded(child: Text(task)),
                      ],
                    ),
                  ),
                )
          else if (style == StudyPlanWidgetStyle.progress)
            Row(
              children: [
                SizedBox.square(
                  dimension: 72,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      SizedBox.expand(
                        child: CircularProgressIndicator(
                          value: percent.clamp(0, 100) / 100,
                          strokeWidth: 6,
                          backgroundColor: accent.withValues(alpha: .15),
                          color: accent,
                        ),
                      ),
                      Text(
                        '$percent%',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 20),
                Expanded(child: Text(title)),
              ],
            )
          else ...[
            Text(title, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(dateLabel, style: Theme.of(context).textTheme.bodySmall),
          ],
          const SizedBox(height: 20),
          Text('點一下回到 UniWay', style: TextStyle(color: accent, fontSize: 12)),
        ],
      ),
    );
  }
}
