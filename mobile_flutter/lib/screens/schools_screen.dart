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

  Future<void> _showFilters(
    ExchangeStore store,
    List<PartnerUniversity> schools,
    List<String> countries,
  ) async {
    var selectedCountry = country;
    var onlySaved = savedOnly;
    final result =
        await showModalBottomSheet<({String country, bool savedOnly})>(
          context: context,
          isScrollControlled: true,
          showDragHandle: true,
          builder: (sheetContext) => StatefulBuilder(
            builder: (context, setSheetState) {
              final query = searchController.text.trim().toLowerCase();
              final matchCount = schools.where((school) {
                return (query.isEmpty ||
                        school.searchableText.contains(query)) &&
                    (selectedCountry.isEmpty ||
                        school.country == selectedCountry) &&
                    (!onlySaved || store.favorites.contains(school.schoolName));
              }).length;
              return SafeArea(
                top: false,
                child: FractionallySizedBox(
                  heightFactor: .82,
                  child: Padding(
                    key: const ValueKey('school-filter-sheet'),
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          '篩選學校',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '選擇想探索的國家與收藏。',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                        const SizedBox(height: 20),
                        Expanded(
                          child: SingleChildScrollView(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '國家或地區',
                                  style: Theme.of(
                                    context,
                                  ).textTheme.titleMedium,
                                ),
                                const SizedBox(height: 12),
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 8,
                                  children: [
                                    ChoiceChip(
                                      label: const Text('全部國家'),
                                      selected: selectedCountry.isEmpty,
                                      onSelected: (_) => setSheetState(
                                        () => selectedCountry = '',
                                      ),
                                    ),
                                    for (final item in countries)
                                      ChoiceChip(
                                        label: Text(item),
                                        selected: selectedCountry == item,
                                        onSelected: (_) => setSheetState(
                                          () => selectedCountry = item,
                                        ),
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 20),
                                const Divider(),
                                SwitchListTile(
                                  contentPadding: EdgeInsets.zero,
                                  title: const Text('只看收藏的學校'),
                                  subtitle: Text(
                                    '已收藏 ${store.favorites.length} 間',
                                  ),
                                  value: onlySaved,
                                  onChanged: (value) =>
                                      setSheetState(() => onlySaved = value),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            TextButton(
                              onPressed: () => setSheetState(() {
                                selectedCountry = '';
                                onlySaved = false;
                              }),
                              child: const Text('重設'),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: FilledButton(
                                onPressed: () =>
                                    Navigator.of(sheetContext).pop((
                                      country: selectedCountry,
                                      savedOnly: onlySaved,
                                    )),
                                child: Text('顯示 $matchCount 間學校'),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        );
    if (!mounted || result == null) return;
    setState(() {
      country = result.country;
      savedOnly = result.savedOnly;
    });
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final dashboard = store.dashboard;
    final query = searchController.text.trim().toLowerCase();
    final allSchools =
        dashboard?.partnerUniversities ?? const <PartnerUniversity>[];
    final countries = {
      for (final school in allSchools)
        if (school.country.isNotEmpty) school.country,
    }.toList()..sort();
    final partners = allSchools
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
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 0),
              sliver: SliverList.list(
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
                  Row(
                    children: [
                      OutlinedButton.icon(
                        key: const ValueKey('open-school-filters'),
                        onPressed: () =>
                            _showFilters(store, allSchools, countries),
                        icon: const Icon(Icons.tune_rounded, size: 18),
                        label: const Text('篩選'),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 10,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: SingleChildScrollView(
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
                                onSelected: (value) =>
                                    setState(() => savedOnly = value),
                              ),
                              const SizedBox(width: 8),
                              ChoiceChip(
                                label: const Text('全部國家'),
                                selected: country.isEmpty,
                                onSelected: (_) => setState(() => country = ''),
                              ),
                              ...countries.map(
                                (c) => Padding(
                                  padding: const EdgeInsets.only(left: 8),
                                  child: ChoiceChip(
                                    label: Text(c),
                                    selected: country == c,
                                    onSelected: (_) =>
                                        setState(() => country = c),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
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
                  ],
                ],
              ),
            ),
            if (partners.isNotEmpty)
              SliverPadding(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 128),
                sliver: SliverLayoutBuilder(
                  builder: (context, constraints) {
                    final columns = constraints.crossAxisExtent >= 720 ? 2 : 1;
                    return SliverList.separated(
                      itemCount: (partners.length / columns).ceil(),
                      separatorBuilder: (_, _) => const SizedBox(height: 16),
                      itemBuilder: (context, row) {
                        final first = row * columns;
                        if (columns == 1) {
                          return _SchoolCard(
                            school: partners[first],
                            store: store,
                          );
                        }
                        return Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              child: _SchoolCard(
                                school: partners[first],
                                store: store,
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: first + 1 < partners.length
                                  ? _SchoolCard(
                                      school: partners[first + 1],
                                      store: store,
                                    )
                                  : const SizedBox(),
                            ),
                          ],
                        );
                      },
                    );
                  },
                ),
              )
            else
              const SliverToBoxAdapter(child: SizedBox(height: 128)),
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
      padding: EdgeInsets.zero,
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => SchoolDetailScreen(school: school)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Stack(
            children: [
              SizedBox(
                height: 144,
                width: double.infinity,
                child: SchoolPhoto(school: school),
              ),
              Positioned(
                right: 12,
                top: 12,
                child: Material(
                  color: ExchangeColors.surface,
                  shape: const CircleBorder(),
                  child: IconButton(
                    tooltip: saved ? '取消收藏' : '加入收藏',
                    onPressed: () => store.toggleFavorite(school.schoolName),
                    icon: Icon(
                      saved
                          ? Icons.bookmark_rounded
                          : Icons.bookmark_outline_rounded,
                      color: saved
                          ? ExchangeColors.teal
                          : ExchangeColors.secondaryInk,
                    ),
                  ),
                ),
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                StudentIconLabel(
                  Icons.place_outlined,
                  school.country,
                  color: ExchangeColors.teal,
                ),
                const SizedBox(height: 8),
                Text(
                  school.schoolName,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: school.displayStudyPeriod.isEmpty
                          ? const StudentIconLabel(
                              Icons.school_outlined,
                              '查看交換條件',
                            )
                          : StudentIconLabel(
                              Icons.schedule_rounded,
                              school.displayStudyPeriod,
                            ),
                    ),
                    const Icon(
                      Icons.arrow_forward_rounded,
                      size: 20,
                      color: ExchangeColors.teal,
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
  Widget build(BuildContext context) => TextField(
    controller: controller,
    onChanged: onChanged,
    textInputAction: TextInputAction.search,
    decoration: InputDecoration(
      labelText: '搜尋學校',
      hintText: '校名、國家或交換條件',
      prefixIcon: const Icon(Icons.search_rounded),
      suffixIcon: onClear == null
          ? null
          : IconButton(
              tooltip: '清除搜尋',
              onPressed: onClear,
              icon: const Icon(Icons.close_rounded),
            ),
    ),
  );
}
