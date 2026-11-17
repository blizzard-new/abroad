import 'package:flutter/material.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/school_visuals.dart';
import '../core/student_plan.dart';
import '../core/student_ui.dart';
import '../core/uniway_brand.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import 'feature_screens.dart';
import 'school_detail_screen.dart';

Future<void> selectSchoolAsApplicationTarget(
  BuildContext context,
  ExchangeStore store,
  PartnerUniversity school, {
  bool popCurrentRoute = false,
}) async {
  final messenger = ScaffoldMessenger.maybeOf(context);
  final navigator = Navigator.maybeOf(context);
  final previousContext = await store.selectTargetSchoolForApplication(school);
  if (popCurrentRoute && navigator != null && navigator.canPop()) {
    navigator.pop();
  }
  messenger
    ?..hideCurrentSnackBar()
    ..showSnackBar(
      SnackBar(
        content: Text('已將「${school.schoolName}」設為申請目標校'),
        action: SnackBarAction(
          label: '復原',
          onPressed: () {
            store.updateApplicationContext(previousContext);
            store.selectMainTab(1);
          },
        ),
      ),
    );
}

Future<void> showSchoolCompareSheet(
  BuildContext context,
  ExchangeStore store,
) async {
  await showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    backgroundColor: ExchangeColors.surface,
    builder: (sheetContext) => AnimatedBuilder(
      animation: store,
      builder: (modalContext, _) {
        final schools = store.comparedPartnerSchools;
        if (schools.isEmpty) {
          return SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '尚未選擇比較學校',
                    style: Theme.of(modalContext).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '請在學校卡片點選「加入比較」，最多可並排對照 4 間合作校。',
                    style: Theme.of(modalContext).textTheme.bodySmall,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: () => Navigator.of(sheetContext).pop(),
                    child: const Text('返回找學校'),
                  ),
                ],
              ),
            ),
          );
        }

        return SafeArea(
          top: false,
          child: FractionallySizedBox(
            heightFactor: 0.88,
            child: Column(
              key: const ValueKey('school-compare-sheet'),
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 4, 16, 12),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '合作校並排比較（${schools.length}/4 間）',
                              style: Theme.of(modalContext).textTheme.titleLarge
                                  ?.copyWith(
                                    fontFeatures: ExchangeColors.tabularFigures,
                                  ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              schools.length < 2
                                  ? '可回列表再加入 1 至 3 間學校並排對照'
                                  : '左右滑動比較開放狀態、名額、期限與門檻',
                              style: Theme.of(modalContext).textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ),
                      TextButton(
                        onPressed: () {
                          store.clearCompareSchools();
                          Navigator.of(sheetContext).pop();
                        },
                        child: const Text('清空'),
                      ),
                    ],
                  ),
                ),
                const MetroLineBar(),
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: IntrinsicHeight(
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            for (var i = 0; i < schools.length; i++) ...[
                              if (i > 0) const SizedBox(width: 12),
                              SizedBox(
                                width: 224,
                                child: _CompareSchoolColumn(
                                  school: schools[i],
                                  store: store,
                                  onSelectTarget: () async {
                                    Navigator.of(sheetContext).pop();
                                    await selectSchoolAsApplicationTarget(
                                      context,
                                      store,
                                      schools[i],
                                    );
                                  },
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    ),
  );
}

class _CompareSchoolColumn extends StatelessWidget {
  const _CompareSchoolColumn({
    required this.school,
    required this.store,
    required this.onSelectTarget,
  });

  final PartnerUniversity school;
  final ExchangeStore store;
  final VoidCallback onSelectTarget;

  @override
  Widget build(BuildContext context) {
    final assessment = assessSchoolCondition(
      school,
      store.planProfile,
      academicScoreMinimum: store.activeUniversity.academicScoreMinimum,
    );
    final isTarget = store.applicationContext.targetSchool == school.schoolName;
    final languageSummary = school.languageRequirement.trim().isNotEmpty
        ? school.languageRequirement.trim()
        : (school.eligibilityPoints.isNotEmpty
              ? school.eligibilityPoints.first
              : '依校方簡章');
    final tuitionSummary = school.tuitionPoints.isNotEmpty
        ? school.tuitionPoints.first
        : '依合作協議與簡章';

    return GlassCard(
      borderColor: isTarget ? ExchangeColors.actionBlue : ExchangeColors.line,
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      school.country,
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: ExchangeColors.actionBlue,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      school.schoolName,
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ],
                ),
              ),
              IconButton(
                tooltip: '移出比較',
                onPressed: () => store.toggleCompareSchool(school.schoolName),
                constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
                padding: EdgeInsets.zero,
                icon: const Icon(Icons.close_rounded, size: 18),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Align(
            alignment: Alignment.centerLeft,
            child: _AvailabilityBadge(school: school),
          ),
          const SizedBox(height: 12),
          const Divider(height: 1),
          _CompareCell(label: '交換名額', value: school.displayQuota, tabular: true),
          _CompareCell(
            label: '申請期限',
            value: school.displayDeadlineSummary,
            tabular: true,
          ),
          _CompareCell(label: '學制與學院', value: _scopeSummary(school)),
          _CompareCell(label: '語言與資格', value: languageSummary),
          _CompareCell(label: '費用重點', value: tuitionSummary),
          if (assessment != null)
            _CompareCell(
              label: '我的條件初判',
              value: '${assessment.label}（${assessment.detail}）',
            )
          else if (!school.isOpenThisCycle &&
              school.availabilityNote.isNotEmpty)
            _CompareCell(label: '狀態說明', value: school.availabilityNote),
          const Spacer(),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: onSelectTarget,
            icon: Icon(
              isTarget ? Icons.check_rounded : Icons.flag_outlined,
              size: 18,
            ),
            label: Text(isTarget ? '目前目標校' : '設為目標校'),
          ),
        ],
      ),
    );
  }

  String _scopeSummary(PartnerUniversity school) {
    final parts = <String>[
      if (school.degreeLevels.trim().isNotEmpty) school.degreeLevels.trim(),
      if (school.colleges.trim().isNotEmpty) school.colleges.trim(),
    ];
    return parts.isEmpty ? '不限學院與學制' : parts.join(' · ');
  }
}

class _CompareCell extends StatelessWidget {
  const _CompareCell({
    required this.label,
    required this.value,
    this.tabular = false,
  });

  final String label;
  final String value;
  final bool tabular;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: ExchangeColors.line)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.labelSmall),
          const SizedBox(height: 3),
          Text(
            value,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: ExchangeColors.ink,
              fontWeight: FontWeight.w600,
              fontFeatures: tabular ? ExchangeColors.tabularFigures : null,
            ),
          ),
        ],
      ),
    );
  }
}

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
  String degreeFilter = '';
  bool openOnly = false;
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

  bool _matchesDegree(PartnerUniversity school, String selectedDegree) {
    if (selectedDegree.isEmpty) return true;
    final limit = school.degreeLevels.trim();
    if (limit.isEmpty || limit.contains('不限')) return true;
    if (selectedDegree == '大學部') {
      return limit.contains('大學') || limit.contains('學士');
    }
    if (selectedDegree == '研究所') {
      return limit.contains('研究') || limit.contains('碩') || limit.contains('博');
    }
    return true;
  }

  bool _matchesSchool(
    ExchangeStore store,
    PartnerUniversity school, {
    required String query,
    required String selectedCountry,
    required String selectedDegree,
    required bool onlyOpen,
    required bool onlySaved,
  }) {
    return (query.isEmpty || school.searchableText.contains(query)) &&
        (selectedCountry.isEmpty || school.country == selectedCountry) &&
        (!onlyOpen || school.isOpenThisCycle) &&
        _matchesDegree(school, selectedDegree) &&
        (!onlySaved || store.favorites.contains(school.schoolName));
  }

  Future<void> _showFilters(
    ExchangeStore store,
    List<PartnerUniversity> schools,
    List<String> countries,
  ) async {
    var selectedCountry = country;
    var selectedDegree = degreeFilter;
    var onlyOpen = openOnly;
    var onlySaved = savedOnly;
    final result = await showModalBottomSheet<
      ({String country, String degree, bool openOnly, bool savedOnly})
    >(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      backgroundColor: ExchangeColors.surface,
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setSheetState) {
          final query = searchController.text.trim().toLowerCase();
          final matchCount = schools
              .where(
                (school) => _matchesSchool(
                  store,
                  school,
                  query: query,
                  selectedCountry: selectedCountry,
                  selectedDegree: selectedDegree,
                  onlyOpen: onlyOpen,
                  onlySaved: onlySaved,
                ),
              )
              .length;
          return SafeArea(
            top: false,
            child: FractionallySizedBox(
              heightFactor: 0.84,
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
                      '依國家、開放狀態與學制篩選合作校。',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    const SizedBox(height: 16),
                    Expanded(
                      child: SingleChildScrollView(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '開放狀態',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 10),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: [
                                ChoiceChip(
                                  label: const Text('全部狀態'),
                                  selected: !onlyOpen,
                                  onSelected: (_) =>
                                      setSheetState(() => onlyOpen = false),
                                ),
                                ChoiceChip(
                                  label: const Text('僅看本期開放'),
                                  selected: onlyOpen,
                                  onSelected: (_) =>
                                      setSheetState(() => onlyOpen = true),
                                ),
                              ],
                            ),
                            const SizedBox(height: 18),
                            Text(
                              '適用學制',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 10),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: [
                                ChoiceChip(
                                  label: const Text('全部學制'),
                                  selected: selectedDegree.isEmpty,
                                  onSelected: (_) =>
                                      setSheetState(() => selectedDegree = ''),
                                ),
                                for (final item in const ['大學部', '研究所'])
                                  ChoiceChip(
                                    label: Text(item),
                                    selected: selectedDegree == item,
                                    onSelected: (_) => setSheetState(
                                      () => selectedDegree = item,
                                    ),
                                  ),
                              ],
                            ),
                            const SizedBox(height: 18),
                            Text(
                              '國家或地區',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 10),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: [
                                ChoiceChip(
                                  label: const Text('全部國家'),
                                  selected: selectedCountry.isEmpty,
                                  onSelected: (_) =>
                                      setSheetState(() => selectedCountry = ''),
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
                            const SizedBox(height: 18),
                            const Divider(),
                            SwitchListTile(
                              contentPadding: EdgeInsets.zero,
                              title: const Text('只看收藏的學校'),
                              subtitle: Text(
                                '已收藏 ${store.favorites.length} 間',
                                style: Theme.of(context).textTheme.bodySmall
                                    ?.copyWith(
                                      fontFeatures:
                                          ExchangeColors.tabularFigures,
                                    ),
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
                            selectedDegree = '';
                            onlyOpen = false;
                            onlySaved = false;
                          }),
                          child: const Text('重設'),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: FilledButton(
                            onPressed: () => Navigator.of(sheetContext).pop((
                              country: selectedCountry,
                              degree: selectedDegree,
                              openOnly: onlyOpen,
                              savedOnly: onlySaved,
                            )),
                            child: Text(
                              '顯示 $matchCount 間學校',
                              style: const TextStyle(
                                fontFeatures: ExchangeColors.tabularFigures,
                              ),
                            ),
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
      degreeFilter = result.degree;
      openOnly = result.openOnly;
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
          (school) => _matchesSchool(
            store,
            school,
            query: query,
            selectedCountry: country,
            selectedDegree: degreeFilter,
            onlyOpen: openOnly,
            onlySaved: savedOnly,
          ),
        )
        .toList();
    final compared = store.comparedPartnerSchools;

    return SafeArea(
      bottom: false,
      child: Column(
        children: [
          Expanded(
            child: RefreshIndicator(
              onRefresh: store.refresh,
              child: CustomScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                slivers: [
                  SliverPadding(
                    padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
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
                                title: '高效率選校流程',
                                steps: const [
                                  (
                                    icon: Icons.tune_rounded,
                                    title: '先設選校條件',
                                    detail:
                                        '填寫學院、學制、平均成績與語檢，卡片會標示資格相符度。',
                                  ),
                                  (
                                    icon: Icons.compare_arrows_rounded,
                                    title: '加入 2 至 4 校並排比較',
                                    detail: '直接對照開放狀態、名額、截止日與語言門檻。',
                                  ),
                                  (
                                    icon: Icons.flag_outlined,
                                    title: '一鍵設為目標校',
                                    detail: '直接將目標校帶入申請文件頁，免去重複選擇。',
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                        ],
                        _ConditionsBar(store: store),
                        const SizedBox(height: 10),
                        _SchoolSearchField(
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
                        const SizedBox(height: 10),
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
                                        size: 18,
                                      ),
                                      label: Text(
                                        '收藏 ${store.favorites.length}',
                                        style: const TextStyle(
                                          fontFeatures:
                                              ExchangeColors.tabularFigures,
                                        ),
                                      ),
                                      selected: savedOnly,
                                      onSelected: (value) =>
                                          setState(() => savedOnly = value),
                                    ),
                                    const SizedBox(width: 8),
                                    FilterChip(
                                      key: const ValueKey('filter-open-only'),
                                      label: const Text('僅看本期開放'),
                                      selected: openOnly,
                                      onSelected: (value) =>
                                          setState(() => openOnly = value),
                                    ),
                                    const SizedBox(width: 8),
                                    ChoiceChip(
                                      label: const Text('全部國家'),
                                      selected: country.isEmpty,
                                      onSelected: (_) =>
                                          setState(() => country = ''),
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
                        const SizedBox(height: 16),
                        if (store.isLoading && dashboard == null)
                          const LoadingCards(count: 4)
                        else if (store.error != null && dashboard == null)
                          InlineError(
                            message: store.error!,
                            onRetry: store.refresh,
                          )
                        else if (partners.isEmpty)
                          StudentEmptyState(
                            icon: savedOnly
                                ? Icons.bookmark_outline_rounded
                                : Icons.search_off_rounded,
                            title: savedOnly && store.favorites.isEmpty
                                ? '尚未收藏合作校'
                                : '沒有符合條件的學校',
                            detail: savedOnly && store.favorites.isEmpty
                                ? '點選學校卡片右上角書籤，即可加入收藏清單。'
                                : '請調整關鍵字、國家或開放狀態篩選條件。',
                            action: OutlinedButton(
                              onPressed: () {
                                setState(() {
                                  country = '';
                                  degreeFilter = '';
                                  openOnly = false;
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
                            style: Theme.of(context).textTheme.bodySmall
                                ?.copyWith(
                                  fontFeatures: ExchangeColors.tabularFigures,
                                ),
                          ),
                          const SizedBox(height: 10),
                        ],
                      ],
                    ),
                  ),
                  if (partners.isNotEmpty)
                    SliverPadding(
                      padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
                      sliver: SliverLayoutBuilder(
                        builder: (context, constraints) {
                          final columns = constraints.crossAxisExtent >= 720
                              ? 2
                              : 1;
                          return SliverList.separated(
                            itemCount: (partners.length / columns).ceil(),
                            separatorBuilder: (_, _) =>
                                const SizedBox(height: 12),
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
                                  const SizedBox(width: 12),
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
                    const SliverToBoxAdapter(child: SizedBox(height: 24)),
                ],
              ),
            ),
          ),
          if (compared.isNotEmpty) _CompareTrayBar(store: store),
        ],
      ),
    );
  }
}

class _ConditionsBar extends StatelessWidget {
  const _ConditionsBar({required this.store});

  final ExchangeStore store;

  @override
  Widget build(BuildContext context) {
    final profile = store.planProfile;
    return GlassCard(
      key: const ValueKey('school-conditions-bar'),
      tint: ExchangeColors.surfaceMuted,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      onTap: () => Navigator.of(
        context,
      ).push(MaterialPageRoute(builder: (_) => const EligibilityScreen())),
      child: Row(
        children: [
          const Icon(
            Icons.manage_search_rounded,
            size: 20,
            color: ExchangeColors.actionBlue,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '我的選校條件',
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    color: ExchangeColors.actionBlue,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  profile == null ? '設定條件，自動標示適合學校' : profile.summaryLabel,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: ExchangeColors.ink,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Text(
            profile == null ? '設定' : '編輯',
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: ExchangeColors.actionBlue,
            ),
          ),
          const Icon(
            Icons.chevron_right_rounded,
            size: 18,
            color: ExchangeColors.actionBlue,
          ),
        ],
      ),
    );
  }
}

class _CompareTrayBar extends StatelessWidget {
  const _CompareTrayBar({required this.store});

  final ExchangeStore store;

  @override
  Widget build(BuildContext context) {
    final compared = store.comparedPartnerSchools;
    return DecoratedBox(
      key: const ValueKey('school-compare-tray'),
      decoration: const BoxDecoration(
        color: ExchangeColors.surface,
        border: Border(top: BorderSide(color: ExchangeColors.line)),
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
        child: Wrap(
          spacing: 10,
          runSpacing: 8,
          alignment: WrapAlignment.spaceBetween,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.view_column_outlined,
                  size: 20,
                  color: ExchangeColors.actionBlue,
                ),
                const SizedBox(width: 8),
                Flexible(
                  child: Text(
                    '已選 ${compared.length} / 4 間比較',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontFeatures: ExchangeColors.tabularFigures,
                    ),
                  ),
                ),
              ],
            ),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextButton(
                  onPressed: store.clearCompareSchools,
                  child: const Text('清空'),
                ),
                const SizedBox(width: 6),
                FilledButton.icon(
                  key: const ValueKey('open-compare-sheet'),
                  onPressed: () => showSchoolCompareSheet(context, store),
                  icon: const Icon(Icons.compare_arrows_rounded, size: 18),
                  label: const Text('並排比較'),
                ),
              ],
            ),
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
    final inCompare = store.isInCompare(school.schoolName);
    final isTarget = store.applicationContext.targetSchool == school.schoolName;
    final hasVerifiedPhoto =
        school.imageStatus == 'verified' && school.imageUrl.trim().isNotEmpty;
    final assessment = assessSchoolCondition(
      school,
      store.planProfile,
      academicScoreMinimum: store.activeUniversity.academicScoreMinimum,
    );

    return GlassCard(
      borderColor: isTarget ? ExchangeColors.actionBlue : ExchangeColors.line,
      padding: const EdgeInsets.all(16),
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => SchoolDetailScreen(school: school)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    UniWayPill(school.country, icon: Icons.place_outlined),
                    _AvailabilityBadge(school: school),
                    if (isTarget)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: ExchangeColors.tealSoft,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          '申請目標校',
                          style: Theme.of(context).textTheme.labelSmall
                              ?.copyWith(
                                color: ExchangeColors.actionBlue,
                                fontWeight: FontWeight.w700,
                              ),
                        ),
                      ),
                  ],
                ),
              ),
              IconButton(
                tooltip: saved ? '取消收藏' : '加入收藏',
                constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
                onPressed: () => store.toggleFavorite(school.schoolName),
                icon: Icon(
                  saved
                      ? Icons.bookmark_rounded
                      : Icons.bookmark_outline_rounded,
                  color: saved
                      ? ExchangeColors.actionBlue
                      : ExchangeColors.secondaryInk,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            school.schoolName,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          if (hasVerifiedPhoto) ...[
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: SizedBox(
                height: 108,
                width: double.infinity,
                child: SchoolPhoto(school: school),
              ),
            ),
          ],
          const SizedBox(height: 12),
          _SignageFactsStrip(school: school),
          if (!school.isOpenThisCycle &&
              school.availabilityNote.trim().isNotEmpty) ...[
            const SizedBox(height: 10),
            _StatusStrip(
              icon: Icons.info_outline_rounded,
              text: school.availabilityNote.trim(),
              background: ExchangeColors.referenceSoft,
              foreground: ExchangeColors.referenceInk,
            ),
          ] else if (assessment != null) ...[
            const SizedBox(height: 10),
            _ConditionAssessmentStrip(assessment: assessment),
          ],
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              OutlinedButton.icon(
                key: ValueKey('compare-toggle-${school.schoolName}'),
                onPressed: () {
                  final ok = store.toggleCompareSchool(school.schoolName);
                  if (!ok) {
                    ScaffoldMessenger.maybeOf(context)
                      ?..hideCurrentSnackBar()
                      ..showSnackBar(
                        const SnackBar(content: Text('最多同時比較 4 間學校。')),
                      );
                  }
                },
                icon: Icon(
                  inCompare
                      ? Icons.check_box_outlined
                      : Icons.compare_arrows_rounded,
                  size: 18,
                ),
                label: Text(inCompare ? '已加入比較' : '加入比較'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 8,
                  ),
                ),
              ),
              FilledButton.tonalIcon(
                key: ValueKey('set-target-${school.schoolName}'),
                onPressed: () {
                  if (isTarget) {
                    store.selectMainTab(2);
                  } else {
                    selectSchoolAsApplicationTarget(context, store, school);
                  }
                },
                icon: Icon(
                  isTarget
                      ? Icons.assignment_turned_in_outlined
                      : Icons.flag_outlined,
                  size: 18,
                ),
                label: Text(isTarget ? '前往申請文件' : '設為目標'),
                style: FilledButton.styleFrom(
                  backgroundColor: isTarget
                      ? ExchangeColors.actionBlue
                      : ExchangeColors.tealSoft,
                  foregroundColor: isTarget
                      ? ExchangeColors.onPrimary
                      : ExchangeColors.actionBlue,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 8,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _AvailabilityBadge extends StatelessWidget {
  const _AvailabilityBadge({required this.school});

  final PartnerUniversity school;

  @override
  Widget build(BuildContext context) {
    final (bg, fg, border) = switch (school.availabilityStatus) {
      'open' => (
        ExchangeColors.successSoft,
        ExchangeColors.success,
        ExchangeColors.success.withValues(alpha: 0.28),
      ),
      'agreement_only' => (
        ExchangeColors.referenceSoft,
        ExchangeColors.referenceInk,
        ExchangeColors.referenceAccent.withValues(alpha: 0.45),
      ),
      'quota_unconfirmed' || 'visiting_fee_paying' => (
        ExchangeColors.amberSoft,
        ExchangeColors.amber,
        ExchangeColors.amber.withValues(alpha: 0.35),
      ),
      'closed' => (
        ExchangeColors.coralSoft,
        ExchangeColors.danger,
        ExchangeColors.danger.withValues(alpha: 0.35),
      ),
      _ => (
        ExchangeColors.surfaceMuted,
        ExchangeColors.secondaryInk,
        ExchangeColors.line,
      ),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: border),
      ),
      child: Text(
        school.availabilityLabel,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: fg,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _SignageFactsStrip extends StatelessWidget {
  const _SignageFactsStrip({required this.school});

  final PartnerUniversity school;

  @override
  Widget build(BuildContext context) {
    final items = [
      (label: '交換名額', value: school.displayQuota, tabular: true),
      (label: '申請期限', value: school.displayDeadlineSummary, tabular: true),
      (label: '學制 / 條件', value: school.displayScopeAndLanguage, tabular: false),
    ];
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: ExchangeColors.surfaceMuted,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ExchangeColors.line),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final stacked =
              constraints.maxWidth < 280 ||
              MediaQuery.textScalerOf(context).scale(14) >= 24;
          if (stacked) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (var i = 0; i < items.length; i++) ...[
                  if (i > 0) const SizedBox(height: 8),
                  _FactCell(item: items[i]),
                ],
              ],
            );
          }
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (var i = 0; i < items.length; i++) ...[
                if (i > 0)
                  Container(
                    width: 1,
                    height: 36,
                    margin: const EdgeInsets.symmetric(horizontal: 10),
                    color: ExchangeColors.line,
                  ),
                Expanded(child: _FactCell(item: items[i])),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _FactCell extends StatelessWidget {
  const _FactCell({required this.item});

  final ({String label, String value, bool tabular}) item;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(item.label, style: Theme.of(context).textTheme.labelSmall),
        const SizedBox(height: 2),
        Text(
          item.value,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: ExchangeColors.ink,
            fontWeight: FontWeight.w600,
            fontFeatures: item.tabular ? ExchangeColors.tabularFigures : null,
          ),
        ),
      ],
    );
  }
}

class _ConditionAssessmentStrip extends StatelessWidget {
  const _ConditionAssessmentStrip({required this.assessment});

  final SchoolConditionAssessment assessment;

  @override
  Widget build(BuildContext context) {
    final (icon, bg, fg) = switch (assessment.status) {
      SchoolConditionStatus.preliminaryMatch => (
        Icons.check_circle_outline_rounded,
        ExchangeColors.successSoft,
        ExchangeColors.success,
      ),
      SchoolConditionStatus.needsConfirmation => (
        Icons.help_outline_rounded,
        ExchangeColors.amberSoft,
        ExchangeColors.amber,
      ),
      SchoolConditionStatus.mismatch => (
        Icons.warning_amber_rounded,
        ExchangeColors.coralSoft,
        ExchangeColors.danger,
      ),
    };
    return _StatusStrip(
      icon: icon,
      text: '${assessment.label} · ${assessment.detail}',
      background: bg,
      foreground: fg,
    );
  }
}

class _StatusStrip extends StatelessWidget {
  const _StatusStrip({
    required this.icon,
    required this.text,
    required this.background,
    required this.foreground,
  });

  final IconData icon;
  final String text;
  final Color background;
  final Color foreground;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: foreground),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: foreground,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SchoolSearchField extends StatelessWidget {
  const _SchoolSearchField({
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
      floatingLabelBehavior: FloatingLabelBehavior.never,
      hintText: '校名、國家、學院或交換條件',
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
