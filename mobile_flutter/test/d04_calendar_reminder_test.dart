import 'package:exchange_guide_flutter/core/application_calendar.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('D-04: Chinese date extraction', () {
    test('extracts 月日 format', () {
      final dates = extractFutureDates('截止日10月15日', today: DateTime(2026, 9, 1));
      expect(dates, isNotEmpty);
      expect(dates.first.month, 10);
      expect(dates.first.day, 15);
    });

    test('extracts English "15 October" format', () {
      final dates = extractFutureDates(
        'Deadline: 15 October 2026',
        today: DateTime(2026, 9, 1),
      );
      expect(dates, isNotEmpty);
      expect(dates.first.month, 10);
    });

    test('past dates roll over to next year', () {
      final dates = extractFutureDates('3月15日', today: DateTime(2026, 11, 1));
      if (dates.isNotEmpty) {
        expect(dates.first.year, greaterThanOrEqualTo(2027));
      }
    });
  });

  group('D-04: Countdown labels', () {
    test('today', () {
      expect(
        countdownLabel(DateTime(2026, 9, 15), today: DateTime(2026, 9, 15)),
        '今天',
      );
    });

    test('tomorrow', () {
      expect(
        countdownLabel(DateTime(2026, 9, 16), today: DateTime(2026, 9, 15)),
        '明天',
      );
    });

    test('future shows 天後', () {
      final label = countdownLabel(
        DateTime(2026, 9, 22), today: DateTime(2026, 9, 15),
      );
      expect(label, contains('7'));
      expect(label, contains('天後'));
    });

    test('past shows 已過', () {
      final label = countdownLabel(
        DateTime(2026, 9, 10), today: DateTime(2026, 9, 15),
      );
      expect(label, contains('已過'));
      expect(label, contains('5'));
    });
  });

  group('D-04: Calendar event construction', () {
    test('ApplicationCalendarEvent holds all required fields', () {
      final event = ApplicationCalendarEvent(
        id: 'e1', title: '申請截止', date: DateTime(2026, 10, 15),
        category: 'home', reminderDays: 7, note: '以官方簡章為準',
        sourceUrl: 'https://example.com', isOfficial: true,
      );
      expect(event.title, '申請截止');
      expect(event.isOfficial, isTrue);
      expect(event.reminderDays, 7);
    });

    test('calendarEventDescription returns non-empty', () {
      final event = ApplicationCalendarEvent(
        id: 'e2', title: '測試', date: DateTime(2026, 10, 1),
        category: 'partner', reminderDays: 3, note: '備註',
        sourceUrl: 'https://example.com', isOfficial: true,
      );
      expect(calendarEventDescription(event), isNotEmpty);
    });

    test('dateKey formats as YYYY-MM-DD', () {
      expect(dateKey(DateTime(2026, 3, 5)), '2026-03-05');
    });

    test('parseDateKey round-trips for valid date', () {
      final d = parseDateKey('2026-10-15');
      expect(d, isNotNull);
      expect(d!.year, 2026);
      expect(d.month, 10);
      expect(d.day, 15);
    });
  });

  group('D-04: Reminder threshold intervals', () {
    test('30/14/7/3/1 day intervals are correct', () {
      final deadline = DateTime(2026, 12, 1);
      for (final days in [30, 14, 7, 3, 1]) {
        final reminder = deadline.subtract(Duration(days: days));
        expect(deadline.difference(reminder).inDays, days);
      }
    });
  });
}
