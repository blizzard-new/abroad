import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'exchange_theme.dart';

/// The platform's own mark replaces generic framework/compass artwork.
class UniWayLogo extends StatelessWidget {
  const UniWayLogo({this.size = 36, this.wordmark = false, super.key});
  final double size;
  final bool wordmark;
  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Image.asset(
        'assets/brand/uniway-mark.webp',
        width: size,
        height: size,
        fit: BoxFit.contain,
        semanticLabel: 'UniWay',
      ),
      if (wordmark) ...[
        const SizedBox(width: 8),
        const Flexible(
          child: FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(
              'UniWay',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w700,
                letterSpacing: -1,
                color: ExchangeColors.ink,
              ),
            ),
          ),
        ),
      ],
    ],
  );
}

/// Same suitcase and measured eye positions as the website, without a video asset.
/// Motion is finite and respects reduced motion and offstage TickerMode.
class UniWayMascot extends StatefulWidget {
  const UniWayMascot({this.size = 120, this.animate = true, super.key});
  final double size;
  final bool animate;
  @override
  State<UniWayMascot> createState() => _UniWayMascotState();
}

class _UniWayMascotState extends State<UniWayMascot>
    with SingleTickerProviderStateMixin {
  late final controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1800),
  );
  bool started = false;
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.disableAnimationsOf(context)) {
      controller.stop();
      controller.value = 1;
    } else if (!started &&
        widget.animate &&
        TickerMode.valuesOf(context).enabled) {
      started = true;
      controller.forward();
    }
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final height = widget.size * 460 / 384;
    return Semantics(
      image: true,
      label: 'UniWay 行李箱吉祥物',
      child: RepaintBoundary(
        child: AnimatedBuilder(
          animation: controller,
          builder: (context, child) {
            final t = controller.value;
            final lift = math.sin(t * math.pi * 2) * 5 * (1 - t);
            final blink = t > .43 && t < .57 ? .16 : 1.0;
            Widget eye(double left, double top) => Positioned(
              left: widget.size * left,
              top: height * top,
              child: Transform.rotate(
                angle: .16,
                child: Transform.scale(
                  scaleY: blink,
                  child: Container(
                    width: widget.size * .0854,
                    height: height * .124,
                    decoration: BoxDecoration(
                      color: Color(0xFF2C2C2F),
                      borderRadius: BorderRadius.circular(50),
                    ),
                  ),
                ),
              ),
            );
            return Transform.translate(
              offset: Offset(0, -lift),
              child: SizedBox(
                width: widget.size,
                height: height,
                child: Stack(
                  children: [
                    Positioned.fill(
                      child: Image.asset(
                        'assets/brand/suitcase.webp',
                        excludeFromSemantics: true,
                      ),
                    ),
                    eye(.37011, .46830),
                    eye(.61052, .48873),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class UniWayProgress extends StatelessWidget {
  const UniWayProgress({
    required this.value,
    required this.label,
    this.color = ExchangeColors.teal,
    super.key,
  });
  final double value;
  final String label;
  final Color color;
  @override
  Widget build(BuildContext context) => TweenAnimationBuilder<double>(
    tween: Tween(begin: 0, end: value.clamp(0, 1)),
    duration: Duration(
      milliseconds: MediaQuery.disableAnimationsOf(context) ? 0 : 650,
    ),
    curve: Curves.easeOutCubic,
    builder: (context, progress, _) => LinearProgressIndicator(
      value: progress,
      minHeight: 10,
      borderRadius: BorderRadius.circular(20),
      color: color,
      backgroundColor: ExchangeColors.surfaceMuted,
      semanticsLabel: label,
      semanticsValue: '${(value * 100).round()}%',
    ),
  );
}

class UniWayPill extends StatelessWidget {
  const UniWayPill(
    this.text, {
    this.icon,
    this.color = ExchangeColors.teal,
    this.background = ExchangeColors.tealSoft,
    super.key,
  });
  final String text;
  final IconData? icon;
  final Color color, background;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
    decoration: BoxDecoration(
      color: background,
      borderRadius: BorderRadius.circular(12),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (icon != null) ...[
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 6),
        ],
        Flexible(
          child: Text(
            text,
            style: Theme.of(
              context,
            ).textTheme.labelMedium?.copyWith(color: color),
          ),
        ),
      ],
    ),
  );
}
