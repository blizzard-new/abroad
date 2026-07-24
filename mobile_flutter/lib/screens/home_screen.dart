import 'package:flutter/material.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_plan.dart';
import '../state/exchange_store.dart';
import 'account_screen.dart';
import 'ai_tools_screens.dart';
import 'feature_screens.dart';
import 'student_plan_screens.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({
    required this.onSelectTab,
    this.showHeader = true,
    super.key,
  });

  final ValueChanged<int> onSelectTab;
  final bool showHeader;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final searchController = TextEditingController();

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  void _search(ExchangeStore store, [String? preset]) {
    store.setSchoolSearchQuery((preset ?? searchController.text).trim());
    widget.onSelectTab(1);
  }

  void _open(Widget page) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final dashboard = store.dashboard;

    return SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: store.refresh,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 116),
          children: [
            if (widget.showHeader) ...[
              _TopHeader(
                store: store,
                onAccount: () => _open(const AccountScreen()),
              ),
              const SizedBox(height: 16),
            ],
            if (store.isLoading && dashboard == null)
              const _DashboardLoading()
            else if (store.error != null && dashboard == null)
              InlineError(message: store.error!, onRetry: store.refresh)
            else if (dashboard != null) ...[
              _CampusHero(
                schoolCount: dashboard.partnerUniversities.length,
                controller: searchController,
                onSearch: () => _search(store),
              ),
              const SizedBox(height: 14),
              _AdvisorSpotlight(onTap: () => _open(const AdvisorScreen())),
              const SizedBox(height: 14),
              _PersonalPlanCard(
                store: store,
                onOpenEligibility: () => _open(const EligibilityScreen()),
              ),
              const SizedBox(height: 14),
              _FeatureGrid(
                features: [
                  _FeatureDefinition(
                    title: '長庚討論板',
                    detail: '匿名貼文、聊天與私訊',
                    icon: Icons.forum_outlined,
                    color: ExchangeColors.teal,
                    tint: ExchangeColors.tealSoft,
                    onTap: () => widget.onSelectTab(4),
                  ),
                  _FeatureDefinition(
                    title: '找交換學校',
                    detail: '${dashboard.partnerUniversities.length} 間合作校',
                    icon: Icons.school_outlined,
                    color: ExchangeColors.blue,
                    tint: ExchangeColors.blueSoft,
                    onTap: () => _search(store, ''),
                  ),
                  _FeatureDefinition(
                    title: '申請文件',
                    detail:
                        '${store.initialApplicationReadyCount}/${store.initialApplicationTemplates.length} 份已完成',
                    icon: Icons.edit_document,
                    color: ExchangeColors.teal,
                    tint: ExchangeColors.tealSoft,
                    onTap: () => widget.onSelectTab(2),
                  ),
                  _FeatureDefinition(
                    title: '申請日曆',
                    detail: '任務、提醒與日曆同步',
                    icon: Icons.calendar_month_outlined,
                    color: ExchangeColors.coral,
                    tint: ExchangeColors.coralSoft,
                    onTap: () => widget.onSelectTab(3),
                  ),
                  _FeatureDefinition(
                    title: '官方截止日',
                    detail: '${store.deadlines.length} 筆時程來源',
                    icon: Icons.event_available_outlined,
                    color: ExchangeColors.amber,
                    tint: ExchangeColors.amberSoft,
                    onTap: () => _open(const OfficialDeadlinesScreen()),
                  ),
                  _FeatureDefinition(
                    title: '補助資訊',
                    detail: '${dashboard.scholarshipInfo.length} 項補助整理',
                    icon: Icons.savings_outlined,
                    color: ExchangeColors.success,
                    tint: ExchangeColors.tealSoft,
                    onTap: () => _open(const ScholarshipsScreen()),
                  ),
                  _FeatureDefinition(
                    title: '資格初判',
                    detail: '成績、學制與語言比對',
                    icon: Icons.fact_check_outlined,
                    color: ExchangeColors.blue,
                    tint: ExchangeColors.blueSoft,
                    onTap: () => _open(const EligibilityScreen()),
                  ),
                  _FeatureDefinition(
                    title: '文件檢查',
                    detail: '漏填、字數與簽名',
                    icon: Icons.fact_check_outlined,
                    color: ExchangeColors.success,
                    tint: ExchangeColors.tealSoft,
                    onTap: () => _open(const DocumentCheckScreen()),
                  ),
                  _FeatureDefinition(
                    title: '文件改寫',
                    detail: '正式化、翻譯與精簡',
                    icon: Icons.auto_fix_high_rounded,
                    color: ExchangeColors.blue,
                    tint: ExchangeColors.blueSoft,
                    onTap: () => _open(const WritingAssistantScreen()),
                  ),
                  _FeatureDefinition(
                    title: '文件庫',
                    detail:
                        '${store.documentReadyCount}/${applicationDocumentLabels.length} 已完成',
                    icon: Icons.folder_copy_outlined,
                    color: ExchangeColors.coral,
                    tint: ExchangeColors.coralSoft,
                    onTap: () => _open(const DocumentsScreen()),
                  ),
                  _FeatureDefinition(
                    title: '交換預算',
                    detail: store.budgetPlans.isEmpty
                        ? '估算生活費與補助'
                        : '${store.budgetPlans.length} 間已估算',
                    icon: Icons.calculate_outlined,
                    color: ExchangeColors.blue,
                    tint: ExchangeColors.blueSoft,
                    onTap: () => _open(const BudgetScreen()),
                  ),
                  _FeatureDefinition(
                    title: '收藏比較',
                    detail: '${store.favorites.length} 間候選學校',
                    icon: Icons.bookmarks_outlined,
                    color: ExchangeColors.amber,
                    tint: ExchangeColors.amberSoft,
                    onTap: () => _open(const FavoritesScreen()),
                  ),
                  _FeatureDefinition(
                    title: '桌面小工具',
                    detail: '下一個任務隨時查看',
                    icon: Icons.widgets_outlined,
                    color: ExchangeColors.teal,
                    tint: ExchangeColors.tealSoft,
                    onTap: () => _open(const WidgetSettingsScreen()),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _AdvisorSpotlight extends StatelessWidget {
  const _AdvisorSpotlight({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: '開啟申請顧問',
      child: SizedBox(
        height: 154,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Stack(
            fit: StackFit.expand,
            children: [
              Image.asset(
                'assets/images/destination-tokyo.jpg',
                fit: BoxFit.cover,
                alignment: const Alignment(0, -.15),
              ),
              const DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.centerLeft,
                    end: Alignment.centerRight,
                    colors: [
                      Color(0xE5102734),
                      Color(0x8A102734),
                      Color(0x25102734),
                    ],
                  ),
                ),
              ),
              Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: onTap,
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  const Icon(
                                    Icons.auto_awesome_rounded,
                                    color: Colors.white,
                                    size: 18,
                                  ),
                                  const SizedBox(width: 7),
                                  Text(
                                    '依官方資料規劃',
                                    style: Theme.of(context).textTheme.bodySmall
                                        ?.copyWith(
                                          color: Colors.white,
                                          fontWeight: FontWeight.w700,
                                        ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 7),
                              Text(
                                '申請顧問',
                                style: Theme.of(context)
                                    .textTheme
                                    .headlineMedium
                                    ?.copyWith(color: Colors.white),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '選校、條件缺口與下一步',
                                style: Theme.of(context).textTheme.bodyMedium
                                    ?.copyWith(
                                      color: Colors.white.withValues(alpha: .9),
                                    ),
                              ),
                            ],
                          ),
                        ),
                        Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: .78),
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.white),
                          ),
                          child: const Icon(Icons.arrow_forward_rounded),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TopHeader extends StatelessWidget {
  const _TopHeader({required this.store, required this.onAccount});

  final ExchangeStore store;
  final VoidCallback onAccount;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const ExchangeIconBadge(
          Icons.school_outlined,
          color: ExchangeColors.blue,
          background: ExchangeColors.blueSoft,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('目前就讀學校', style: Theme.of(context).textTheme.bodySmall),
              Text(
                store.account?.homeUniversity ?? '長庚大學',
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ],
          ),
        ),
        IconButton.outlined(
          tooltip: '重新整理',
          onPressed: store.isLoading ? null : store.refresh,
          constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
          icon: store.isLoading
              ? const SizedBox.square(
                  dimension: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.refresh_rounded),
        ),
        const SizedBox(width: 8),
        IconButton.outlined(
          tooltip: store.account == null ? '登入' : '我的帳號',
          onPressed: onAccount,
          constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
          icon: Icon(
            store.account == null
                ? Icons.person_outline_rounded
                : Icons.person_rounded,
          ),
        ),
      ],
    );
  }
}

class _CampusHero extends StatelessWidget {
  const _CampusHero({
    required this.schoolCount,
    required this.controller,
    required this.onSearch,
  });

  final int schoolCount;
  final TextEditingController controller;
  final VoidCallback onSearch;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 248,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: Stack(
          fit: StackFit.expand,
          children: [
            Image.asset(
              'assets/images/cgu-campus.jpg',
              fit: BoxFit.cover,
              alignment: const Alignment(.25, 0),
            ),
            const DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Color(0x00101824), Color(0xA80A1D2B)],
                  stops: [.38, 1],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: .9),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: .96),
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF10212E).withValues(alpha: .2),
                          blurRadius: 24,
                          offset: const Offset(0, 10),
                        ),
                      ],
                    ),
                    child: TextField(
                      controller: controller,
                      onSubmitted: (_) => onSearch(),
                      textInputAction: TextInputAction.search,
                      decoration: InputDecoration(
                        hintText: '搜尋 $schoolCount 間合作校',
                        prefixIcon: const Icon(Icons.search_rounded),
                        suffixIcon: IconButton(
                          tooltip: '搜尋',
                          onPressed: onSearch,
                          constraints: const BoxConstraints(
                            minWidth: 48,
                            minHeight: 48,
                          ),
                          icon: const Icon(Icons.arrow_forward_rounded),
                        ),
                        fillColor: Colors.transparent,
                        contentPadding: const EdgeInsets.symmetric(
                          vertical: 17,
                        ),
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FeatureGrid extends StatelessWidget {
  const _FeatureGrid({required this.features});

  final List<_FeatureDefinition> features;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 720 ? 4 : 2;
        const gap = 10.0;
        final width = (constraints.maxWidth - gap * (columns - 1)) / columns;
        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: features
              .map(
                (feature) => SizedBox(
                  width: width,
                  child: _FeatureTile(feature: feature),
                ),
              )
              .toList(),
        );
      },
    );
  }
}

class _PersonalPlanCard extends StatelessWidget {
  const _PersonalPlanCard({
    required this.store,
    required this.onOpenEligibility,
  });

  final ExchangeStore store;
  final VoidCallback onOpenEligibility;

  @override
  Widget build(BuildContext context) {
    final progress = store.planCompletionPercent;
    final topMatch = store.rankedSchoolMatches.firstOrNull;
    final profile = store.planProfile;
    return GlassCard(
      onTap: onOpenEligibility,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              SizedBox.square(
                dimension: 54,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    CircularProgressIndicator(
                      value: progress / 100,
                      strokeWidth: 6,
                      backgroundColor: ExchangeColors.tealSoft,
                      strokeCap: StrokeCap.round,
                    ),
                    Text(
                      '$progress%',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: ExchangeColors.teal,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '我的交換計畫',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      profile?.goalLabel.isNotEmpty == true
                          ? profile!.goalLabel
                          : '先設定交換目標與資格',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded),
            ],
          ),
          const SizedBox(height: 16),
          Container(height: 1, color: ExchangeColors.line),
          const SizedBox(height: 14),
          Text('下一步', style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 3),
          Text(
            store.nextPlanAction,
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
          ),
          if (topMatch != null) ...[
            const SizedBox(height: 8),
            Text(
              '目前首選：${topMatch.school.schoolName} · ${topMatch.score} 分',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: ExchangeColors.teal,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _FeatureTile extends StatelessWidget {
  const _FeatureTile({required this.feature});

  final _FeatureDefinition feature;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      tint: feature.tint,
      padding: const EdgeInsets.all(14),
      onTap: feature.onTap,
      child: ConstrainedBox(
        constraints: const BoxConstraints(minHeight: 116),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ExchangeIconBadge(
              feature.icon,
              color: feature.color,
              background: Colors.white54,
            ),
            const SizedBox(height: 20),
            Text(
              feature.title,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 3),
            Text(
              feature.detail,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class _FeatureDefinition {
  const _FeatureDefinition({
    required this.title,
    required this.detail,
    required this.icon,
    required this.color,
    required this.tint,
    required this.onTap,
  });

  final String title;
  final String detail;
  final IconData icon;
  final Color color;
  final Color tint;
  final VoidCallback onTap;
}

class _DashboardLoading extends StatelessWidget {
  const _DashboardLoading();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        SizedBox(
          height: 160,
          child: Center(child: CircularProgressIndicator()),
        ),
        LoadingCards(count: 4),
      ],
    );
  }
}
