import 'package:flutter/material.dart';
import 'exchange_theme.dart';

class DaylightBackground extends StatelessWidget {
  const DaylightBackground({required this.child, super.key});
  final Widget child;
  @override
  Widget build(BuildContext context) =>
      ColoredBox(color: ExchangeColors.background, child: child);
}

class LiquidControlSurface extends StatelessWidget {
  const LiquidControlSurface({
    required this.child,
    this.active = false,
    this.disabled = false,
    this.pressed = false,
    this.radius = 12,
    super.key,
  });
  final Widget child;
  final bool active, disabled, pressed;
  final double radius;
  @override
  Widget build(BuildContext context) => AnimatedContainer(
    duration: Duration(
      milliseconds: MediaQuery.disableAnimationsOf(context) ? 0 : 120,
    ),
    decoration: BoxDecoration(
      color: disabled
          ? ExchangeColors.surfaceMuted
          : active
          ? (pressed ? ExchangeColors.primaryEnd : ExchangeColors.actionBlue)
          : (pressed ? ExchangeColors.surfaceMuted : ExchangeColors.surface),
      borderRadius: BorderRadius.circular(radius),
      border: active
          ? null
          : Border.all(
              color: disabled ? ExchangeColors.line : ExchangeColors.line,
            ),
    ),
    child: child,
  );
}
