import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'cosmic_surface.dart';

abstract final class ExchangeColors {
  static const background = Color(0xFF0B1228);
  static const surface = Color(0xFF18213B);
  static const surfaceMuted = Color(0xE61C2843);
  static const ink = Color(0xFFF1F4FF);
  static const secondaryInk = Color(0xFFB7C3DB);
  static const line = Color(0x338CA1CC);
  static const teal = Color(0xFF92E4E9);
  static const tealSoft = Color(0xFF253F55);
  static const blue = Color(0xFFA7C9FF);
  static const blueSoft = Color(0xFF293758);
  static const coral = Color(0xFFFFBDAA);
  static const coralSoft = Color(0xFF4B3044);
  static const amber = Color(0xFFF3D292);
  static const amberSoft = Color(0xFF453B38);
  static const success = Color(0xFF8AE0B8);
  static const danger = Color(0xFFFFA9B0);
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
    brightness: Brightness.dark,
    primary: ExchangeColors.teal,
    surface: ExchangeColors.surface,
    onSurface: ExchangeColors.ink,
    error: ExchangeColors.danger,
  );

  final base = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
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
      backgroundColor: ExchangeColors.background.withValues(alpha: .88),
      systemOverlayStyle: SystemUiOverlayStyle.light,
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
      fillColor: const Color(0xBB26334F),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      constraints: const BoxConstraints(minHeight: 48),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: ExchangeColors.line),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: ExchangeColors.line),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: ExchangeColors.teal, width: 1.4),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: _liquidStyle(primary: true),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(style: _liquidStyle()),
    textButtonTheme: TextButtonThemeData(style: _liquidStyle()),
    iconButtonTheme: IconButtonThemeData(style: _liquidStyle(round: true)),
    chipTheme: base.chipTheme.copyWith(
      backgroundColor: ExchangeColors.surfaceMuted,
      selectedColor: ExchangeColors.tealSoft.withValues(alpha: .76),
      disabledColor: ExchangeColors.surface,
      side: BorderSide(color: ExchangeColors.line),
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
      barBackgroundColor: Color(0xE618213B),
      textTheme: CupertinoTextThemeData(
        textStyle: TextStyle(color: ExchangeColors.ink, fontSize: 16),
      ),
    ),
  );
}

ButtonStyle _liquidStyle({bool primary = false, bool round = false}) =>
    ButtonStyle(
      minimumSize: WidgetStatePropertyAll(Size(44, round ? 44 : 48)),
      foregroundColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.disabled)
            ? ExchangeColors.secondaryInk.withValues(alpha: .5)
            : (primary ? ExchangeColors.ink : ExchangeColors.teal),
      ),
      backgroundColor: const WidgetStatePropertyAll(Colors.transparent),
      surfaceTintColor: const WidgetStatePropertyAll(Colors.transparent),
      elevation: const WidgetStatePropertyAll(0),
      side: const WidgetStatePropertyAll(BorderSide.none),
      shape: WidgetStatePropertyAll(
        RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(round ? 999 : 20),
        ),
      ),
      padding: WidgetStatePropertyAll(
        round
            ? const EdgeInsets.all(10)
            : const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
      textStyle: const WidgetStatePropertyAll(
        TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
      backgroundBuilder: (context, states, child) => LiquidControlSurface(
        active: primary,
        disabled: states.contains(WidgetState.disabled),
        pressed: states.contains(WidgetState.pressed),
        radius: round ? 999 : 20,
        child: child ?? const SizedBox.shrink(),
      ),
    );
