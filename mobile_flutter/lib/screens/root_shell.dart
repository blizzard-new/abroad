import 'dart:ui';

import 'package:flutter/material.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/daylight_surface.dart';
import '../state/exchange_store.dart';
import 'account_screen.dart';
import 'application_documents_screen.dart';
import 'community_screen.dart';
import 'deadlines_screen.dart';
import 'home_screen.dart';
import 'journey_screen.dart';
import 'forum_screen.dart';
import 'schools_screen.dart';

Future<void> showUniversityPickerSheet(BuildContext context) async {
  final store = ExchangeStoreScope.of(context, listen: false);
  final selected = await showModalBottomSheet<String>(
    context: context,
    showDragHandle: true,
    isScrollControlled: true,
    backgroundColor: ExchangeColors.surface,
    builder: (sheetContext) {
      return SafeArea(
        child: DraggableScrollableSheet(
          expand: false,
          initialChildSize: 0.72,
          maxChildSize: 0.9,
          minChildSize: 0.45,
          builder: (_, scrollController) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 4, 20, 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '切換就讀學校（${store.universities.length} 校）',
                        style: Theme.of(sheetContext).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '選擇你的學校，查看適用的交換資訊。',
                        style: Theme.of(sheetContext).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1),
                Expanded(
                  child: ListView.separated(
                    controller: scrollController,
                    itemCount: store.universities.length,
                    separatorBuilder: (_, _) => const Divider(height: 1),
                    itemBuilder: (_, itemIndex) {
                      final university = store.universities[itemIndex];
                      final isSelected =
                          university.schoolName == store.selectedUniversity;
                      return ListTile(
                        minTileHeight: 60,
                        leading: Icon(
                          isSelected
                              ? Icons.check_circle_rounded
                              : Icons.school_outlined,
                          color: isSelected
                              ? ExchangeColors.teal
                              : ExchangeColors.secondaryInk,
                        ),
                        title: Text(
                          university.schoolName,
                          style: TextStyle(
                            fontWeight: isSelected
                                ? FontWeight.w600
                                : FontWeight.w400,
                          ),
                        ),
                        subtitle: Text(
                          university.partnerCount > 0
                              ? '${university.shortName} · ${university.partnerCount} 所合作校'
                              : university.shortName,
                        ),
                        trailing: isSelected
                            ? const Text(
                                '目前選擇',
                                style: TextStyle(
                                  color: ExchangeColors.teal,
                                  fontWeight: FontWeight.w600,
                                ),
                              )
                            : null,
                        onTap: () => Navigator.of(
                          sheetContext,
                        ).pop(university.schoolName),
                      );
                    },
                  ),
                ),
              ],
            );
          },
        ),
      );
    },
  );
  if (selected != null && selected.isNotEmpty) {
    await store.selectUniversity(selected);
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
    return ExchangePageBackground(
      child: Scaffold(
        extendBody: true,
        body: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 840),
            child: IndexedStack(index: index, children: pages),
          ),
        ),
        bottomNavigationBar: SafeArea(
          top: false,
          minimum: const EdgeInsets.fromLTRB(16, 0, 16, 12),
          child: LiquidControlSurface(
            radius: 30,
            child: Padding(
              key: const ValueKey('main-navigation'),
              padding: const EdgeInsets.all(8),
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
                          borderRadius: BorderRadius.circular(24),
                          onTap: () => store.selectMainTab(i),
                          child: AnimatedContainer(
                            duration: Duration(
                              milliseconds: reduceEffects ? 0 : 180,
                            ),
                            constraints: const BoxConstraints(minHeight: 52),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(24),
                              color: i == index
                                  ? ExchangeColors.teal.withValues(alpha: .17)
                                  : Colors.transparent,
                              border: Border.all(
                                color: i == index
                                    ? ExchangeColors.teal.withValues(alpha: .38)
                                    : Colors.transparent,
                              ),
                            ),
                            child: Icon(
                              icons[i],
                              size: 26,
                              color: i == index
                                  ? ExchangeColors.teal
                                  : ExchangeColors.secondaryInk,
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

class CguBoardShell extends StatefulWidget {
  const CguBoardShell({super.key});

  @override
  State<CguBoardShell> createState() => _CguBoardShellState();
}

class _CguBoardShellState extends State<CguBoardShell> {
  int index = 0;

  void select(int value) => setState(() => index = value);

  void openAccount() {
    Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => const AccountScreen()));
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final pageTitles = [
      '我的交換計畫',
      '找交換學校',
      '申請文件',
      '申請時程',
      store.activeUniversity.boardTitleLabel,
    ];
    final pages = [
      HomeScreen(onSelectTab: select, showHeader: false),
      const SchoolsScreen(showPageHeader: false),
      const ApplicationDocumentsScreen(),
      const DeadlinesScreen(embedded: true),
      CommunityScreen(
        initialSchool: store.selectedUniversity,
        lockedToInitialSchool: true,
      ),
    ];

    return ExchangePageBackground(
      child: Scaffold(
        extendBody: true,
        body: Column(
          children: [
            SafeArea(
              bottom: false,
              child: _BoardContextBar(
                boardTitle: '${store.activeUniversity.schoolName}板',
                pageTitle: pageTitles[index],
                onSwitchSchool: () => showUniversityPickerSheet(context),
                onAccount: openAccount,
              ),
            ),
            Expanded(
              child: MediaQuery.removePadding(
                context: context,
                removeTop: true,
                child: IndexedStack(index: index, children: pages),
              ),
            ),
          ],
        ),
        bottomNavigationBar: SafeArea(
          top: false,
          minimum: const EdgeInsets.fromLTRB(10, 0, 10, 8),
          child: _LiquidNavigationBar(
            selectedIndex: index,
            items: [
              _LiquidNavItem(
                icon: Icons.home_outlined,
                selectedIcon: Icons.home_rounded,
                label: '計畫',
                onTap: () => select(0),
              ),
              _LiquidNavItem(
                icon: Icons.search_rounded,
                selectedIcon: Icons.search_rounded,
                label: '找學校',
                onTap: () => select(1),
              ),
              _LiquidNavItem(
                icon: Icons.edit_document,
                selectedIcon: Icons.edit_document,
                label: '填文件',
                onTap: () => select(2),
              ),
              _LiquidNavItem(
                icon: Icons.calendar_month_outlined,
                selectedIcon: Icons.calendar_month_rounded,
                label: '時程',
                onTap: () => select(3),
              ),
              _LiquidNavItem(
                icon: Icons.forum_outlined,
                selectedIcon: Icons.forum_rounded,
                label: '討論板',
                onTap: () => select(4),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _BoardContextBar extends StatelessWidget {
  const _BoardContextBar({
    required this.boardTitle,
    required this.pageTitle,
    required this.onSwitchSchool,
    required this.onAccount,
  });

  final String boardTitle;
  final String pageTitle;
  final VoidCallback onSwitchSchool;
  final VoidCallback onAccount;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 6, 12, 8),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(18),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
          child: Container(
            constraints: const BoxConstraints(minHeight: 64),
            padding: const EdgeInsets.symmetric(horizontal: 8),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .68),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: Colors.white.withValues(alpha: .92)),
            ),
            child: Row(
              children: [
                IconButton(
                  tooltip: '返回留學首頁',
                  onPressed: () => Navigator.of(context).maybePop(),
                  constraints: const BoxConstraints(
                    minWidth: 48,
                    minHeight: 48,
                  ),
                  icon: const Icon(Icons.arrow_back_rounded),
                ),
                const ExchangeIconBadge(
                  Icons.school_outlined,
                  color: ExchangeColors.blue,
                  background: ExchangeColors.blueSoft,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: InkWell(
                    borderRadius: BorderRadius.circular(12),
                    onTap: onSwitchSchool,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 6),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Flexible(
                                child: Text(
                                  boardTitle,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: Theme.of(
                                    context,
                                  ).textTheme.titleMedium,
                                ),
                              ),
                              const SizedBox(width: 4),
                              const Icon(
                                Icons.unfold_more_rounded,
                                size: 18,
                                color: ExchangeColors.secondaryInk,
                              ),
                            ],
                          ),
                          Text(
                            pageTitle,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                IconButton(
                  tooltip: '切換學校',
                  onPressed: onSwitchSchool,
                  constraints: const BoxConstraints(
                    minWidth: 44,
                    minHeight: 48,
                  ),
                  icon: const Icon(Icons.swap_horiz_rounded),
                ),
                IconButton(
                  tooltip: '我的帳號',
                  onPressed: onAccount,
                  constraints: const BoxConstraints(
                    minWidth: 48,
                    minHeight: 48,
                  ),
                  icon: const Icon(Icons.person_outline_rounded),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _LiquidNavigationBar extends StatelessWidget {
  const _LiquidNavigationBar({
    required this.selectedIndex,
    required this.items,
  });

  final int selectedIndex;
  final List<_LiquidNavItem> items;

  @override
  Widget build(BuildContext context) {
    assert(items.length == 5);
    return RepaintBoundary(
      child: LayoutBuilder(
        builder: (context, constraints) {
          const gap = 5.0;
          final circleSize = ((constraints.maxWidth - 120 - gap * 4) / 4)
              .clamp(48.0, 60.0)
              .toDouble();
          final centerWidth = constraints.maxWidth - circleSize * 4 - gap * 4;

          final systemScale = MediaQuery.textScalerOf(
            context,
          ).scale(1).clamp(1.0, 1.5);
          final barHeight = 72 + (systemScale - 1) * 18;

          return SizedBox(
            height: barHeight,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                _LiquidDestination(
                  width: circleSize,
                  icon: items[0].icon,
                  selectedIcon: items[0].selectedIcon,
                  label: items[0].label,
                  selected: selectedIndex == 0,
                  onTap: items[0].onTap,
                ),
                const SizedBox(width: gap),
                _LiquidDestination(
                  width: circleSize,
                  icon: items[1].icon,
                  selectedIcon: items[1].selectedIcon,
                  label: items[1].label,
                  selected: selectedIndex == 1,
                  onTap: items[1].onTap,
                ),
                const SizedBox(width: gap),
                _LiquidDestination(
                  width: centerWidth,
                  icon: items[2].icon,
                  selectedIcon: items[2].selectedIcon,
                  label: items[2].label,
                  showLabel: true,
                  selected: selectedIndex == 2,
                  onTap: items[2].onTap,
                ),
                const SizedBox(width: gap),
                _LiquidDestination(
                  width: circleSize,
                  icon: items[3].icon,
                  selectedIcon: items[3].selectedIcon,
                  label: items[3].label,
                  selected: selectedIndex == 3,
                  onTap: items[3].onTap,
                ),
                const SizedBox(width: gap),
                _LiquidDestination(
                  width: circleSize,
                  icon: items[4].icon,
                  selectedIcon: items[4].selectedIcon,
                  label: items[4].label,
                  selected: selectedIndex == 4,
                  onTap: items[4].onTap,
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _LiquidNavItem {
  const _LiquidNavItem({
    required this.icon,
    required this.selectedIcon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final IconData selectedIcon;
  final String label;
  final VoidCallback onTap;
}

class _LiquidDestination extends StatelessWidget {
  const _LiquidDestination({
    required this.width,
    required this.icon,
    required this.selectedIcon,
    required this.label,
    required this.selected,
    required this.onTap,
    this.showLabel = false,
  });

  final double width;
  final IconData icon;
  final IconData selectedIcon;
  final String label;
  final bool selected;
  final VoidCallback onTap;
  final bool showLabel;

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(999);
    final foreground = selected
        ? ExchangeColors.ink
        : ExchangeColors.secondaryInk;
    final height = selected ? 64.0 : 60.0;

    return Semantics(
      button: true,
      selected: selected,
      label: label,
      child: Tooltip(
        message: label,
        child: AnimatedScale(
          scale: selected ? 1.045 : 1,
          duration: const Duration(milliseconds: 260),
          curve: Curves.easeOutBack,
          child: AnimatedContainer(
            width: width,
            height: height,
            duration: const Duration(milliseconds: 240),
            curve: Curves.easeOutCubic,
            decoration: BoxDecoration(
              borderRadius: radius,
              boxShadow: [
                BoxShadow(
                  color: const Color(
                    0xFF17313E,
                  ).withValues(alpha: selected ? .2 : .13),
                  blurRadius: selected ? 30 : 24,
                  spreadRadius: -5,
                  offset: const Offset(0, 13),
                ),
                BoxShadow(
                  color: Colors.white.withValues(alpha: .78),
                  blurRadius: 10,
                  spreadRadius: -3,
                  offset: const Offset(0, -4),
                ),
              ],
            ),
            child: ClipRRect(
              borderRadius: radius,
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 34, sigmaY: 34),
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 240),
                      decoration: BoxDecoration(
                        borderRadius: radius,
                        gradient: LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: selected
                              ? [
                                  Colors.white.withValues(alpha: .78),
                                  ExchangeColors.tealSoft.withValues(alpha: .5),
                                  Colors.white.withValues(alpha: .48),
                                ]
                              : [
                                  Colors.white.withValues(alpha: .66),
                                  ExchangeColors.blueSoft.withValues(alpha: .3),
                                  Colors.white.withValues(alpha: .4),
                                ],
                          stops: const [0, .52, 1],
                        ),
                        border: Border.all(
                          color: selected
                              ? ExchangeColors.teal.withValues(alpha: .3)
                              : Colors.white.withValues(alpha: .9),
                          width: selected ? 1.35 : 1,
                        ),
                      ),
                    ),
                    Positioned(
                      top: 1,
                      left: showLabel ? 25 : 11,
                      right: showLabel ? 25 : 11,
                      child: Container(
                        height: 1.4,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(999),
                          gradient: LinearGradient(
                            colors: [
                              Colors.white.withValues(alpha: 0),
                              Colors.white,
                              Colors.white.withValues(alpha: 0),
                            ],
                          ),
                        ),
                      ),
                    ),
                    Positioned(
                      bottom: -9,
                      left: showLabel ? 20 : 7,
                      right: showLabel ? 20 : 7,
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 240),
                        height: 20,
                        decoration: BoxDecoration(
                          color:
                              (selected
                                      ? ExchangeColors.teal
                                      : ExchangeColors.blue)
                                  .withValues(alpha: selected ? .14 : .055),
                          borderRadius: BorderRadius.circular(999),
                        ),
                      ),
                    ),
                    Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: radius,
                        onTap: onTap,
                        splashColor: ExchangeColors.teal.withValues(alpha: .1),
                        highlightColor: Colors.white.withValues(alpha: .14),
                        child: Center(
                          child: AnimatedSwitcher(
                            duration: const Duration(milliseconds: 190),
                            child: showLabel
                                ? Row(
                                    key: ValueKey(selected),
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(
                                        selected ? selectedIcon : icon,
                                        color: foreground,
                                        size: 27,
                                      ),
                                      const SizedBox(width: 8),
                                      Text(
                                        label,
                                        style: Theme.of(context)
                                            .textTheme
                                            .labelLarge
                                            ?.copyWith(
                                              color: foreground,
                                              fontWeight: FontWeight.w800,
                                            ),
                                      ),
                                    ],
                                  )
                                : Icon(
                                    selected ? selectedIcon : icon,
                                    key: ValueKey(selected),
                                    color: foreground,
                                    size: 28,
                                  ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
