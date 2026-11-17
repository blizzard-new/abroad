import 'package:flutter/material.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import 'account_screen.dart';
import 'application_documents_screen.dart';
import 'forum_screen.dart';
import 'journey_screen.dart';
import 'schools_screen.dart';

String _normalizeUniversityQuery(String input) =>
    input.trim().toLowerCase().replaceAll('台', '臺');

bool _matchesUniversity(SupportedUniversity university, String rawQuery) {
  final query = _normalizeUniversityQuery(rawQuery);
  if (query.isEmpty) return true;
  final haystack = _normalizeUniversityQuery([
    university.id,
    university.schoolName,
    university.shortName,
    university.englishName,
    ...university.aliases,
  ].join(' '));
  return haystack.contains(query);
}

Future<void> showUniversityPickerSheet(BuildContext context) async {
  final store = ExchangeStoreScope.of(context, listen: false);
  final selected = await showModalBottomSheet<String>(
    context: context,
    showDragHandle: true,
    isScrollControlled: true,
    backgroundColor: ExchangeColors.surface,
    builder: (sheetContext) => _UniversityPickerSheet(store: store),
  );
  if (selected != null && selected.isNotEmpty) {
    await store.selectUniversity(selected);
  }
}

class _UniversityPickerSheet extends StatefulWidget {
  const _UniversityPickerSheet({required this.store});

  final ExchangeStore store;

  @override
  State<_UniversityPickerSheet> createState() => _UniversityPickerSheetState();
}

class _UniversityPickerSheetState extends State<_UniversityPickerSheet> {
  final searchController = TextEditingController();

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final store = widget.store;
    final query = searchController.text;
    final currentName = store.selectedUniversity;
    final homeName = store.account?.homeUniversity.trim() ?? '';
    final canSwitchToHome =
        homeName.isNotEmpty &&
        homeName != currentName &&
        store.universities.any((u) => u.schoolName == homeName);

    final filtered = store.universities
        .where((u) => _matchesUniversity(u, query))
        .toList();
    filtered.sort((left, right) {
      final leftSelected = left.schoolName == currentName ? 0 : 1;
      final rightSelected = right.schoolName == currentName ? 0 : 1;
      if (leftSelected != rightSelected) {
        return leftSelected.compareTo(rightSelected);
      }
      return 0;
    });

    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.viewInsetsOf(context).bottom,
        ),
        child: DraggableScrollableSheet(
          expand: false,
          initialChildSize: 0.78,
          maxChildSize: 0.92,
          minChildSize: 0.5,
          builder: (_, scrollController) {
            return Column(
              key: const ValueKey('university-picker-sheet'),
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 4, 20, 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '切換就讀學校（${store.universities.length} 校）',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontFeatures: ExchangeColors.tabularFigures,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '輸入校名、簡稱或英文縮寫快速定位。',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        key: const ValueKey('university-picker-search'),
                        controller: searchController,
                        textInputAction: TextInputAction.search,
                        onChanged: (_) => setState(() {}),
                        decoration: InputDecoration(
                          labelText: '搜尋就讀學校',
                          floatingLabelBehavior: FloatingLabelBehavior.never,
                          hintText: '搜尋大學名稱、簡稱或代碼，例如 台大 / NTU / CGU',
                          prefixIcon: const Icon(Icons.search_rounded),
                          suffixIcon: query.isEmpty
                              ? null
                              : IconButton(
                                  tooltip: '清除搜尋',
                                  onPressed: () {
                                    searchController.clear();
                                    setState(() {});
                                  },
                                  icon: const Icon(Icons.close_rounded),
                                ),
                        ),
                      ),
                      if (canSwitchToHome) ...[
                        const SizedBox(height: 10),
                        ActionChip(
                          avatar: const Icon(Icons.home_work_outlined, size: 16),
                          label: Text('切回帳號母校：$homeName'),
                          onPressed: () =>
                              Navigator.of(context).pop(homeName),
                        ),
                      ],
                    ],
                  ),
                ),
                const Divider(height: 1),
                Expanded(
                  child: filtered.isEmpty
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.all(24),
                            child: Text(
                              '找不到符合「${query.trim()}」的學校。',
                              style: Theme.of(context).textTheme.bodyMedium,
                              textAlign: TextAlign.center,
                            ),
                          ),
                        )
                      : ListView.separated(
                          controller: scrollController,
                          itemCount: filtered.length,
                          separatorBuilder: (_, _) => const Divider(height: 1),
                          itemBuilder: (_, itemIndex) {
                            final university = filtered[itemIndex];
                            final isSelected =
                                university.schoolName == currentName;
                            return ListTile(
                              minTileHeight: 60,
                              tileColor: isSelected
                                  ? ExchangeColors.tealSoft
                                  : null,
                              leading: Icon(
                                isSelected
                                    ? Icons.check_circle_rounded
                                    : Icons.school_outlined,
                                color: isSelected
                                    ? ExchangeColors.actionBlue
                                    : ExchangeColors.secondaryInk,
                              ),
                              title: Text(
                                university.schoolName,
                                style: TextStyle(
                                  fontWeight: isSelected
                                      ? FontWeight.w700
                                      : FontWeight.w500,
                                  color: ExchangeColors.ink,
                                ),
                              ),
                              subtitle: Text(
                                university.partnerCount > 0
                                    ? '${university.shortName} · ${university.partnerCount} 所合作校'
                                    : university.shortName,
                                style: Theme.of(context).textTheme.bodySmall
                                    ?.copyWith(
                                      fontFeatures:
                                          ExchangeColors.tabularFigures,
                                    ),
                              ),
                              trailing: isSelected
                                  ? const Text(
                                      '目前選擇',
                                      style: TextStyle(
                                        color: ExchangeColors.actionBlue,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    )
                                  : null,
                              onTap: () => Navigator.of(
                                context,
                              ).pop(university.schoolName),
                            );
                          },
                        ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class RootShell extends StatefulWidget {
  const RootShell({super.key});

  @override
  State<RootShell> createState() => _RootShellState();
}

class _RootShellState extends State<RootShell> {
  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final index = store.navigationTab;
    final reduceEffects =
        MediaQuery.disableAnimationsOf(context) ||
        MediaQuery.highContrastOf(context);
    final pages = [
      JourneyScreen(onSelectTab: store.selectMainTab),
      const SchoolsScreen(),
      const ApplicationDocumentsScreen(),
      const ForumScreen(),
      const AccountScreen(),
    ];
    const labels = ['旅程', '學校', '申請', '論壇', '我的'];
    const icons = [
      Icons.explore_outlined,
      Icons.travel_explore_rounded,
      Icons.assignment_outlined,
      Icons.forum_outlined,
      Icons.person_outline_rounded,
    ];
    const activeIcons = [
      Icons.explore_rounded,
      Icons.travel_explore_rounded,
      Icons.assignment_rounded,
      Icons.forum_rounded,
      Icons.person_rounded,
    ];
    return ExchangePageBackground(
      child: Scaffold(
        body: Column(
          children: [
            const SafeArea(bottom: false, child: MetroLineBar()),
            Expanded(
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 840),
                  child: MediaQuery.removePadding(
                    context: context,
                    removeTop: true,
                    child: IndexedStack(
                      index: index,
                      children: [
                        for (var i = 0; i < pages.length; i++)
                          TickerMode(enabled: i == index, child: pages[i]),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
        bottomNavigationBar: DecoratedBox(
          decoration: const BoxDecoration(
            color: ExchangeColors.surface,
            border: Border(top: BorderSide(color: ExchangeColors.line)),
          ),
          child: SafeArea(
            top: false,
            child: Center(
              heightFactor: 1,
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 840),
                child: Padding(
                  key: const ValueKey('main-navigation'),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 6,
                    vertical: 6,
                  ),
                  child: Row(
                    children: List.generate(
                      labels.length,
                      (i) => Expanded(
                        child: Semantics(
                          label: labels[i],
                          selected: i == index,
                          button: true,
                          child: Tooltip(
                            message: labels[i],
                            excludeFromSemantics: true,
                            child: InkWell(
                              key: ValueKey('main-tab-$i'),
                              borderRadius: BorderRadius.circular(10),
                              onTap: () => store.selectMainTab(i),
                              child: AnimatedContainer(
                                duration: Duration(
                                  milliseconds: reduceEffects ? 0 : 140,
                                ),
                                constraints: const BoxConstraints(
                                  minHeight: 54,
                                  minWidth: 48,
                                ),
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 4,
                                  vertical: 6,
                                ),
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(10),
                                  color: i == index
                                      ? ExchangeColors.tealSoft
                                      : Colors.transparent,
                                ),
                                child: ExcludeSemantics(
                                  child: Column(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(
                                        i == index ? activeIcons[i] : icons[i],
                                        size: 22,
                                        color: i == index
                                            ? ExchangeColors.actionBlue
                                            : ExchangeColors.secondaryInk,
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        labels[i],
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        textAlign: TextAlign.center,
                                        style: TextStyle(
                                          fontSize: 12,
                                          height: 1.2,
                                          fontWeight: i == index
                                              ? FontWeight.w700
                                              : FontWeight.w500,
                                          color: i == index
                                              ? ExchangeColors.actionBlue
                                              : ExchangeColors.secondaryInk,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
