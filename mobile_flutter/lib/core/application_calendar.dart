import '../data/models.dart';

class ApplicationCalendarEvent {
  const ApplicationCalendarEvent({
    required this.id,
    required this.title,
    required this.date,
    required this.category,
    required this.reminderDays,
    required this.note,
    required this.sourceUrl,
    required this.isOfficial,
  });

  factory ApplicationCalendarEvent.fromJson(Map<String, dynamic> json) {
    return ApplicationCalendarEvent(
      id: textValue(json['id']),
      title: textValue(json['title']),
      date: parseDateKey(textValue(json['date'])) ?? DateTime.now(),
      category: textValue(json['category'], 'other'),
      reminderDays: json['reminder_days'] is int
          ? json['reminder_days'] as int
          : int.tryParse(textValue(json['reminder_days'])) ?? 0,
      note: textValue(json['note']),
      sourceUrl: textValue(json['source_url']),
      isOfficial: json['is_official'] == true,
    );
  }

  final String id;
  final String title;
  final DateTime date;
  final String category;
  final int reminderDays;
  final String note;
  final String sourceUrl;
  final bool isOfficial;

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'date': dateKey(date),
    'category': category,
    'reminder_days': reminderDays,
    'note': note,
    'source_url': sourceUrl,
    'is_official': isOfficial,
  };
}

DateTime dateOnly(DateTime value) =>
    DateTime(value.year, value.month, value.day);

String dateKey(DateTime value) =>
    '${value.year.toString().padLeft(4, '0')}-'
    '${value.month.toString().padLeft(2, '0')}-'
    '${value.day.toString().padLeft(2, '0')}';

DateTime? parseDateKey(String value) {
  final match = RegExp(r'^(\d{4})-(\d{2})-(\d{2})$').firstMatch(value);
  if (match == null) return null;
  return _validDate(
    int.parse(match.group(1)!),
    int.parse(match.group(2)!),
    int.parse(match.group(3)!),
  );
}

DateTime? _validDate(int year, int month, int day) {
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;
  final value = DateTime(year, month, day);
  if (value.year != year || value.month != month || value.day != day) {
    return null;
  }
  return value;
}

class _DateCandidate {
  const _DateCandidate(this.month, this.day, this.index);

  final int month;
  final int day;
  final int index;
}

List<DateTime> extractFutureDates(
  String text, {
  DateTime? today,
  bool lastOnly = false,
}) {
  final value = text.trim();
  if (value.isEmpty) return const [];
  final base = dateOnly(today ?? DateTime.now());
  final explicitYear = RegExp(r'(20\d{2})\s*年?').firstMatch(value)?.group(1);
  final candidates = <_DateCandidate>[];

  void add(String? month, String? day, int index) {
    final monthValue = int.tryParse(month ?? '');
    final dayValue = int.tryParse(day ?? '');
    if (monthValue == null || dayValue == null) return;
    if (monthValue < 1 || monthValue > 12 || dayValue < 1 || dayValue > 31) {
      return;
    }
    candidates.add(_DateCandidate(monthValue, dayValue, index));
  }

  for (final match in RegExp(
    r'(\d{1,2})\s*月\s*(\d{1,2})\s*日?',
  ).allMatches(value)) {
    add(match.group(1), match.group(2), match.start);
  }
  for (final match in RegExp(
    r'(?<!\d)(\d{1,2})\s*[/.\-]\s*(\d{1,2})(?!\d)',
  ).allMatches(value)) {
    add(match.group(1), match.group(2), match.start);
  }

  const months = {
    'january': 1,
    'jan': 1,
    'february': 2,
    'feb': 2,
    'march': 3,
    'mar': 3,
    'april': 4,
    'apr': 4,
    'may': 5,
    'june': 6,
    'jun': 6,
    'july': 7,
    'jul': 7,
    'august': 8,
    'aug': 8,
    'september': 9,
    'sept': 9,
    'sep': 9,
    'october': 10,
    'oct': 10,
    'november': 11,
    'nov': 11,
    'december': 12,
    'dec': 12,
  };
  for (final match in RegExp(
    r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\b',
    caseSensitive: false,
  ).allMatches(value)) {
    final month = months[match.group(2)!.toLowerCase()];
    if (month != null) add('$month', match.group(1), match.start);
  }

  candidates.sort((left, right) => left.index.compareTo(right.index));
  final ordered = lastOnly && candidates.isNotEmpty
      ? [candidates.last]
      : candidates;
  final seen = <String>{};
  final dates = <DateTime>[];
  for (final candidate in ordered) {
    var year = explicitYear == null ? base.year : int.parse(explicitYear);
    var date = _validDate(year, candidate.month, candidate.day);
    if (date == null) continue;
    if (explicitYear == null && date.isBefore(base)) {
      year += 1;
      date = _validDate(year, candidate.month, candidate.day);
    }
    if (date == null || date.isBefore(base)) continue;
    if (seen.add(dateKey(date))) dates.add(date);
  }
  return dates;
}

List<ApplicationCalendarEvent> officialApplicationEvents(
  StudentDashboard? dashboard, {
  DateTime? today,
}) {
  if (dashboard == null) return const [];
  final events = <ApplicationCalendarEvent>[];

  for (final period in dashboard.applicationPeriods) {
    for (final detail in period.details) {
      for (final date in extractFutureDates(
        detail,
        today: today,
        lastOnly: true,
      )) {
        events.add(
          ApplicationCalendarEvent(
            id: 'official-home-${dateKey(date)}-${period.title}',
            title: period.title,
            date: date,
            category: 'home',
            reminderDays: 7,
            note: detail,
            sourceUrl: period.source?.sourceUrl ?? '',
            isOfficial: true,
          ),
        );
      }
    }
  }

  for (final school in dashboard.partnerUniversities) {
    for (final date in extractFutureDates(
      school.displayApplicationDeadline,
      today: today,
    )) {
      events.add(
        ApplicationCalendarEvent(
          id: 'official-partner-${dateKey(date)}-${school.schoolName}',
          title: school.schoolName,
          date: date,
          category: 'partner',
          reminderDays: 7,
          note: school.displayApplicationDeadline,
          sourceUrl: school.sourceUrl,
          isOfficial: true,
        ),
      );
    }
  }
  return mergeApplicationEvents(events);
}

List<ApplicationCalendarEvent> mergeApplicationEvents(
  Iterable<ApplicationCalendarEvent> events,
) {
  final sorted = events.toList()
    ..sort((left, right) {
      final byDate = dateOnly(left.date).compareTo(dateOnly(right.date));
      return byDate != 0 ? byDate : left.title.compareTo(right.title);
    });
  final seen = <String>{};
  return sorted.where((event) {
    final key = '${event.isOfficial}|${event.title}|${dateKey(event.date)}';
    return seen.add(key);
  }).toList();
}

int daysUntil(DateTime value, {DateTime? today}) =>
    dateOnly(value).difference(dateOnly(today ?? DateTime.now())).inDays;

String countdownLabel(DateTime value, {DateTime? today}) {
  final days = daysUntil(value, today: today);
  if (days < 0) return '已過 ${days.abs()} 天';
  if (days == 0) return '今天';
  if (days == 1) return '明天';
  return '$days 天後';
}

String calendarEventDescription(ApplicationCalendarEvent event) {
  return [
    if (event.note.isNotEmpty) event.note,
    if (event.sourceUrl.isNotEmpty) '官方來源：${event.sourceUrl}',
    if (event.isOfficial) '日期可能調整，送件前請再次核對官方公告。',
  ].join('\n');
}
