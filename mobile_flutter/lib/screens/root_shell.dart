import 'dart:ui';

import 'package:flutter/material.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import 'account_screen.dart';
import 'application_documents_screen.dart';
import 'community_screen.dart';
import 'deadlines_screen.dart';
import 'global_community_screen.dart';
import 'home_screen.dart';
import 'schools_screen.dart';

class RootShell extends StatefulWidget {
  const RootShell({super.key});

  @override
  State<RootShell> createState() => _RootShellState();
}

class _RootShellState extends State<RootShell> {
  final globalCommunityKey = GlobalKey<GlobalCommunityScreenState>();
  int globalPageIndex = 0;
  CommunityFeed globalFeed = CommunityFeed.all;

  void _showGlobalFeed(CommunityFeed feed) {
    setState(() {
      globalPageIndex = 0;
      globalFeed = feed;
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      globalCommunityKey.currentState?.selectFeed(feed);
    });
  }

  void _showAccount() => setState(() => globalPageIndex = 1);

  void _compose() {
    setState(() => globalPageIndex = 0);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      globalCommunityKey.currentState?.openComposer();
    });
  }

  Future<void> _openCguBoard() async {
    await Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => const CguBoardShell()));
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      GlobalCommunityScreen(
        key: globalCommunityKey,
        initialFeed: CommunityFeed.all,
        includeCguFeed: false,
        showCguChatShortcut: false,
        onOpenCguBoard: _openCguBoard,
        onFeedChanged: (feed) {
          if (globalFeed != feed && mounted) setState(() => globalFeed = feed);
        },
      ),
      const AccountScreen(),
    ];
    final selectedDestination = globalPageIndex == 1
        ? 4
        : globalFeed == CommunityFeed.following
        ? 1
        : 0;

    return ExchangePageBackground(
      child: Scaffold(
        extendBody: true,
        body: IndexedStack(index: globalPageIndex, children: pages),
        bottomNavigationBar: SafeArea(
          top: false,
          minimum: const EdgeInsets.fromLTRB(10, 0, 10, 8),
          child: _LiquidNavigationBar(
            selectedIndex: selectedDestination,
            items: [
              _LiquidNavItem(
                icon: Icons.home_outlined,
                selectedIcon: Icons.home_rounded,
                label: '留學首頁',
                onTap: () => _showGlobalFeed(CommunityFeed.all),
              ),
              _LiquidNavItem(
                icon: Icons.rss_feed_outlined,
                selectedIcon: Icons.rss_feed_rounded,
                label: '追蹤',
                onTap: () => _showGlobalFeed(CommunityFeed.following),
              ),
              _LiquidNavItem(
                icon: Icons.edit_square,
                selectedIcon: Icons.edit_square,
                label: '發文',
                onTap: _compose,
              ),
              _LiquidNavItem(
                icon: Icons.school_outlined,
                selectedIcon: Icons.school_rounded,
                label: '長庚板',
                onTap: _openCguBoard,
              ),
              _LiquidNavItem(
                icon: Icons.person_outline_rounded,
                selectedIcon: Icons.person_rounded,
                label: '我的',
                onTap: _showAccount,
              ),
            ],
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
    final pageTitles = ['我的交換計畫', '找交換學校', '申請文件', '申請時程', '長庚討論板'];
    final pages = [
      HomeScreen(onSelectTab: select, showHeader: false),
      const SchoolsScreen(showPageHeader: false),
      const ApplicationDocumentsScreen(),
      const DeadlinesScreen(),
      const CommunityScreen(
        initialSchool: cguCommunityBoard,
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
                pageTitle: pageTitles[index],
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
  const _BoardContextBar({required this.pageTitle, required this.onAccount});

  final String pageTitle;
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
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '長庚大學板',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.titleMedium,
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
