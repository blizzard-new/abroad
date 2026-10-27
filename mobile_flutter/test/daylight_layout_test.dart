import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:exchange_guide_flutter/core/exchange_theme.dart';
import 'package:exchange_guide_flutter/screens/root_shell.dart';
import 'package:exchange_guide_flutter/state/exchange_store.dart';
import 'student_ui_test.dart' show fixtureStore;

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));
  for (final size in [
    const Size(375, 812),
    const Size(812, 375),
    const Size(768, 1024),
  ]) {
    testWidgets('daylight navigation and content at $size with large text', (
      tester,
    ) async {
      await tester.binding.setSurfaceSize(size);
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final store = fixtureStore();
      addTearDown(store.dispose);
      await tester.pumpWidget(
        ExchangeStoreScope(
          store: store,
          child: MaterialApp(
            theme: buildExchangeTheme(),
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(context).copyWith(
                textScaler: const TextScaler.linear(2),
                disableAnimations: true,
                highContrast: true,
              ),
              child: child!,
            ),
            home: const RootShell(),
          ),
        ),
      );
      await tester.pumpAndSettle();
      for (var tab = 0; tab < 5; tab++) {
        final target = find.byKey(ValueKey('main-tab-$tab'));
        expect(tester.getSize(target).height, greaterThanOrEqualTo(48));
        expect(tester.getSize(target).width, greaterThanOrEqualTo(48));
        await tester.tap(target);
        await tester.pumpAndSettle();
        expect(store.navigationTab, tab);
        expect(tester.takeException(), isNull, reason: 'tab $tab at $size');
      }
    });
  }
}
