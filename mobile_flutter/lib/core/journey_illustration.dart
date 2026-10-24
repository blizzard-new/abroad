import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'exchange_theme.dart';

/// Original vector travel illustration; decorative, with no network dependency.
class JourneyIllustration extends StatelessWidget {
  const JourneyIllustration({super.key});
  @override
  Widget build(BuildContext context) => ExcludeSemantics(
    child: SizedBox(
      width: 104,
      height: 112,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Positioned.fill(child: CustomPaint(painter: _JourneyPainter())),
          const Positioned(
            right: 0,
            top: 4,
            child: Icon(
              Icons.flight_rounded,
              size: 32,
              color: ExchangeColors.teal,
            ),
          ),
          Positioned(
            left: 2,
            bottom: 0,
            child: Container(
              width: 44,
              height: 52,
              decoration: BoxDecoration(
                color: ExchangeColors.blue,
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(
                Icons.public_rounded,
                color: Colors.white,
                size: 24,
              ),
            ),
          ),
        ],
      ),
    ),
  );
}

class _JourneyPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width * .55, size.height * .53);
    final globe = Rect.fromCircle(center: center, radius: 38);
    canvas.drawCircle(
      center,
      44,
      Paint()..color = Colors.white.withValues(alpha: .65),
    );
    canvas.drawCircle(center, 38, Paint()..color = ExchangeColors.tealSoft);
    final line = Paint()
      ..color = ExchangeColors.teal.withValues(alpha: .3)
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;
    canvas.drawCircle(center, 38, line);
    canvas.drawOval(
      Rect.fromCenter(center: center, width: 32, height: 76),
      line,
    );
    canvas.drawOval(
      Rect.fromCenter(center: center, width: 76, height: 27),
      line,
    );
    canvas.drawLine(
      center - const Offset(38, 0),
      center + const Offset(38, 0),
      line,
    );
    final route = globe.inflate(9);
    line.color = ExchangeColors.teal;
    for (var i = 0; i < 9; i++) {
      canvas.drawArc(route, math.pi * (1.03 + i * .065), .09, false, line);
    }
    canvas.drawCircle(
      center + const Offset(25, 26),
      4,
      Paint()..color = ExchangeColors.coral,
    );
  }

  @override
  bool shouldRepaint(_JourneyPainter oldDelegate) => false;
}
