// Deterministic native-icon packaging of UniWay's existing artwork.
// Run from mobile_flutter: dart run tool/build_brand_icons.dart
import 'dart:io';
import 'dart:convert';
import 'package:image/image.dart' as image;

void main() {
  final source = image.decodeWebP(
    File('assets/brand/uniway-logo.webp').readAsBytesSync(),
  )!;
  image.Image canvas(
    int size, {
    bool transparent = false,
    double coverage = .72,
  }) {
    final output = image.Image(width: size, height: size, numChannels: 4);
    image.fill(
      output,
      color: image.ColorRgba8(255, 255, 255, transparent ? 0 : 255),
    );
    final logo = image.copyResize(
      source,
      width: (size * coverage).round(),
      interpolation: image.Interpolation.cubic,
    );
    image.compositeImage(
      output,
      logo,
      dstX: (size - logo.width) ~/ 2,
      dstY: (size - logo.height) ~/ 2,
    );
    return output;
  }

  void save(String path, image.Image icon) {
    final file = File(path)..parent.createSync(recursive: true);
    file.writeAsBytesSync(image.encodePng(icon));
  }

  for (final entry in {
    'mdpi': 48,
    'hdpi': 72,
    'xhdpi': 96,
    'xxhdpi': 144,
    'xxxhdpi': 192,
  }.entries) {
    save(
      'android/app/src/main/res/mipmap-${entry.key}/ic_launcher.png',
      canvas(entry.value),
    );
  }
  save(
    'android/app/src/main/res/drawable-xxxhdpi/uniway_foreground.png',
    canvas(432, transparent: true, coverage: .6),
  );
  final icons = jsonDecode(
    File(
      'ios/Runner/Assets.xcassets/AppIcon.appiconset/Contents.json',
    ).readAsStringSync(),
  );
  for (final entry in icons['images'] as List) {
    if (entry['filename'] == null) continue;
    final points = double.parse((entry['size'] as String).split('x').first);
    final scale = double.parse((entry['scale'] as String).replaceAll('x', ''));
    save(
      'ios/Runner/Assets.xcassets/AppIcon.appiconset/${entry['filename']}',
      canvas((points * scale).round()),
    );
  }
  for (var scale = 1; scale <= 3; scale++) {
    save(
      'ios/Runner/Assets.xcassets/LaunchImage.imageset/LaunchImage${scale == 1 ? '' : '@${scale}x'}.png',
      canvas(180 * scale),
    );
  }
  stdout.writeln('UniWay launcher and launch image assets generated.');
}
