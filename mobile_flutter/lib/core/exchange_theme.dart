import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'daylight_surface.dart';

abstract final class ExchangeColors {
  // Ground & Concourse surfaces (UniWay Metro Signage)
  static const surface = Color(0xFFFFFFFF);
  static const background = Color(0xFFFFFFFF);
  static const concourse = Color(0xFFF3F4F6);
  static const surfaceMuted = Color(0xFFF3F4F6);

  // Ink hierarchy (WCAG AAA >= 7.5:1 on white and muted surfaces)
  static const ink = Color(0xFF1A1D23);
  static const bodyInk = Color(0xFF2B303A);
  static const secondaryInk = Color(0xFF454C5A);

  // Primary Action Blue (>= 6.5:1 with white label, >= 5.7:1 on soft fills)
  static const actionBlue = Color(0xFF165CB4);
  static const teal = Color(0xFF165CB4);
  static const primaryEnd = Color(0xFF0F448A);
  static const onPrimary = Color(0xFFFFFFFF);
  static const blue = Color(0xFF165CB4);
  static const tealSoft = Color(0xFFEAF1FB);
  static const blueSoft = Color(0xFFEAF1FB);

  // Rules & Input borders
  static const line = Color(0xFFD6DAE1);
  static const fieldBorder = Color(0xFF8D95A3);

  // Semantic Status Roles
  static const success = Color(0xFF0C7D56);
  static const successSoft = Color(0xFFE7F4EE);
  static const referenceAccent = Color(0xFF8C5A2E);
  static const referenceInk = Color(0xFF5A3A1D);
  static const referenceSoft = Color(0xFFF5EFE8);
  static const amber = Color(0xFF9A4B00);
  static const amberSoft = Color(0xFFFEF5E1);
  static const coral = Color(0xFF9A4B00);
  static const coralSoft = Color(0xFFFDECEC);
  static const danger = Color(0xFFB81C22);

  // Canonical 5-color Metro Line rule segments
  static const metroRed = Color(0xFFD9262C);
  static const metroYellow = Color(0xFFF2A81D);
  static const metroBlue = Color(0xFF1F6FD1);
  static const metroGreen = Color(0xFF0C7D56);
  static const metroBrown = Color(0xFF8C5A2E);

  static const tabularFigures = [FontFeature.tabularFigures()];
}

ThemeData buildExchangeTheme() {
  TextStyle type(
    double size, {
    bool strong = false,
    bool bold = false,
    bool secondary = false,
    bool tabular = false,
    double height = 1.42,
  }) => TextStyle(
    fontSize: size,
    height: height,
    fontWeight: bold
        ? FontWeight.w700
        : (strong ? FontWeight.w600 : FontWeight.w400),
    color: secondary ? ExchangeColors.secondaryInk : ExchangeColors.ink,
    fontFeatures: tabular ? ExchangeColors.tabularFigures : null,
  );

  final scheme = ColorScheme.fromSeed(
    seedColor: ExchangeColors.actionBlue,
    brightness: Brightness.light,
    primary: ExchangeColors.actionBlue,
    onPrimary: ExchangeColors.onPrimary,
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

  final inputRadius = BorderRadius.circular(12);

  return base.copyWith(
    textTheme: TextTheme(
      displayLarge: type(30, bold: true, tabular: true, height: 1.24),
      displayMedium: type(28, bold: true, tabular: true, height: 1.26),
      displaySmall: type(26, bold: true, tabular: true, height: 1.28),
      headlineLarge: type(26, bold: true, height: 1.28),
      headlineMedium: type(22, bold: true, tabular: true, height: 1.3),
      headlineSmall: type(22, bold: true, height: 1.3),
      titleLarge: type(18, bold: true, height: 1.34),
      titleMedium: type(16, strong: true, height: 1.36),
      titleSmall: type(15, strong: true, height: 1.36),
      bodyLarge: type(16),
      bodyMedium: type(15),
      bodySmall: type(13, secondary: true, tabular: true),
      labelLarge: type(15, strong: true, tabular: true),
      labelMedium: type(12, strong: true, tabular: true, height: 1.3),
      labelSmall: type(12, tabular: true, height: 1.3),
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: ExchangeColors.surface,
      systemOverlayStyle: SystemUiOverlayStyle.dark,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: type(18, bold: true, height: 1.3),
      iconTheme: const IconThemeData(color: ExchangeColors.ink),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: ExchangeColors.surface,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: ExchangeColors.line),
      ),
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      backgroundColor: ExchangeColors.surface,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
    ),
    expansionTileTheme: const ExpansionTileThemeData(
      shape: Border(),
      collapsedShape: Border(),
      iconColor: ExchangeColors.actionBlue,
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
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      constraints: const BoxConstraints(minHeight: 48),
      border: OutlineInputBorder(
        borderRadius: inputRadius,
        borderSide: const BorderSide(color: ExchangeColors.fieldBorder),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: inputRadius,
        borderSide: const BorderSide(color: ExchangeColors.fieldBorder),
      ),
      disabledBorder: OutlineInputBorder(
        borderRadius: inputRadius,
        borderSide: const BorderSide(color: ExchangeColors.line),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: inputRadius,
        borderSide: const BorderSide(
          color: ExchangeColors.actionBlue,
          width: 2,
        ),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: inputRadius,
        borderSide: const BorderSide(color: ExchangeColors.danger),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: inputRadius,
        borderSide: const BorderSide(color: ExchangeColors.danger, width: 2),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: _metroButtonStyle(primary: true),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: _metroButtonStyle(primary: false),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        minimumSize: const Size(48, 48),
        foregroundColor: ExchangeColors.actionBlue,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        textStyle: type(14, strong: true, tabular: true),
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(
        minimumSize: const Size(48, 48),
        foregroundColor: ExchangeColors.secondaryInk,
      ),
    ),
    chipTheme: base.chipTheme.copyWith(
      backgroundColor: ExchangeColors.surface,
      selectedColor: ExchangeColors.tealSoft,
      disabledColor: ExchangeColors.surfaceMuted,
      checkmarkColor: ExchangeColors.actionBlue,
      side: WidgetStateBorderSide.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return const BorderSide(color: ExchangeColors.actionBlue, width: 1.2);
        }
        return const BorderSide(color: ExchangeColors.line);
      }),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      labelStyle: const TextStyle(
        color: ExchangeColors.ink,
        fontSize: 13,
        fontWeight: FontWeight.w600,
        fontFeatures: ExchangeColors.tabularFigures,
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      height: 64,
      backgroundColor: ExchangeColors.surface,
      indicatorColor: ExchangeColors.tealSoft,
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          fontSize: 12,
          fontWeight: states.contains(WidgetState.selected)
              ? FontWeight.w700
              : FontWeight.w500,
          color: states.contains(WidgetState.selected)
              ? ExchangeColors.actionBlue
              : ExchangeColors.secondaryInk,
        ),
      ),
    ),
    cupertinoOverrideTheme: const CupertinoThemeData(
      primaryColor: ExchangeColors.actionBlue,
      scaffoldBackgroundColor: ExchangeColors.background,
      barBackgroundColor: ExchangeColors.surface,
      textTheme: CupertinoTextThemeData(
        textStyle: TextStyle(color: ExchangeColors.ink, fontSize: 15),
      ),
    ),
  );
}

ButtonStyle _metroButtonStyle({required bool primary}) => ButtonStyle(
  minimumSize: const WidgetStatePropertyAll(Size(48, 48)),
  foregroundColor: WidgetStateProperty.resolveWith(
    (states) => states.contains(WidgetState.disabled)
        ? ExchangeColors.secondaryInk
        : (primary ? ExchangeColors.onPrimary : ExchangeColors.actionBlue),
  ),
  backgroundColor: const WidgetStatePropertyAll(Colors.transparent),
  surfaceTintColor: const WidgetStatePropertyAll(Colors.transparent),
  elevation: const WidgetStatePropertyAll(0),
  side: WidgetStateProperty.resolveWith((states) {
    if (primary) return BorderSide.none;
    if (states.contains(WidgetState.disabled)) {
      return const BorderSide(color: ExchangeColors.line);
    }
    return const BorderSide(color: ExchangeColors.line);
  }),
  shape: WidgetStatePropertyAll(
    RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
  ),
  padding: const WidgetStatePropertyAll(
    EdgeInsets.symmetric(horizontal: 16, vertical: 12),
  ),
  textStyle: const WidgetStatePropertyAll(
    TextStyle(
      fontSize: 15,
      fontWeight: FontWeight.w600,
      fontFeatures: ExchangeColors.tabularFigures,
    ),
  ),
  backgroundBuilder: (context, states, child) => LiquidControlSurface(
    active: primary,
    disabled: states.contains(WidgetState.disabled),
    pressed: states.contains(WidgetState.pressed),
    radius: 12,
    child: child ?? const SizedBox.shrink(),
  ),
);
