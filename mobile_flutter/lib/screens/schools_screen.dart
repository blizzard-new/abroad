import 'dart:ui';

import 'package:flutter/material.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
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
  String country = '';
  bool savedOnly = false;

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
                  (query.isEmpty || school.searchableText.contains(query)) &&
                  (country.isEmpty || school.country == country) &&
                  (!savedOnly || store.favorites.contains(school.schoolName)),
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
              StudentHeading(
                '找學校',
                subtitle: store.selectedUniversity,
                action: IconButton(
                  tooltip: '找學校指南',
                  icon: const Icon(Icons.help_outline_rounded),
                  onPressed: () => showStudentGuide(
                    context,
                    title: '找到適合的學校',
                    steps: const [
                      (
                        icon: Icons.search_rounded,
                        title: '搜尋與篩選',
                        detail: '輸入校名或條件，選擇國家縮小範圍。',
                      ),
                      (
                        icon: Icons.bookmark_outline_rounded,
                        title: '收藏志願',
                        detail: '點書籤留下學校；點卡片查看完整條件與官方來源。',
                      ),
                      (
                        icon: Icons.verified_outlined,
                        title: '確認當期規定',
                        detail: '名額、資格與截止日以當期官方公告為準。',
                      ),
                    ],
                  ),
                ),
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
            const SizedBox(height: 12),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  FilterChip(
                    avatar: Icon(
                      savedOnly
                          ? Icons.bookmark_rounded
                          : Icons.bookmark_outline_rounded,
                      size: 20,
                    ),
                    label: Text('收藏 ${store.favorites.length}'),
                    selected: savedOnly,
                    onSelected: (value) => setState(() => savedOnly = value),
                  ),
                  const SizedBox(width: 8),
                  ChoiceChip(
                    label: const Text('全部國家'),
                    selected: country.isEmpty,
                    onSelected: (_) => setState(() => country = ''),
                  ),
                  ...{
                        for (final school
                            in dashboard?.partnerUniversities ??
                                <PartnerUniversity>[])
                          school.country,
                      }
                      .where((c) => c.isNotEmpty)
                      .map(
                        (c) => Padding(
                          padding: const EdgeInsets.only(left: 8),
                          child: ChoiceChip(
                            label: Text(c),
                            selected: country == c,
                            onSelected: (_) => setState(() => country = c),
                          ),
                        ),
                      ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            if (store.isLoading && dashboard == null)
              const LoadingCards(count: 5)
            else if (store.error != null && dashboard == null)
              InlineError(message: store.error!, onRetry: store.refresh)
            else if (partners.isEmpty)
              StudentEmptyState(
                icon: savedOnly
                    ? Icons.bookmark_outline_rounded
                    : Icons.search_off_rounded,
                title: savedOnly && store.favorites.isEmpty
                    ? '先收藏一所學校'
                    : '沒有符合的學校',
                detail: savedOnly && store.favorites.isEmpty
                    ? '點學校旁的書籤，就會留在這裡。'
                    : '換個條件再試試。',
                action: OutlinedButton(
                  onPressed: () {
                    setState(() {
                      country = '';
                      savedOnly = false;
                      searchController.clear();
                      appliedStoreQuery = '';
                    });
                    store.setSchoolSearchQuery('');
                  },
                  child: const Text('查看全部學校'),
                ),
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

class _SchoolCard extends StatelessWidget {
  const _SchoolCard({required this.school, required this.store});
  final PartnerUniversity school;
  final ExchangeStore store;
  @override
  Widget build(BuildContext context) {
    final saved = store.favorites.contains(school.schoolName);
    return GlassCard(
      padding: const EdgeInsets.all(16),
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => SchoolDetailScreen(school: school)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: SizedBox(
              width: 72,
              height: 88,
              child: SchoolPhoto(school: school),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                StudentIconLabel(Icons.place_outlined, school.country),
                const SizedBox(height: 8),
                Text(
                  school.schoolName,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                if (school.displayStudyPeriod.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    school.displayStudyPeriod,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ],
            ),
          ),
          IconButton(
            tooltip: saved ? '取消收藏' : '加入收藏',
            onPressed: () => store.toggleFavorite(school.schoolName),
            icon: Icon(
              saved ? Icons.bookmark_rounded : Icons.bookmark_outline_rounded,
              color: saved ? ExchangeColors.teal : ExchangeColors.secondaryInk,
            ),
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
    final radius = BorderRadius.circular(20);
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
          filter: ImageFilter.blur(
            sigmaX:
                MediaQuery.disableAnimationsOf(context) ||
                    MediaQuery.highContrastOf(context)
                ? 0
                : 16,
            sigmaY:
                MediaQuery.disableAnimationsOf(context) ||
                    MediaQuery.highContrastOf(context)
                ? 0
                : 16,
          ),
          child: DecoratedBox(
            decoration: BoxDecoration(
              borderRadius: radius,
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  const Color(0xCF34415F),
                  const Color(0xDB22314A),
                  const Color(0xD51C2540),
                ],
              ),
              border: Border.all(color: ExchangeColors.line),
            ),
            child: TextField(
              controller: controller,
              onChanged: onChanged,
              textInputAction: TextInputAction.search,
              decoration: InputDecoration(
                hintText: '搜尋校名或條件',
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
