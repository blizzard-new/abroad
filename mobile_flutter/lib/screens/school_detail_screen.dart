import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/school_visuals.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import 'community_screen.dart';

enum _DetailSection { overview, workflow, life, stories, community }

class SchoolDetailScreen extends StatefulWidget {
  const SchoolDetailScreen({required this.school, super.key});

  final PartnerUniversity school;

  @override
  State<SchoolDetailScreen> createState() => _SchoolDetailScreenState();
}

class _SchoolDetailScreenState extends State<SchoolDetailScreen> {
  _DetailSection section = _DetailSection.overview;
  Future<ApplicationWorkflow>? workflowFuture;
  Future<ExperienceDigest>? experiencesFuture;
  bool loaded = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (loaded) return;
    loaded = true;
    final api = ExchangeStoreScope.of(context).api;
    workflowFuture = api.workflow(widget.school.schoolName);
    experiencesFuture = api.experiences(widget.school.schoolName);
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final favorite = store.favorites.contains(widget.school.schoolName);
    return ExchangePageBackground(
      child: Scaffold(
        body: CustomScrollView(
          slivers: [
            SliverAppBar(
              expandedHeight: 430,
              pinned: true,
              stretch: true,
              surfaceTintColor: Colors.transparent,
              backgroundColor: ExchangeColors.background.withValues(alpha: .9),
              scrolledUnderElevation: 0,
              leadingWidth: 64,
              leading: IconButton(
                tooltip: '返回',
                onPressed: () => Navigator.of(context).pop(),
                icon: const Icon(Icons.arrow_back_ios_new_rounded),
              ),
              actions: [
                IconButton(
                  tooltip: favorite ? '取消收藏' : '加入收藏',
                  onPressed: () =>
                      store.toggleFavorite(widget.school.schoolName),
                  icon: Icon(
                    favorite
                        ? Icons.bookmark_rounded
                        : Icons.bookmark_outline_rounded,
                    color: favorite ? ExchangeColors.teal : ExchangeColors.ink,
                  ),
                ),
                const SizedBox(width: 8),
              ],
              flexibleSpace: LayoutBuilder(
                builder: (context, constraints) {
                  final topPadding = MediaQuery.paddingOf(context).top;
                  final collapsedHeight = kToolbarHeight + topPadding;
                  final progress =
                      ((constraints.maxHeight - collapsedHeight) /
                              (430 - collapsedHeight))
                          .clamp(0.0, 1.0);
                  return Stack(
                    fit: StackFit.expand,
                    children: [
                      SchoolPhoto(school: widget.school),
                      const DecoratedBox(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [Color(0x1A07131C), Color(0xC9081722)],
                            stops: [.3, 1],
                          ),
                        ),
                      ),
                      Positioned(
                        left: 18,
                        right: 18,
                        bottom: 22,
                        child: IgnorePointer(
                          ignoring: progress < .35,
                          child: Opacity(
                            opacity: progress,
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(8),
                              child: BackdropFilter(
                                filter: ImageFilter.blur(
                                  sigmaX: 24,
                                  sigmaY: 24,
                                ),
                                child: Container(
                                  padding: const EdgeInsets.all(18),
                                  decoration: BoxDecoration(
                                    color: const Color(
                                      0xD9F8FAFB,
                                    ).withValues(alpha: .82),
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(
                                      color: Colors.white.withValues(alpha: .9),
                                    ),
                                  ),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        '${widget.school.country} · ${widget.school.programType}',
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: Theme.of(context)
                                            .textTheme
                                            .bodySmall
                                            ?.copyWith(
                                              color: ExchangeColors.teal,
                                              fontWeight: FontWeight.w800,
                                            ),
                                      ),
                                      const SizedBox(height: 6),
                                      Text(
                                        widget.school.schoolName,
                                        maxLines: 3,
                                        overflow: TextOverflow.ellipsis,
                                        style: Theme.of(context)
                                            .textTheme
                                            .displaySmall
                                            ?.copyWith(
                                              fontSize: 30,
                                              height: 1.08,
                                              fontWeight: FontWeight.w800,
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
                    ],
                  );
                },
              ),
            ),
            SliverPersistentHeader(
              pinned: true,
              delegate: _SectionSelectorDelegate(
                selected: section,
                onSelected: (value) => setState(() => section = value),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 44),
              sliver: SliverToBoxAdapter(child: _selectedContent(store)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _selectedContent(ExchangeStore store) {
    return switch (section) {
      _DetailSection.overview => _OverviewSection(
        school: widget.school,
        dashboard: store.dashboard,
      ),
      _DetailSection.workflow => FutureBuilder<ApplicationWorkflow>(
        future: workflowFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const LoadingCards(count: 4);
          }
          if (snapshot.hasError) {
            return InlineError(
              message: snapshot.error.toString(),
              onRetry: () => setState(
                () => workflowFuture = store.api.workflow(
                  widget.school.schoolName,
                ),
              ),
            );
          }
          return _WorkflowSection(workflow: snapshot.data!);
        },
      ),
      _DetailSection.life => FutureBuilder<ExperienceDigest>(
        future: experiencesFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const LoadingCards(count: 4);
          }
          if (snapshot.hasError) {
            return InlineError(
              message: snapshot.error.toString(),
              onRetry: () => setState(
                () => experiencesFuture = store.api.experiences(
                  widget.school.schoolName,
                ),
              ),
            );
          }
          return _LifeSection(digest: snapshot.data!);
        },
      ),
      _DetailSection.stories => FutureBuilder<ExperienceDigest>(
        future: experiencesFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const LoadingCards(count: 4);
          }
          if (snapshot.hasError) {
            return InlineError(
              message: snapshot.error.toString(),
              onRetry: () => setState(
                () => experiencesFuture = store.api.experiences(
                  widget.school.schoolName,
                ),
              ),
            );
          }
          return _StoriesSection(digest: snapshot.data!);
        },
      ),
      _DetailSection.community => CommunityScreen(
        embedded: true,
        initialSchool: widget.school.schoolName,
      ),
    };
  }
}

class _SectionSelectorDelegate extends SliverPersistentHeaderDelegate {
  _SectionSelectorDelegate({required this.selected, required this.onSelected});

  final _DetailSection selected;
  final ValueChanged<_DetailSection> onSelected;

  @override
  double get minExtent => 64;

  @override
  double get maxExtent => 64;

  @override
  Widget build(
    BuildContext context,
    double shrinkOffset,
    bool overlapsContent,
  ) {
    const labels = {
      _DetailSection.overview: '重點',
      _DetailSection.workflow: '流程',
      _DetailSection.life: '生活',
      _DetailSection.stories: '心得',
      _DetailSection.community: '社群',
    };
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 22, sigmaY: 22),
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: ExchangeColors.background.withValues(alpha: .78),
            border: const Border(
              bottom: BorderSide(color: ExchangeColors.line),
            ),
          ),
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            children: labels.entries
                .map(
                  (entry) => Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(entry.value),
                      selected: entry.key == selected,
                      onSelected: (_) => onSelected(entry.key),
                    ),
                  ),
                )
                .toList(),
          ),
        ),
      ),
    );
  }

  @override
  bool shouldRebuild(covariant _SectionSelectorDelegate oldDelegate) =>
      oldDelegate.selected != selected;
}

class _OverviewSection extends StatelessWidget {
  const _OverviewSection({required this.school, required this.dashboard});

  final PartnerUniversity school;
  final StudentDashboard? dashboard;

  @override
  Widget build(BuildContext context) {
    final details = <({IconData icon, String label, String value})>[
      if (school.displayApplicationDeadline.isNotEmpty)
        (
          icon: Icons.event_rounded,
          label: '合作校截止',
          value: school.displayApplicationDeadline,
        ),
      if (school.displayStudyPeriod.isNotEmpty)
        (
          icon: Icons.schedule_rounded,
          label: '研修期間',
          value: school.displayStudyPeriod,
        ),
      if (school.quota.isNotEmpty)
        (
          icon: Icons.people_outline_rounded,
          label: '交換名額',
          value: school.quota,
        ),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const ExchangeSectionHeader(title: '申請重點'),
        const SizedBox(height: 14),
        ...details.map(
          (detail) => Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: GlassCard(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ExchangeIconBadge(detail.icon),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          detail.label,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          detail.value,
                          style: Theme.of(context).textTheme.bodyMedium
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        if (school.eligibilityPoints.isNotEmpty) ...[
          const SizedBox(height: 8),
          _StudentPointCard(
            icon: Icons.fact_check_outlined,
            title: '資格與語言重點',
            points: school.eligibilityPoints,
            translated: school.studentSummaryZh.translatedFromEnglish,
          ),
        ],
        if (school.applicationSteps.isNotEmpty) ...[
          const SizedBox(height: 12),
          _StudentPointCard(
            icon: Icons.route_outlined,
            title: '合作校申請步驟',
            points: school.applicationSteps,
            translated: school.studentSummaryZh.translatedFromEnglish,
          ),
        ],
        if (school.tuitionPoints.isNotEmpty) ...[
          const SizedBox(height: 12),
          _StudentPointCard(
            icon: Icons.payments_outlined,
            title: '學費與費用提醒',
            points: school.tuitionPoints,
            translated: school.studentSummaryZh.translatedFromEnglish,
          ),
        ],
        if (dashboard?.ruleExplanations.isNotEmpty == true) ...[
          const SizedBox(height: 26),
          const ExchangeSectionHeader(title: '長庚規定與補助要點'),
          const SizedBox(height: 12),
          ...dashboard!.ruleExplanations
              .take(5)
              .map(
                (rule) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _RuleCard(rule: rule),
                ),
              ),
        ],
        const SizedBox(height: 10),
        _SourceButtons(school: school),
      ],
    );
  }
}

class _StudentPointCard extends StatelessWidget {
  const _StudentPointCard({
    required this.icon,
    required this.title,
    required this.points,
    required this.translated,
  });

  final IconData icon;
  final String title;
  final List<String> points;
  final bool translated;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              ExchangeIconBadge(icon),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
              if (translated)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 9,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: ExchangeColors.tealSoft.withValues(alpha: .72),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    '中文整理',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: ExchangeColors.teal,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 14),
          ...points.map((point) => BulletPoint(point, strong: true)),
        ],
      ),
    );
  }
}

class _RuleCard extends StatelessWidget {
  const _RuleCard({required this.rule});

  final RuleExplanation rule;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(top: 8),
        shape: const Border(),
        collapsedShape: const Border(),
        leading: ExchangeIconBadge(
          rule.fullTextExtracted
              ? Icons.verified_outlined
              : Icons.description_outlined,
        ),
        title: Text(rule.title, style: Theme.of(context).textTheme.titleMedium),
        children: [
          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              rule.summary,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          const SizedBox(height: 12),
          ...rule.keyPoints.map((point) => BulletPoint(point, strong: true)),
          if (rule.documentUrl.isNotEmpty || rule.source.sourceUrl.isNotEmpty)
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                onPressed: () => _openUrl(
                  rule.documentUrl.isNotEmpty
                      ? rule.documentUrl
                      : rule.source.sourceUrl,
                ),
                icon: const Icon(Icons.open_in_new_rounded),
                label: const Text('查看完整官方文件'),
              ),
            ),
        ],
      ),
    );
  }
}

class _WorkflowSection extends StatelessWidget {
  const _WorkflowSection({required this.workflow});

  final ApplicationWorkflow workflow;

  @override
  Widget build(BuildContext context) {
    if (workflow.steps.isEmpty) {
      return EmptyState(
        icon: Icons.route_outlined,
        title: '流程資料仍在整理',
        message: workflow.coverageNote.isEmpty
            ? '請先以長庚國際處與合作校公告為準。'
            : workflow.coverageNote,
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const ExchangeSectionHeader(title: '詳細申請流程'),
        const SizedBox(height: 8),
        Text(
          '校內甄選與合作校申請是兩個階段，請依順序完成。',
          style: Theme.of(
            context,
          ).textTheme.bodyLarge?.copyWith(color: ExchangeColors.secondaryInk),
        ),
        const SizedBox(height: 18),
        ...workflow.steps.map(
          (step) =>
              _TimelineStep(step: step, isLast: step == workflow.steps.last),
        ),
        if (workflow.disclaimer.isNotEmpty) ...[
          const SizedBox(height: 10),
          GlassCard(
            tint: ExchangeColors.amberSoft.withValues(alpha: .76),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(
                  Icons.info_outline_rounded,
                  color: ExchangeColors.amber,
                ),
                const SizedBox(width: 12),
                Expanded(child: Text(workflow.disclaimer)),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _TimelineStep extends StatelessWidget {
  const _TimelineStep({required this.step, required this.isLast});

  final ApplicationStep step;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
            width: 44,
            child: Column(
              children: [
                Container(
                  width: 34,
                  height: 34,
                  alignment: Alignment.center,
                  decoration: const BoxDecoration(
                    color: ExchangeColors.teal,
                    shape: BoxShape.circle,
                  ),
                  child: Text(
                    '${step.order}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                if (!isLast)
                  Expanded(
                    child: Container(width: 2, color: ExchangeColors.tealSoft),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: GlassCard(
                child: ExpansionTile(
                  tilePadding: EdgeInsets.zero,
                  childrenPadding: const EdgeInsets.only(top: 10),
                  shape: const Border(),
                  collapsedShape: const Border(),
                  title: Text(
                    step.title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  subtitle: Text(
                    [
                      step.phase,
                      step.timing,
                    ].where((item) => item.isNotEmpty).join(' · '),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  children: [
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Text(step.summary),
                    ),
                    if (step.responsibleParty.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          '負責單位：${step.responsibleParty}',
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                      ),
                    ],
                    const SizedBox(height: 10),
                    ...step.details.map((detail) => BulletPoint(detail)),
                    ...step.requiredDocuments.map(
                      (document) => BulletPoint('文件：$document', strong: true),
                    ),
                    if (step.actionUrl.isNotEmpty)
                      Align(
                        alignment: Alignment.centerLeft,
                        child: TextButton.icon(
                          onPressed: () => _openUrl(step.actionUrl),
                          icon: const Icon(Icons.open_in_new_rounded),
                          label: const Text('前往辦理'),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _LifeSection extends StatelessWidget {
  const _LifeSection({required this.digest});

  final ExperienceDigest digest;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const ExchangeSectionHeader(title: '生活情報'),
        const SizedBox(height: 18),
        if (digest.highlights.isEmpty)
          const EmptyState(
            icon: Icons.public_rounded,
            title: '尚未找到足夠生活資料',
            message: '不使用一般學校介紹代替學生的實際生活經驗。',
          )
        else
          ...digest.highlights.map(
            (highlight) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _LifeCard(highlight: highlight),
            ),
          ),
      ],
    );
  }
}

class _LifeCard extends StatelessWidget {
  const _LifeCard({required this.highlight});

  final ExperienceHighlight highlight;

  @override
  Widget build(BuildContext context) {
    final verified = highlight.hasConcreteSummary;
    return GlassCard(
      tint: verified ? const Color(0xE9F7FCF9) : null,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              ExchangeIconBadge(
                verified
                    ? Icons.verified_outlined
                    : Icons.pending_actions_outlined,
                color: verified ? ExchangeColors.success : ExchangeColors.amber,
                background: verified
                    ? ExchangeColors.tealSoft
                    : ExchangeColors.amberSoft,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      highlight.title,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    Text(
                      '${highlight.sourceCount} 個來源${verified ? '已整理' : '待補充'}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          if (highlight.keyPoints.isNotEmpty)
            ...highlight.keyPoints.map(
              (point) => BulletPoint(point, strong: true),
            )
          else ...[
            Text(
              highlight.sourceCount > 0
                  ? '已有相關來源，但具體內容尚待整理，暫不自行推測。'
                  : '尚未找到足夠公開學生來源。',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: ExchangeColors.secondaryInk,
              ),
            ),
          ],
          if (highlight.sourceUrls.isNotEmpty) ...[
            const Divider(height: 24),
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              shape: const Border(),
              collapsedShape: const Border(),
              title: const Text('查看完整整理與來源'),
              children: highlight.sourceUrls
                  .map(
                    (url) => ListTile(
                      contentPadding: EdgeInsets.zero,
                      minTileHeight: 48,
                      leading: const Icon(Icons.link_rounded),
                      title: Text(Uri.tryParse(url)?.host ?? '外部來源'),
                      trailing: const Icon(Icons.open_in_new_rounded, size: 18),
                      onTap: () => _openUrl(url),
                    ),
                  )
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }
}

class _StoriesSection extends StatelessWidget {
  const _StoriesSection({required this.digest});

  final ExperienceDigest digest;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const ExchangeSectionHeader(title: '學生心得'),
        const SizedBox(height: 8),
        Text(
          '共 ${digest.totalSources} 個來源：${digest.articleCount} 篇文章、${digest.videoCount} 支影片、${digest.communityCount} 則社群內容。',
          style: Theme.of(
            context,
          ).textTheme.bodyLarge?.copyWith(color: ExchangeColors.secondaryInk),
        ),
        const SizedBox(height: 18),
        if (digest.sources.isEmpty)
          const EmptyState(
            icon: Icons.auto_stories_outlined,
            title: '尚未找到可驗證的學生心得',
            message: '系統不會用一般校方介紹冒充學生經驗。',
          )
        else
          ...digest.sources.map(
            (source) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: GlassCard(
                onTap: source.sourceUrl.isEmpty
                    ? null
                    : () => _openUrl(source.sourceUrl),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ExchangeIconBadge(
                      source.sourceType == 'video'
                          ? Icons.play_circle_outline_rounded
                          : Icons.article_outlined,
                      color: source.sourceType == 'video'
                          ? ExchangeColors.coral
                          : ExchangeColors.blue,
                      background: source.sourceType == 'video'
                          ? ExchangeColors.coralSoft
                          : ExchangeColors.blueSoft,
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            source.title,
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            [
                              source.platform,
                              ...source.themes.take(2),
                            ].where((item) => item.isNotEmpty).join(' · '),
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          if (source.summary.isNotEmpty) ...[
                            const SizedBox(height: 8),
                            Text(
                              source.summary,
                              maxLines: 3,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ],
                      ),
                    ),
                    const Icon(
                      Icons.open_in_new_rounded,
                      size: 18,
                      color: ExchangeColors.secondaryInk,
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _SourceButtons extends StatelessWidget {
  const _SourceButtons({required this.school});

  final PartnerUniversity school;

  @override
  Widget build(BuildContext context) {
    final links = <({String label, String url})>[
      if (school.imagePageUrl.isNotEmpty)
        (label: '官方圖片來源', url: school.imagePageUrl),
      if (school.sourceUrl.isNotEmpty)
        (label: '長庚合作校資料', url: school.sourceUrl),
      if (school.website.isNotEmpty) (label: '合作校官方網站', url: school.website),
    ];
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: links
          .map(
            (link) => OutlinedButton.icon(
              onPressed: () => _openUrl(link.url),
              icon: const Icon(Icons.open_in_new_rounded),
              label: Text(link.label),
            ),
          )
          .toList(),
    );
  }
}

Future<void> _openUrl(String value) async {
  final uri = Uri.tryParse(value);
  if (uri == null) return;
  await launchUrl(uri, mode: LaunchMode.externalApplication);
}
