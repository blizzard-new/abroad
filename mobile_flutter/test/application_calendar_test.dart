import 'package:exchange_guide_flutter/core/application_calendar.dart';
import 'package:exchange_guide_flutter/data/models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('extracts Chinese and English future deadline dates', () {
    final today = DateTime(2026, 7, 18);

    expect(
      extractFutureDates('秋季班：9月30日，春季班：3月30日', today: today).map(dateKey),
      ['2026-09-30', '2027-03-30'],
    );
    expect(
      extractFutureDates(
        'Semester 1: 30 September; Semester 2: 30 March',
        today: today,
      ).map(dateKey),
      ['2026-09-30', '2027-03-30'],
    );
  });

  test('official application events merge school and partner deadlines', () {
    final dashboard = StudentDashboard.fromJson({
      'school_name': '長庚大學',
      'application_periods': [
        {
          'title': '校內甄選',
          'details': ['秋季班：11/01-12/20'],
          'source': {
            'title': '公告',
            'source_url': 'https://www.cgu.edu.tw/oia-ch/',
          },
        },
      ],
      'partner_universities': [
        {
          'school_name': 'Lincoln University',
          'country': '紐西蘭',
          'application_deadline': '30 September',
          'source_url': 'https://www.cgu.edu.tw/oia-ch/',
        },
      ],
    });

    final events = officialApplicationEvents(
      dashboard,
      today: DateTime(2026, 7, 18),
    );

    expect(events.map((event) => event.title), ['Lincoln University', '校內甄選']);
    expect(events.map((event) => dateKey(event.date)), [
      '2026-09-30',
      '2026-12-20',
    ]);
  });

  test('builds concise calendar descriptions with official sources', () {
    final event = ApplicationCalendarEvent(
      id: 'personal-1',
      title: '完成交換讀書計畫',
      date: DateTime(2026, 7, 25),
      category: 'documents',
      reminderDays: 7,
      note: '整理動機與修課規劃',
      sourceUrl: 'https://www.cgu.edu.tw/oia-ch/',
      isOfficial: true,
    );

    final description = calendarEventDescription(event);
    expect(description, contains('整理動機與修課規劃'));
    expect(description, contains('官方來源：https://www.cgu.edu.tw/oia-ch/'));
    expect(description, contains('送件前請再次核對官方公告'));
  });
}
