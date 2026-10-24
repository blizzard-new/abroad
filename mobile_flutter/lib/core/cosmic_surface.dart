import 'dart:math' as math;
import 'dart:ui';
import 'package:flutter/material.dart';

/// Static stars avoid continuous GPU work while reading or filling a form.
class CosmicBackground extends StatelessWidget {
  const CosmicBackground({required this.child, super.key});
  final Widget child;
  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: const BoxDecoration(
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [Color(0xFF090F25), Color(0xFF171630), Color(0xFF080F20)],
      ),
    ),
    child: CustomPaint(
      painter: _CosmicPainter(quiet: MediaQuery.highContrastOf(context)),
      child: child,
    ),
  );
}

class _CosmicPainter extends CustomPainter {
  const _CosmicPainter({required this.quiet});
  final bool quiet;
  @override
  void paint(Canvas canvas, Size size) {
    if (quiet) return;
    final glow = Paint()
      ..shader =
          const RadialGradient(
            colors: [Color(0x403E6EB2), Color(0x005C4BAB)],
          ).createShader(
            Rect.fromCircle(
              center: Offset(size.width * .15, size.height * .24),
              radius: size.width * .9,
            ),
          );
    canvas.drawRect(Offset.zero & size, glow);
    glow.shader =
        const RadialGradient(
          colors: [Color(0x405E388E), Color(0x006A439C)],
        ).createShader(
          Rect.fromCircle(
            center: Offset(size.width, size.height * .7),
            radius: size.width,
          ),
        );
    canvas.drawRect(Offset.zero & size, glow);
    final random = math.Random(427);
    for (var i = 0; i < 100; i++) {
      final point = Offset(
        random.nextDouble() * size.width,
        random.nextDouble() * size.height,
      );
      final radius = i % 13 == 0 ? 1.35 : .55;
      final paint = Paint()
        ..color = Color(0xFFE1E8FF).withValues(alpha: i % 13 == 0 ? .58 : .18);
      canvas.drawCircle(point, radius, paint);
      if (i % 29 == 0) {
        paint.strokeWidth = .6;
        canvas.drawLine(
          point - const Offset(3, 0),
          point + const Offset(3, 0),
          paint,
        );
        canvas.drawLine(
          point - const Offset(0, 3),
          point + const Offset(0, 3),
          paint,
        );
      }
    }
  }

  @override
  bool shouldRepaint(_CosmicPainter oldDelegate) => quiet != oldDelegate.quiet;
}

/// One material for buttons and navigation; solid fallback for accessibility.
class LiquidControlSurface extends StatelessWidget {
  const LiquidControlSurface({
    required this.child,
    this.active = false,
    this.disabled = false,
    this.pressed = false,
    this.radius = 20,
    super.key,
  });
  final Widget child;
  final bool active, disabled, pressed;
  final double radius;
  @override
  Widget build(BuildContext context) {
    final quiet =
        MediaQuery.disableAnimationsOf(context) ||
        MediaQuery.highContrastOf(context);
    final shape = BorderRadius.circular(radius);
    return ClipRRect(
      borderRadius: shape,
      child: BackdropFilter(
        filter: ImageFilter.blur(
          sigmaX: quiet ? 0 : 12,
          sigmaY: quiet ? 0 : 12,
        ),
        child: DecoratedBox(
          decoration: BoxDecoration(
            borderRadius: shape,
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: disabled
                  ? const [Color(0xFF1C2540), Color(0xFF171F36)]
                  : active
                  ? [
                      Color(quiet ? 0xFF2D4869 : 0xCF344F73),
                      Color(quiet ? 0xFF383A67 : 0xD83A3B67),
                    ]
                  : [
                      Color(quiet ? 0xFF27314C : 0xB83E4766),
                      Color(quiet ? 0xFF1B2540 : 0xD31D2944),
                    ],
            ),
            border: Border.all(
              color: Colors.white.withValues(
                alpha: disabled ? .08 : (pressed ? .55 : .27),
              ),
              width: 1,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.white.withValues(alpha: .08),
                blurRadius: 2,
                offset: const Offset(0, -1),
              ),
            ],
          ),
          child: child,
        ),
      ),
    );
  }
}
