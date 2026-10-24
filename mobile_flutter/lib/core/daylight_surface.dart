import 'dart:ui';
import 'package:flutter/material.dart';
import 'exchange_theme.dart';

/// A quiet canvas leaves photos, deadlines and actions in the foreground.
class DaylightBackground extends StatelessWidget {
  const DaylightBackground({required this.child, super.key});
  final Widget child;
  @override
  Widget build(BuildContext context) =>
      ColoredBox(color: ExchangeColors.background, child: child);
}

/// Glass is reserved for navigation and primary controls, with opaque fallback.
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
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ImageFilter.blur(
          sigmaX: quiet || active ? 0 : 12,
          sigmaY: quiet || active ? 0 : 12,
        ),
        child: DecoratedBox(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(radius),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: disabled
                  ? [ExchangeColors.surfaceMuted, ExchangeColors.surfaceMuted]
                  : active
                  ? [ExchangeColors.teal, ExchangeColors.primaryEnd]
                  : [
                      Colors.white.withValues(alpha: quiet ? 1 : .96),
                      Colors.white.withValues(alpha: quiet ? 1 : .9),
                    ],
            ),
            border: Border.all(
              color: pressed
                  ? ExchangeColors.teal
                  : active
                  ? Colors.transparent
                  : ExchangeColors.line,
            ),
          ),
          child: child,
        ),
      ),
    );
  }
}
