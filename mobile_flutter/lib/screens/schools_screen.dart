import 'dart:ui';

import 'package:flutter/material.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/school_visuals.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import 'school_detail_screen.dart';

class SchoolsScreen extends StatefulWidget {
  const SchoolsScreen({super.key, this.showPageHeader = true});

  final bool showPageHeader;

  @override
  State<SchoolsScreen> createState() => _SchoolsScreenState();
}

class _SchoolsScreenState extends State<SchoolsScreen> {
  final searchController = TextEditingController();
  String appliedStoreQuery = '';

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final query = ExchangeStoreScope.of(context).schoolSearchQuery;
    if (query != appliedStoreQuery) {
      appliedStoreQuery = query;
      searchController.text = query;
    }
  }

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final dashboard = store.dashboard;
    final query = searchController.text.trim().toLowerCase();
    final partners =
        (dashboard?.partnerUniversities ?? const <PartnerUniversity>[])
            .where(
              (school) =>
                  query.isEmpty || school.searchableText.contains(query),
            )
            .toList();

    return SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: store.refresh,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 110),
          children: [
            if (widget.showPageHeader) ...[
              const ExchangeSectionHeader(
                eyebrow: '長庚大學合作校',
                title: '找到適合你的學校',
              ),
              const SizedBox(height: 14),
            ],
            _LiquidGlassSearchField(
              controller: searchController,
              onChanged: (value) {
                appliedStoreQuery = value;
                store.setSchoolSearchQuery(value);
                setState(() {});
              },
              onClear: searchController.text.isEmpty
                  ? null
                  : () {
                      searchController.clear();
                      appliedStoreQuery = '';
                      store.setSchoolSearchQuery('');
                      setState(() {});
                    },
            ),
            const SizedBox(height: 20),
            if (store.isLoading && dashboard == null)
              const LoadingCards(count: 5)
            else if (store.error != null && dashboard == null)
              InlineError(message: store.error!, onRetry: store.refresh)
            else if (partners.isEmpty)
              const EmptyState(
                icon: Icons.search_off_rounded,
                title: '沒有符合條件的學校',
                message: '試著縮短關鍵字，再重新搜尋。',
              )
            else ...[
              Text(
                '顯示 ${partners.length} 間學校',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 10),
              LayoutBuilder(
                builder: (context, constraints) {
                  final twoColumns = constraints.maxWidth >= 720;
                  final cardWidth = twoColumns
                      ? (constraints.maxWidth - 14) / 2
                      : constraints.maxWidth;
                  return Wrap(
                    spacing: 14,
                    runSpacing: 14,
                    children: partners
                        .map(
                          (school) => SizedBox(
                            width: cardWidth,
                            child: _SchoolCard(school: school, store: store),
                          ),
                        )
                        .toList(),
                  );
                },
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SchoolCard extends StatefulWidget {
  const _SchoolCard({required this.school, required this.store});

  final PartnerUniversity school;
  final ExchangeStore store;

  @override
  State<_SchoolCard> createState() => _SchoolCardState();
}

class _SchoolCardState extends State<_SchoolCard> {
  bool expanded = false;

  void _openDetail() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => SchoolDetailScreen(school: widget.school),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final school = widget.school;
    final store = widget.store;
    final isFavorite = store.favorites.contains(school.schoolName);
    final summary = studentFacingText(school.mobileListSummary);
    return GlassCard(
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(8),
              onTap: () => setState(() => expanded = !expanded),
              child: Semantics(
                button: true,
                expanded: expanded,
                label: '${school.schoolName}詳細資訊',
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(12, 12, 8, 12),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: SizedBox(
                          width: 92,
                          height: 82,
                          child: SchoolPhoto(school: school),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: ExchangeColors.blueSoft.withValues(
                                  alpha: .78,
                                ),
                                borderRadius: BorderRadius.circular(999),
                              ),
                              child: Text(
                                school.country,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: Theme.of(context).textTheme.bodySmall
                                    ?.copyWith(
                                      color: ExchangeColors.blue,
                                      fontWeight: FontWeight.w800,
                                      fontSize: 11,
                                    ),
                              ),
                            ),
                            const SizedBox(height: 5),
                            Text(
                              school.schoolName,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context).textTheme.titleMedium
                                  ?.copyWith(fontWeight: FontWeight.w800),
                            ),
                            if (summary.isNotEmpty) ...[
                              const SizedBox(height: 4),
                              Text(
                                summary,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ],
                          ],
                        ),
                      ),
                      SizedBox.square(
                        dimension: 44,
                        child: Center(
                          child: AnimatedRotation(
                            turns: expanded ? .5 : 0,
                            duration: const Duration(milliseconds: 220),
                            child: const Icon(
                              Icons.keyboard_arrow_down_rounded,
                              color: ExchangeColors.secondaryInk,
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
          AnimatedSize(
            duration: const Duration(milliseconds: 240),
            curve: Curves.easeOutCubic,
            child: expanded
                ? Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Divider(),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(14, 14, 14, 16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Wrap(
                              spacing: 7,
                              runSpacing: 7,
                              children: [
                                if (school.displayStudyPeriod.isNotEmpty)
                                  _FactChip(
                                    icon: Icons.schedule_rounded,
                                    text: school.displayStudyPeriod,
                                  ),
                                if (school.quota.isNotEmpty)
                                  _FactChip(
                                    icon: Icons.people_outline_rounded,
                                    text: '名額 ${school.quota}',
                                  ),
                                if (school
                                    .displayApplicationDeadline
                                    .isNotEmpty)
                                  const _FactChip(
                                    icon: Icons.event_rounded,
                                    text: '截止日已整理',
                                  ),
                                if (school
                                    .studentSummaryZh
                                    .translatedFromEnglish)
                                  const _FactChip(
                                    icon: Icons.translate_rounded,
                                    text: '中文重點',
                                  ),
                              ],
                            ),
                            const SizedBox(height: 14),
                            Row(
                              children: [
                                Expanded(
                                  child: FilledButton.icon(
                                    onPressed: _openDetail,
                                    icon: const Icon(
                                      Icons.arrow_forward_rounded,
                                    ),
                                    label: const Text('查看完整資訊'),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                IconButton.outlined(
                                  tooltip: isFavorite ? '取消收藏' : '加入收藏',
                                  onPressed: () =>
                                      store.toggleFavorite(school.schoolName),
                                  icon: Icon(
                                    isFavorite
                                        ? Icons.bookmark_rounded
                                        : Icons.bookmark_outline_rounded,
                                    color: isFavorite
                                        ? ExchangeColors.teal
                                        : ExchangeColors.secondaryInk,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  )
                : const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}

class _LiquidGlassSearchField extends StatelessWidget {
  const _LiquidGlassSearchField({
    required this.controller,
    required this.onChanged,
    this.onClear,
  });

  final TextEditingController controller;
  final ValueChanged<String> onChanged;
  final VoidCallback? onClear;

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(8);
    return Container(
      decoration: BoxDecoration(
        borderRadius: radius,
        boxShadow: const [
          BoxShadow(
            color: Color(0x161F3045),
            blurRadius: 30,
            spreadRadius: -8,
            offset: Offset(0, 14),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: radius,
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 26, sigmaY: 26),
          child: DecoratedBox(
            decoration: BoxDecoration(
              borderRadius: radius,
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Colors.white.withValues(alpha: .78),
                  const Color(0xFFE7F2F5).withValues(alpha: .48),
                  Colors.white.withValues(alpha: .54),
                ],
              ),
              border: Border.all(color: Colors.white.withValues(alpha: .94)),
            ),
            child: TextField(
              controller: controller,
              onChanged: onChanged,
              textInputAction: TextInputAction.search,
              decoration: InputDecoration(
                hintText: '搜尋學校、國家或條件',
                prefixIcon: const Icon(Icons.search_rounded),
                suffixIcon: onClear == null
                    ? null
                    : IconButton(
                        tooltip: '清除搜尋',
                        onPressed: onClear,
                        icon: const Icon(Icons.close_rounded),
                      ),
                filled: false,
                border: InputBorder.none,
                enabledBorder: InputBorder.none,
                focusedBorder: InputBorder.none,
                constraints: const BoxConstraints(minHeight: 54),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _FactChip extends StatelessWidget {
  const _FactChip({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: .48),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.white.withValues(alpha: .82)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: ExchangeColors.teal),
          const SizedBox(width: 6),
          Text(
            text,
            style: Theme.of(
              context,
            ).textTheme.bodySmall?.copyWith(color: ExchangeColors.ink),
          ),
        ],
      ),
    );
  }
}
