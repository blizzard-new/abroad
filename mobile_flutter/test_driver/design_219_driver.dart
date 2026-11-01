import 'dart:io';
import 'package:integration_test/integration_test_driver_extended.dart';

Future<void> main() async {
  await Directory('build/design-219').create(recursive: true);
  await integrationDriver(
    onScreenshot: (name, bytes, [args]) async {
      await File('build/design-219/$name.png').writeAsBytes(bytes);
      return true;
    },
  );
}
