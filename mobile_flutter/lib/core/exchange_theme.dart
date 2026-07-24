import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

abstract final class ExchangeColors {
  static const background = Color(0xFFF5F7F8);
  static const surface = Color(0xF2FFFFFF);
  static const surfaceMuted = Color(0xD9FFFFFF);
  static const ink = Color(0xFF15212C);
  static const secondaryInk = Color(0xFF596875);
  static const line = Color(0x1F29404F);
  static const teal = Color(0xFF087C8C);
  static const tealSoft = Color(0xFFD9F0F1);
  static const blue = Color(0xFF197DB3);
  static const blueSoft = Color(0xFFDCECF7);
  static const coral = Color(0xFFD97761);
  static const coralSoft = Color(0xFFF7E2DC);
  static const amber = Color(0xFFB97822);
  static const amberSoft = Color(0xFFF7EACF);
  static const success = Color(0xFF24835B);
  static const danger = Color(0xFFC44747);
}

ThemeData buildExchangeTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: ExchangeColors.teal,
    brightness: Brightness.light,
    primary: ExchangeColors.teal,
    surface: ExchangeColors.surface,
    onSurface: ExchangeColors.ink,
    error: ExchangeColors.danger,
  );

  final base = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: scheme,
    scaffoldBackgroundColor: Colors.transparent,
  );

  return base.copyWith(
    textTheme: base.textTheme.copyWith(
      displaySmall: const TextStyle(
        fontSize: 32,
        height: 1.15,
        fontWeight: FontWeight.w700,
        color: ExchangeColors.ink,
      ),
      headlineMedium: const TextStyle(
        fontSize: 24,
        height: 1.2,
        fontWeight: FontWeight.w700,
        color: ExchangeColors.ink,
      ),
      titleLarge: const TextStyle(
        fontSize: 20,
        height: 1.3,
        fontWeight: FontWeight.w700,
        color: ExchangeColors.ink,
      ),
      titleMedium: const TextStyle(
        fontSize: 17,
        height: 1.35,
        fontWeight: FontWeight.w600,
        color: ExchangeColors.ink,
      ),
      bodyLarge: const TextStyle(
        fontSize: 16,
        height: 1.65,
        color: ExchangeColors.ink,
      ),
      bodyMedium: const TextStyle(
        fontSize: 15,
        height: 1.55,
        color: ExchangeColors.ink,
      ),
      bodySmall: const TextStyle(
        fontSize: 13,
        height: 1.45,
        color: ExchangeColors.secondaryInk,
      ),
      labelLarge: const TextStyle(
        fontSize: 15,
        height: 1.2,
        fontWeight: FontWeight.w600,
      ),
    ),
    cardTheme: const CardThemeData(
      elevation: 0,
      color: Colors.transparent,
      margin: EdgeInsets.zero,
    ),
    dividerTheme: const DividerThemeData(
      color: ExchangeColors.line,
      thickness: 1,
      space: 1,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: const Color(0x8FFFFFFF),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      constraints: const BoxConstraints(minHeight: 48),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xD9FFFFFF)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xD9FFFFFF)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: ExchangeColors.teal, width: 1.4),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: ButtonStyle(
        minimumSize: const WidgetStatePropertyAll(Size(44, 48)),
        foregroundColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.disabled)
              ? ExchangeColors.secondaryInk
              : Colors.white,
        ),
        backgroundColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.disabled)) {
            return Colors.white.withValues(alpha: .32);
          }
          if (states.contains(WidgetState.pressed)) {
            return ExchangeColors.ink.withValues(alpha: .88);
          }
          return ExchangeColors.ink.withValues(alpha: .94);
        }),
        overlayColor: WidgetStatePropertyAll(
          Colors.white.withValues(alpha: .12),
        ),
        side: WidgetStatePropertyAll(
          BorderSide(color: Colors.white.withValues(alpha: .24)),
        ),
        elevation: const WidgetStatePropertyAll(0),
        shadowColor: WidgetStatePropertyAll(
          ExchangeColors.ink.withValues(alpha: .16),
        ),
        shape: WidgetStatePropertyAll(
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
        textStyle: const WidgetStatePropertyAll(
          TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: ButtonStyle(
        minimumSize: const WidgetStatePropertyAll(Size(44, 48)),
        foregroundColor: const WidgetStatePropertyAll(ExchangeColors.teal),
        backgroundColor: WidgetStateProperty.resolveWith(
          (states) => Colors.white.withValues(
            alpha: states.contains(WidgetState.pressed) ? .68 : .46,
          ),
        ),
        overlayColor: WidgetStatePropertyAll(
          ExchangeColors.teal.withValues(alpha: .07),
        ),
        side: WidgetStatePropertyAll(
          BorderSide(color: Colors.white.withValues(alpha: .88)),
        ),
        elevation: const WidgetStatePropertyAll(0),
        shape: WidgetStatePropertyAll(
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: ButtonStyle(
        minimumSize: const WidgetStatePropertyAll(Size(44, 44)),
        foregroundColor: const WidgetStatePropertyAll(ExchangeColors.teal),
        overlayColor: WidgetStatePropertyAll(
          ExchangeColors.teal.withValues(alpha: .08),
        ),
        shape: WidgetStatePropertyAll(
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: ButtonStyle(
        minimumSize: const WidgetStatePropertyAll(Size(44, 44)),
        foregroundColor: const WidgetStatePropertyAll(
          ExchangeColors.secondaryInk,
        ),
        backgroundColor: WidgetStateProperty.resolveWith(
          (states) => Colors.white.withValues(
            alpha: states.contains(WidgetState.pressed) ? .72 : .44,
          ),
        ),
        overlayColor: WidgetStatePropertyAll(
          ExchangeColors.teal.withValues(alpha: .08),
        ),
        side: WidgetStatePropertyAll(
          BorderSide(color: Colors.white.withValues(alpha: .82)),
        ),
        shape: const WidgetStatePropertyAll(CircleBorder()),
      ),
    ),
    chipTheme: base.chipTheme.copyWith(
      backgroundColor: Colors.white.withValues(alpha: .44),
      selectedColor: ExchangeColors.tealSoft.withValues(alpha: .76),
      disabledColor: Colors.white.withValues(alpha: .24),
      side: BorderSide(color: Colors.white.withValues(alpha: .84)),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
      labelStyle: const TextStyle(
        color: ExchangeColors.ink,
        fontWeight: FontWeight.w600,
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      height: 68,
      backgroundColor: Colors.transparent,
      indicatorColor: ExchangeColors.tealSoft,
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          fontSize: 12,
          fontWeight: states.contains(WidgetState.selected)
              ? FontWeight.w700
              : FontWeight.w500,
          color: states.contains(WidgetState.selected)
              ? ExchangeColors.teal
              : ExchangeColors.secondaryInk,
        ),
      ),
    ),
    cupertinoOverrideTheme: const CupertinoThemeData(
      primaryColor: ExchangeColors.teal,
      scaffoldBackgroundColor: ExchangeColors.background,
      barBackgroundColor: Color(0xE6F3F7FA),
      textTheme: CupertinoTextThemeData(
        textStyle: TextStyle(color: ExchangeColors.ink, fontSize: 16),
      ),
    ),
  );
}
