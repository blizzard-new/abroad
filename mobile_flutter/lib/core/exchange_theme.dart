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
  TextStyle type(double size, {bool strong = false, bool secondary = false}) =>
      TextStyle(
        fontSize: size,
        height: 1.4,
        fontWeight: strong ? FontWeight.w600 : FontWeight.w400,
        color: secondary ? ExchangeColors.secondaryInk : ExchangeColors.ink,
      );
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
    textTheme: TextTheme(
      displayLarge: type(24, strong: true),
      displayMedium: type(24, strong: true),
      displaySmall: type(24, strong: true),
      headlineLarge: type(24, strong: true),
      headlineMedium: type(24, strong: true),
      headlineSmall: type(24, strong: true),
      titleLarge: type(20, strong: true),
      titleMedium: type(16, strong: true),
      titleSmall: type(16, strong: true),
      bodyLarge: type(16),
      bodyMedium: type(16),
      bodySmall: type(12, secondary: true),
      labelLarge: type(16, strong: true),
      labelMedium: type(12, strong: true),
      labelSmall: type(12),
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: ExchangeColors.background,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: type(20, strong: true),
    ),
    dialogTheme: DialogThemeData(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      backgroundColor: ExchangeColors.background,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
    ),
    expansionTileTheme: const ExpansionTileThemeData(
      shape: Border(),
      collapsedShape: Border(),
      iconColor: ExchangeColors.teal,
      textColor: ExchangeColors.ink,
      collapsedTextColor: ExchangeColors.ink,
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
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      constraints: const BoxConstraints(minHeight: 48),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0xD9FFFFFF)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0xD9FFFFFF)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
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
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        textStyle: const WidgetStatePropertyAll(
          TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
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
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
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
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
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
              ? FontWeight.w600
              : FontWeight.w400,
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
