import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/application_calendar.dart';
import '../core/connected_calendar.dart';
import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
import '../state/exchange_store.dart';

class DeadlinesScreen extends StatefulWidget {
  const DeadlinesScreen({super.key, this.initialDate, this.embedded = false});
  final bool embedded;
  final DateTime? initialDate;

  @override
  State<DeadlinesScreen> createState() => _DeadlinesScreenState();
}

class _DeadlinesScreenState extends State<DeadlinesScreen> {
  late DateTime focusedMonth;
  late DateTime selectedDate;
  bool showUpcoming = true;

  @override
  void initState() {
    super.initState();
    final today = dateOnly(widget.initialDate ?? DateTime.now());
    focusedMonth = DateTime(today.year, today.month);
    selectedDate = today;
  }

  void _showCalendarError(Object exception, ExchangeStore store) {
    if (!mounted) return;
    final connectionError = exception is CalendarConnectionException
        ? exception
        : null;
    final messenger = ScaffoldMessenger.of(context);
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        content: Text(exception.toString()),
        action: connectionError?.canOpenSettings == true
            ? SnackBarAction(
                label: '開啟設定',
                onPressed: store.openCalendarSettings,
              )
            : null,
      ),
    );
  }

  Future<void> _chooseCalendar(ExchangeStore store) async {
    List<WritableCalendar> calendars;
    try {
      calendars = await store.requestWritableCalendars();
    } catch (exception) {
      _showCalendarError(exception, store);
      return;
    }
    if (!mounted) return;
    if (calendars.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('手機尚未加入可寫入的帳號日曆。')));
      return;
    }
    final selected = await showModalBottomSheet<WritableCalendar>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      showDragHandle: true,
      builder: (_) => _CalendarPickerSheet(
        calendars: calendars,
        selectedId: store.connectedCalendar?.id,
      ),
    );
    if (selected == null || !mounted) return;
    try {
      await store.connectCalendar(selected);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('已連接 ${selected.name}，申請任務會自動同步。')),
      );
    } catch (exception) {
      _showCalendarError(exception, store);
    }
  }

  Future<void> _syncAll(ExchangeStore store) async {
    try {
      await store.syncAllCalendarEvents();
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('行程同步完成。')));
    } catch (exception) {
      _showCalendarError(exception, store);
    }
  }

  Future<void> _disconnectCalendar(ExchangeStore store) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('停止日曆同步？'),
        content: const Text('已同步到第三方日曆的行程會保留。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('停止同步'),
          ),
        ],
      ),
    );
    if (confirmed == true) await store.disconnectCalendar();
  }

  Future<void> _addTask(ExchangeStore store) async {
    final event = await showModalBottomSheet<ApplicationCalendarEvent>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      showDragHandle: true,
      backgroundColor: const Color(0xFFF8FAFB),
      builder: (_) => _AddTaskSheet(initialDate: selectedDate),
    );
    if (event == null) return;
    final synced = await store.addCalendarEvent(event);
    if (!mounted) return;
    setState(() {
      selectedDate = event.date;
      focusedMonth = DateTime(event.date.year, event.date.month);
      showUpcoming = false;
    });
    final calendar = store.connectedCalendar;
    final message = calendar == null
        ? '已加入申請日曆。'
        : synced
        ? '已加入並同步到 ${calendar.name}。'
        : '任務已儲存，但同步失敗。';
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _editTask(
    ExchangeStore store,
    ApplicationCalendarEvent event,
  ) async {
    final updated = await showModalBottomSheet<ApplicationCalendarEvent>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      showDragHandle: true,
      backgroundColor: const Color(0xFFF8FAFB),
      builder: (_) =>
          _AddTaskSheet(initialDate: event.date, initialEvent: event),
    );
    if (updated == null) return;
    final synced = await store.updateCalendarEvent(updated);
    if (!mounted) return;
    setState(() {
      selectedDate = updated.date;
      focusedMonth = DateTime(updated.date.year, updated.date.month);
      showUpcoming = false;
    });
    final message = store.connectedCalendar == null
        ? '任務已更新。'
        : synced
        ? '任務與第三方日曆已更新。'
        : '任務已更新，但同步失敗。';
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _deleteTask(
    ExchangeStore store,
    ApplicationCalendarEvent event,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('刪除這個任務？'),
        content: Text(event.title),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('刪除'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await store.deleteCalendarEvent(event.id);
    } catch (exception) {
      _showCalendarError(exception, store);
    }
  }

  Future<void> _syncEvent(
    ExchangeStore store,
    ApplicationCalendarEvent event,
  ) async {
    if (store.connectedCalendar == null) {
      await _chooseCalendar(store);
      if (!mounted || store.connectedCalendar == null) return;
    }
    try {
      await store.syncCalendarEvent(event);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('已同步到第三方日曆。')));
    } catch (exception) {
      _showCalendarError(exception, store);
    }
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final events = store.applicationCalendarEvents;
    final today = dateOnly(DateTime.now());
    final upcoming = events
        .where((event) => !event.date.isBefore(today))
        .toList();
    final selectedEvents = events
        .where((event) => DateUtils.isSameDay(event.date, selectedDate))
        .toList();
    final agenda = showUpcoming ? upcoming.take(6).toList() : selectedEvents;

    final content = SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: store.refresh,
        child: ListView(
          padding: EdgeInsets.fromLTRB(16, 14, 16, widget.embedded ? 122 : 24),
          children: [
            _PlannerHero(events: upcoming),
            const SizedBox(height: 12),
            _CalendarConnectionCard(
              calendar: store.connectedCalendar,
              syncing: store.isCalendarSyncing,
              onConnect: () => _chooseCalendar(store),
              onSync: () => _syncAll(store),
              onDisconnect: () => _disconnectCalendar(store),
            ),
            const SizedBox(height: 12),
            GlassCard(
              padding: const EdgeInsets.fromLTRB(12, 12, 12, 14),
              child: Column(
                children: [
                  _CalendarToolbar(
                    focusedMonth: focusedMonth,
                    onPrevious: () => setState(() {
                      focusedMonth = DateTime(
                        focusedMonth.year,
                        focusedMonth.month - 1,
                      );
                    }),
                    onToday: () => setState(() {
                      selectedDate = today;
                      focusedMonth = DateTime(today.year, today.month);
                      showUpcoming = false;
                    }),
                    onNext: () => setState(() {
                      focusedMonth = DateTime(
                        focusedMonth.year,
                        focusedMonth.month + 1,
                      );
                    }),
                  ),
                  const SizedBox(height: 12),
                  const _WeekdayHeader(),
                  const SizedBox(height: 8),
                  _MonthGrid(
                    month: focusedMonth,
                    selectedDate: selectedDate,
                    events: events,
                    onSelected: (date) => setState(() {
                      selectedDate = date;
                      if (date.month != focusedMonth.month) {
                        focusedMonth = DateTime(date.year, date.month);
                      }
                      showUpcoming = false;
                    }),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: () => _addTask(store),
                icon: const Icon(Icons.add_rounded),
                label: const Text('新增申請任務'),
              ),
            ),
            const SizedBox(height: 24),
            _AgendaHeading(
              showUpcoming: showUpcoming,
              selectedDate: selectedDate,
              count: agenda.length,
              onToggle: () => setState(() => showUpcoming = !showUpcoming),
            ),
            const SizedBox(height: 12),
            if (store.isLoading && events.isEmpty)
              const LoadingCards(count: 3)
            else if (store.error != null && events.isEmpty)
              InlineError(message: store.error!, onRetry: store.refresh)
            else if (agenda.isEmpty)
              _CalendarEmpty(
                selectedDate: selectedDate,
                onAdd: () => _addTask(store),
              )
            else
              ...agenda.map(
                (event) => Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: _AgendaCard(
                    event: event,
                    calendarConnected: store.connectedCalendar != null,
                    synced: store.isCalendarEventSynced(event.id),
                    syncing: store.isCalendarSyncing,
                    onCalendar: () => _syncEvent(store, event),
                    onEdit: event.isOfficial
                        ? null
                        : () => _editTask(store, event),
                    onDelete: event.isOfficial
                        ? null
                        : () => _deleteTask(store, event),
                  ),
                ),
              ),
            const SizedBox(height: 16),
            const Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.verified_user_outlined,
                  color: ExchangeColors.success,
                  size: 19,
                ),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '官方日期仍可能調整；送件前請再次核對來源。',
                    style: TextStyle(color: ExchangeColors.secondaryInk),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
    if (widget.embedded) return content;
    return ExchangePageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: const Text('申請時程'),
          backgroundColor: Colors.white.withValues(alpha: .72),
          surfaceTintColor: Colors.transparent,
        ),
        body: content,
      ),
    );
  }
}

class _PlannerHero extends StatelessWidget {
  const _PlannerHero({required this.events});

  final List<ApplicationCalendarEvent> events;

  @override
  Widget build(BuildContext context) {
    final next = events.isEmpty ? null : events.first;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      if (next != null) const StudentSectionTitle('下一個期限', icon: Icons.timer_outlined),
      StudentSummaryCard(
      icon: Icons.event_outlined,
      title: next == null ? '安排下一步' : countdownLabel(next.date),
      detail: next == null ? '把確認過的日期加入日曆。' : next.title,
    )]);
  }
}

enum _CalendarConnectionAction { change, disconnect }

class _CalendarConnectionCard extends StatelessWidget {
  const _CalendarConnectionCard({
    required this.calendar,
    required this.syncing,
    required this.onConnect,
    required this.onSync,
    required this.onDisconnect,
  });

  final WritableCalendar? calendar;
  final bool syncing;
  final VoidCallback onConnect;
  final VoidCallback onSync;
  final VoidCallback onDisconnect;

  @override
  Widget build(BuildContext context) {
    final connected = calendar != null;
    return GlassCard(
      tint: connected
          ? ExchangeColors.tealSoft.withValues(alpha: .5)
          : Colors.white.withValues(alpha: .54),
      padding: const EdgeInsets.fromLTRB(14, 12, 10, 12),
      child: Row(
        children: [
          ExchangeIconBadge(
            connected ? Icons.cloud_done_outlined : Icons.cloud_sync_outlined,
            color: connected ? ExchangeColors.teal : ExchangeColors.blue,
            background: connected
                ? ExchangeColors.tealSoft
                : ExchangeColors.blueSoft,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  connected ? calendar!.name : '連接第三方日曆',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 2),
                Text(
                  connected ? calendar!.accountLabel : 'Google、iCloud、Outlook',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          if (syncing)
            const SizedBox.square(
              dimension: 44,
              child: Padding(
                padding: EdgeInsets.all(11),
                child: CircularProgressIndicator(strokeWidth: 2.4),
              ),
            )
          else if (!connected)
            SizedBox(
              height: 44,
              child: FilledButton(
                onPressed: onConnect,
                child: const Text('連接'),
              ),
            )
          else ...[
            IconButton(
              tooltip: '立即同步',
              onPressed: onSync,
              icon: const Icon(Icons.sync_rounded),
            ),
            PopupMenuButton<_CalendarConnectionAction>(
              tooltip: '日曆設定',
              onSelected: (action) {
                if (action == _CalendarConnectionAction.change) onConnect();
                if (action == _CalendarConnectionAction.disconnect) {
                  onDisconnect();
                }
              },
              itemBuilder: (_) => const [
                PopupMenuItem(
                  value: _CalendarConnectionAction.change,
                  child: Text('更換日曆'),
                ),
                PopupMenuItem(
                  value: _CalendarConnectionAction.disconnect,
                  child: Text('停止同步'),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _CalendarPickerSheet extends StatelessWidget {
  const _CalendarPickerSheet({
    required this.calendars,
    required this.selectedId,
  });

  final List<WritableCalendar> calendars;
  final String? selectedId;

  @override
  Widget build(BuildContext context) {
    return FractionallySizedBox(
      heightFactor: .72,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 4, 20, 14),
            child: Text(
              '選擇同步日曆',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
              itemCount: calendars.length,
              separatorBuilder: (_, _) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final calendar = calendars[index];
                final selected = calendar.id == selectedId;
                return ListTile(
                  minTileHeight: 60,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                  onTap: () => Navigator.pop(context, calendar),
                  leading: CircleAvatar(
                    backgroundColor: ExchangeColors.blueSoft,
                    foregroundColor: ExchangeColors.blue,
                    child: Icon(
                      calendar.providerName == '本機日曆'
                          ? Icons.phone_android_rounded
                          : Icons.cloud_outlined,
                    ),
                  ),
                  title: Text(calendar.name),
                  subtitle: Text(calendar.accountLabel),
                  trailing: selected
                      ? const Icon(
                          Icons.check_circle_rounded,
                          color: ExchangeColors.success,
                        )
                      : const Icon(Icons.chevron_right_rounded),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _CalendarToolbar extends StatelessWidget {
  const _CalendarToolbar({
    required this.focusedMonth,
    required this.onPrevious,
    required this.onToday,
    required this.onNext,
  });

  final DateTime focusedMonth;
  final VoidCallback onPrevious;
  final VoidCallback onToday;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        IconButton(
          tooltip: '上個月',
          onPressed: onPrevious,
          icon: const Icon(Icons.chevron_left_rounded),
        ),
        const SizedBox(width: 4),
        IconButton(
          tooltip: '回到今天',
          onPressed: onToday,
          icon: const Icon(Icons.my_location_rounded),
        ),
        const SizedBox(width: 4),
        IconButton(
          tooltip: '下個月',
          onPressed: onNext,
          icon: const Icon(Icons.chevron_right_rounded),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            '${focusedMonth.year}年${focusedMonth.month}月',
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
      ],
    );
  }
}

class _WeekdayHeader extends StatelessWidget {
  const _WeekdayHeader();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        for (final day in ['日', '一', '二', '三', '四', '五', '六'])
          Expanded(
            child: Center(
              child: Text(
                day,
                style: const TextStyle(
                  color: ExchangeColors.secondaryInk,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _MonthGrid extends StatelessWidget {
  const _MonthGrid({
    required this.month,
    required this.selectedDate,
    required this.events,
    required this.onSelected,
  });

  final DateTime month;
  final DateTime selectedDate;
  final List<ApplicationCalendarEvent> events;
  final ValueChanged<DateTime> onSelected;

  @override
  Widget build(BuildContext context) {
    final first = DateTime(month.year, month.month);
    final leadingDays = first.weekday % 7;
    final daysInMonth = DateTime(month.year, month.month + 1, 0).day;
    final cellCount = leadingDays + daysInMonth <= 35 ? 35 : 42;
    final firstVisible = first.subtract(Duration(days: leadingDays));
    final dates = List.generate(
      cellCount,
      (index) => firstVisible.add(Duration(days: index)),
    );
    final eventDates = <String, int>{};
    for (final event in events) {
      eventDates.update(
        dateKey(event.date),
        (value) => value + 1,
        ifAbsent: () => 1,
      );
    }
    final today = dateOnly(DateTime.now());

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: dates.length,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 7,
        mainAxisSpacing: 4,
        crossAxisSpacing: 4,
        childAspectRatio: .9,
      ),
      itemBuilder: (context, index) {
        final date = dates[index];
        final selected = DateUtils.isSameDay(date, selectedDate);
        final isToday = DateUtils.isSameDay(date, today);
        final inMonth = date.month == month.month;
        final count = eventDates[dateKey(date)] ?? 0;
        return Semantics(
          button: true,
          selected: selected,
          label: '${date.year}年${date.month}月${date.day}日，$count 個任務',
          child: InkWell(
            borderRadius: BorderRadius.circular(10),
            onTap: () => onSelected(date),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              decoration: BoxDecoration(
                color: selected
                    ? ExchangeColors.blueSoft.withValues(alpha: .9)
                    : Colors.white.withValues(alpha: .38),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: selected
                      ? ExchangeColors.blue.withValues(alpha: .55)
                      : Colors.white.withValues(alpha: .72),
                ),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 30,
                    height: 30,
                    alignment: Alignment.center,
                    decoration: isToday
                        ? const BoxDecoration(
                            color: ExchangeColors.ink,
                            shape: BoxShape.circle,
                          )
                        : null,
                    child: Text(
                      '${date.day}',
                      style: TextStyle(
                        color: isToday
                            ? Colors.white
                            : inMonth
                            ? ExchangeColors.ink
                            : ExchangeColors.secondaryInk.withValues(alpha: .5),
                        fontWeight: isToday || selected
                            ? FontWeight.w600
                            : FontWeight.w400,
                      ),
                    ),
                  ),
                  SizedBox(
                    height: 7,
                    child: count == 0
                        ? null
                        : Row(
                            mainAxisSize: MainAxisSize.min,
                            children: List.generate(
                              count.clamp(1, 3),
                              (_) => Container(
                                width: 4,
                                height: 4,
                                margin: const EdgeInsets.symmetric(
                                  horizontal: 1,
                                ),
                                decoration: const BoxDecoration(
                                  color: ExchangeColors.blue,
                                  shape: BoxShape.circle,
                                ),
                              ),
                            ),
                          ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _AgendaHeading extends StatelessWidget {
  const _AgendaHeading({
    required this.showUpcoming,
    required this.selectedDate,
    required this.count,
    required this.onToggle,
  });

  final bool showUpcoming;
  final DateTime selectedDate;
  final int count;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const ExchangeIconBadge(Icons.checklist_rounded),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            showUpcoming
                ? '接下來要做'
                : '${selectedDate.month}/${selectedDate.day} · $count 項',
            style: Theme.of(context).textTheme.titleLarge,
          ),
        ),
        TextButton(
          onPressed: onToggle,
          child: Text(showUpcoming ? '選定日期' : '看接下來'),
        ),
      ],
    );
  }
}

class _AgendaCard extends StatelessWidget {
  const _AgendaCard({
    required this.event,
    required this.calendarConnected,
    required this.synced,
    required this.syncing,
    required this.onCalendar,
    required this.onEdit,
    required this.onDelete,
  });

  final ApplicationCalendarEvent event;
  final bool calendarConnected;
  final bool synced;
  final bool syncing;
  final VoidCallback onCalendar;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;

  @override
  Widget build(BuildContext context) {
    final category =
        _calendarCategories[event.category] ?? _calendarCategories['other']!;
    return GlassCard(
      padding: const EdgeInsets.all(14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ExchangeIconBadge(
            category.icon,
            color: category.color,
            background: category.background,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  children: [
                    Text(
                      category.label,
                      style: TextStyle(
                        color: category.color,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                    Text(
                      '${event.date.month}/${event.date.day}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    Text(
                      countdownLabel(event.date),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  event.title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                if (event.note.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    studentFacingText(event.note),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
                const SizedBox(height: 8),
                Wrap(
                  spacing: 2,
                  runSpacing: 2,
                  children: [
                    IconButton(
                      tooltip: synced
                          ? '已同步，點擊重新同步'
                          : calendarConnected
                          ? '同步到第三方日曆'
                          : '連接第三方日曆',
                      onPressed: syncing ? null : onCalendar,
                      color: synced
                          ? ExchangeColors.success
                          : ExchangeColors.blue,
                      icon: Icon(
                        synced
                            ? Icons.cloud_done_outlined
                            : calendarConnected
                            ? Icons.cloud_sync_outlined
                            : Icons.add_to_photos_outlined,
                        size: 20,
                      ),
                    ),
                    if (event.sourceUrl.isNotEmpty)
                      IconButton(
                        tooltip: '官方來源',
                        onPressed: () => launchUrl(
                          Uri.parse(event.sourceUrl),
                          mode: LaunchMode.externalApplication,
                        ),
                        icon: const Icon(Icons.open_in_new_rounded, size: 20),
                      ),
                    if (onEdit != null)
                      IconButton(
                        tooltip: '編輯任務',
                        onPressed: onEdit,
                        icon: const Icon(Icons.edit_outlined, size: 20),
                      ),
                    if (onDelete != null)
                      IconButton(
                        tooltip: '刪除任務',
                        onPressed: onDelete,
                        color: ExchangeColors.danger,
                        icon: const Icon(
                          Icons.delete_outline_rounded,
                          size: 20,
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _CalendarEmpty extends StatelessWidget {
  const _CalendarEmpty({required this.selectedDate, required this.onAdd});

  final DateTime selectedDate;
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        children: [
          const ExchangeIconBadge(Icons.calendar_month_outlined),
          const SizedBox(height: 12),
          Text(
            '${selectedDate.month}/${selectedDate.day} 還沒有任務',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 4),
          const Text('可新增文件、語言考試、簽證或住宿提醒。'),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: onAdd,
            icon: const Icon(Icons.add_rounded),
            label: const Text('新增任務'),
          ),
        ],
      ),
    );
  }
}

class _AddTaskSheet extends StatefulWidget {
  const _AddTaskSheet({required this.initialDate, this.initialEvent});

  final DateTime initialDate;
  final ApplicationCalendarEvent? initialEvent;

  @override
  State<_AddTaskSheet> createState() => _AddTaskSheetState();
}

class _AddTaskSheetState extends State<_AddTaskSheet> {
  final titleController = TextEditingController();
  final noteController = TextEditingController();
  late DateTime date;
  String category = 'documents';
  int reminderDays = 7;
  String? error;

  @override
  void initState() {
    super.initState();
    final initial = widget.initialEvent;
    date = initial?.date ?? widget.initialDate;
    titleController.text = initial?.title ?? '';
    noteController.text = initial?.note ?? '';
    category = initial?.category ?? 'documents';
    reminderDays = initial?.reminderDays ?? 7;
  }

  @override
  void dispose() {
    titleController.dispose();
    noteController.dispose();
    super.dispose();
  }

  Future<void> _chooseDate() async {
    final selected = await showDatePicker(
      context: context,
      initialDate: date,
      firstDate: DateTime.now().subtract(const Duration(days: 1)),
      lastDate: DateTime.now().add(const Duration(days: 1460)),
    );
    if (selected != null) setState(() => date = selected);
  }

  void _save() {
    final title = titleController.text.trim();
    if (title.isEmpty) {
      setState(() => error = '請輸入任務名稱。');
      return;
    }
    Navigator.pop(
      context,
      ApplicationCalendarEvent(
        id:
            widget.initialEvent?.id ??
            'personal-${DateTime.now().microsecondsSinceEpoch}',
        title: title,
        date: dateOnly(date),
        category: category,
        reminderDays: reminderDays,
        note: noteController.text.trim(),
        sourceUrl: '',
        isOfficial: false,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        4,
        20,
        20 + MediaQuery.viewInsetsOf(context).bottom,
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.initialEvent == null ? '新增申請任務' : '編輯申請任務',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: titleController,
              autofocus: true,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: '任務名稱',
                hintText: '例如：完成英文讀書計畫',
                prefixIcon: Icon(Icons.task_alt_rounded),
              ),
            ),
            const SizedBox(height: 12),
            InkWell(
              onTap: _chooseDate,
              borderRadius: BorderRadius.circular(12),
              child: InputDecorator(
                decoration: const InputDecoration(
                  labelText: '日期',
                  prefixIcon: Icon(Icons.calendar_today_outlined),
                ),
                child: Text('${date.year}/${date.month}/${date.day}'),
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: category,
              decoration: const InputDecoration(
                labelText: '類型',
                prefixIcon: Icon(Icons.category_outlined),
              ),
              items: _calendarCategories.entries
                  .map(
                    (entry) => DropdownMenuItem(
                      value: entry.key,
                      child: Text(entry.value.label),
                    ),
                  )
                  .toList(),
              onChanged: (value) {
                if (value != null) setState(() => category = value);
              },
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<int>(
              initialValue: reminderDays,
              decoration: const InputDecoration(
                labelText: '提前提醒',
                prefixIcon: Icon(Icons.notifications_none_rounded),
              ),
              items: const [
                DropdownMenuItem(value: 0, child: Text('當天')),
                DropdownMenuItem(value: 3, child: Text('3 天前')),
                DropdownMenuItem(value: 7, child: Text('7 天前')),
                DropdownMenuItem(value: 14, child: Text('14 天前')),
              ],
              onChanged: (value) {
                if (value != null) setState(() => reminderDays = value);
              },
            ),
            const SizedBox(height: 12),
            TextField(
              controller: noteController,
              minLines: 2,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: '備註（選填）',
                hintText: '需要準備的資料或來源',
                alignLabelWithHint: true,
                prefixIcon: Icon(Icons.notes_rounded),
              ),
            ),
            if (error != null) ...[
              const SizedBox(height: 8),
              Text(
                error!,
                style: const TextStyle(
                  color: ExchangeColors.danger,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _save,
                icon: const Icon(Icons.check_rounded),
                label: const Text('儲存任務'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CategoryStyle {
  const _CategoryStyle({
    required this.label,
    required this.icon,
    required this.color,
    required this.background,
  });

  final String label;
  final IconData icon;
  final Color color;
  final Color background;
}

const _calendarCategories = {
  'home': _CategoryStyle(
    label: '校內申請',
    icon: Icons.account_balance_outlined,
    color: ExchangeColors.blue,
    background: ExchangeColors.blueSoft,
  ),
  'partner': _CategoryStyle(
    label: '合作校申請',
    icon: Icons.school_outlined,
    color: ExchangeColors.teal,
    background: ExchangeColors.tealSoft,
  ),
  'documents': _CategoryStyle(
    label: '文件準備',
    icon: Icons.file_copy_outlined,
    color: Color(0xFF6654B8),
    background: Color(0xFFEDE9FA),
  ),
  'language': _CategoryStyle(
    label: '語言考試',
    icon: Icons.translate_rounded,
    color: ExchangeColors.amber,
    background: ExchangeColors.amberSoft,
  ),
  'visa': _CategoryStyle(
    label: '簽證',
    icon: Icons.airplane_ticket_outlined,
    color: ExchangeColors.coral,
    background: ExchangeColors.coralSoft,
  ),
  'housing': _CategoryStyle(
    label: '住宿',
    icon: Icons.bed_outlined,
    color: ExchangeColors.success,
    background: Color(0xFFE5F4EC),
  ),
  'other': _CategoryStyle(
    label: '其他',
    icon: Icons.circle_outlined,
    color: ExchangeColors.secondaryInk,
    background: Color(0xFFE9EEF1),
  ),
};
