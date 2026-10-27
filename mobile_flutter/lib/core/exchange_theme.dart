import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'daylight_surface.dart';

abstract final class ExchangeColors {
  static const primaryEnd = Color(0xFF075C64);
  static const onPrimary = Colors.white;
  static const fieldBorder = Color(0xFF81938E);
  static const background = Color(0xFFF6F8F7);
  static const surface = Color(0xFFFFFFFF);
  static const surfaceMuted = Color(0xFFEEF2F1);
  static const ink = Color(0xFF172D37);
  static const secondaryInk = Color(0xFF52656E);
  static const line = Color(0xFFDCE5E3);
  static const teal = Color(0xFF006C67);
  static const tealSoft = Color(0xFFE2F3EE);
  static const blue = Color(0xFF315DA8);
  static const blueSoft = Color(0xFFEAF0FC);
  static const coral = Color(0xFFAC4934);
  static const coralSoft = Color(0xFFFCEEE7);
  static const amber = Color(0xFF8E620B);
  static const amberSoft = Color(0xFFFCF2DB);
  static const success = Color(0xFF247349);
  static const danger = Color(0xFFB83140);
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
      bodySmall: type(14, secondary: true),
      labelLarge: type(16, strong: true),
      labelMedium: type(12, strong: true),
      labelSmall: type(12),
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: ExchangeColors.background.withValues(alpha: .88),
      systemOverlayStyle: SystemUiOverlayStyle.dark,
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
      fillColor: ExchangeColors.surface,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      constraints: const BoxConstraints(minHeight: 48),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: ExchangeColors.fieldBorder),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: ExchangeColors.fieldBorder),
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
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        minimumSize: const Size(48, 48),
        foregroundColor: ExchangeColors.teal,
        textStyle: type(14, strong: true),
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(
        minimumSize: const Size(48, 48),
        foregroundColor: ExchangeColors.secondaryInk,
      ),
    ),
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
      barBackgroundColor: ExchangeColors.surface,
      textTheme: CupertinoTextThemeData(
        textStyle: TextStyle(color: ExchangeColors.ink, fontSize: 16),
      ),
    ),
  );
}

ButtonStyle _liquidStyle({bool primary = false, bool round = false}) =>
    ButtonStyle(
      minimumSize: WidgetStatePropertyAll(Size(48, 48)),
      foregroundColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.disabled)
            ? ExchangeColors.secondaryInk
            : (primary ? ExchangeColors.onPrimary : ExchangeColors.teal),
      ),
      backgroundColor: const WidgetStatePropertyAll(Colors.transparent),
      surfaceTintColor: const WidgetStatePropertyAll(Colors.transparent),
      elevation: const WidgetStatePropertyAll(0),
      side: const WidgetStatePropertyAll(BorderSide.none),
      shape: WidgetStatePropertyAll(
        RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(round ? 999 : 16),
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
        radius: round ? 999 : 16,
        child: child ?? const SizedBox.shrink(),
      ),
    );
