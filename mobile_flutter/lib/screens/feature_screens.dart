import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/school_visuals.dart';
import '../core/student_plan.dart';
import '../data/models.dart';
import '../state/exchange_store.dart';
import 'school_detail_screen.dart';
import 'schools_screen.dart';

class OfficialDeadlinesScreen extends StatelessWidget {
  const OfficialDeadlinesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    return FeaturePageScaffold(
      title: '官方截止日',
      onRefresh: store.refresh,
      children: [
        if (store.isLoading && store.deadlines.isEmpty)
          const LoadingCards(count: 4)
        else if (store.error != null && store.deadlines.isEmpty)
          InlineError(message: store.error!, onRetry: store.refresh)
        else if (store.deadlines.isEmpty)
          const EmptyState(
            icon: Icons.event_busy_outlined,
            title: '目前沒有可辨識日期',
            message: '資料更新後會顯示在這個頁面。',
          )
        else
          ...store.deadlines.map(
            (deadline) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _DeadlineCard(deadline: deadline),
            ),
          ),
      ],
    );
  }
}

class ScholarshipsScreen extends StatelessWidget {
  const ScholarshipsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final items = store.dashboard?.scholarshipInfo ?? const <StudentInfoItem>[];
    return FeaturePageScaffold(
      title: '補助資訊',
      onRefresh: store.refresh,
      children: [
        if (store.isLoading && store.dashboard == null)
          const LoadingCards(count: 4)
        else if (store.error != null && store.dashboard == null)
          InlineError(message: store.error!, onRetry: store.refresh)
        else if (items.isEmpty)
          const EmptyState(
            icon: Icons.money_off_csred_outlined,
            title: '目前沒有補助資料',
            message: '請稍後重新整理，正式規定仍以校方公告為準。',
          )
        else
          ...items.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _StudentInfoCard(
                item: item,
                icon: Icons.account_balance_wallet_outlined,
                badge: _scholarshipBadge(item, store.planProfile),
              ),
            ),
          ),
      ],
    );
  }
}

class EligibilityScreen extends StatefulWidget {
  const EligibilityScreen({super.key});

  @override
  State<EligibilityScreen> createState() => _EligibilityScreenState();
}

class _EligibilityScreenState extends State<EligibilityScreen> {
  final scoreController = TextEditingController();
  final languageScoreController = TextEditingController();
  final monthlyBudgetController = TextEditingController();
  String college = '';
  String degree = '';
  String languageTest = '';
  String targetTerm = '';
  String preferredCountry = '';
  bool needsScholarship = false;
  bool restored = false;
  _EligibilityResult? result;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (restored) return;
    restored = true;
    final profile = ExchangeStoreScope.of(context).planProfile;
    if (profile == null) return;
    college = profile.college;
    degree = profile.degreeLevel;
    languageTest = profile.languageTest;
    targetTerm = profile.targetTerm;
    preferredCountry = profile.preferredCountry;
    needsScholarship = profile.needsScholarship;
    scoreController.text = profile.academicScore?.toString() ?? '';
    languageScoreController.text = profile.languageScore?.toString() ?? '';
    monthlyBudgetController.text = profile.monthlyBudget?.toString() ?? '';
  }

  @override
  void dispose() {
    scoreController.dispose();
    languageScoreController.dispose();
    monthlyBudgetController.dispose();
    super.dispose();
  }

  Future<void> _check(ExchangeStore store) async {
    final academicScore = double.tryParse(scoreController.text.trim());
    final languageScore = double.tryParse(languageScoreController.text.trim());
    final monthlyBudget = double.tryParse(monthlyBudgetController.text.trim());
    if (college.isEmpty ||
        degree.isEmpty ||
        academicScore == null ||
        languageTest.isEmpty ||
        targetTerm.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('請先完成所有必填欄位。')));
      return;
    }

    final profile = StudentPlanProfile(
      college: college,
      degreeLevel: degree,
      academicScore: academicScore,
      languageTest: languageTest,
      languageScore: languageScore,
      targetTerm: targetTerm,
      preferredCountry: preferredCountry,
      monthlyBudget: monthlyBudget,
      needsScholarship: needsScholarship,
    );
    await store.savePlanProfile(profile);
    if (!mounted) return;

    final minimum = switch (languageTest) {
      'toeic' => 700.0,
      'ielts' => 5.5,
      'toefl' => 72.0,
      'duolingo' => 105.0,
      _ => null,
    };
    final languagePass =
        minimum == null || (languageScore != null && languageScore >= minimum);
    final recommendations = store.rankedSchoolMatches;
    final matched = recommendations.where((item) => item.score >= 50).length;

    setState(() {
      result = _EligibilityResult(
        academicPass: academicScore >= 70,
        languagePass: languagePass,
        languageNeedsReview: minimum == null,
        matchedSchools: matched,
        languageMinimum: minimum,
        recommendations: recommendations.take(3).toList(),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final partners =
        store.dashboard?.partnerUniversities ?? const <PartnerUniversity>[];
    final colleges =
        partners
            .expand((school) => school.colleges.split(RegExp(r'[/、,，；;]')))
            .map((value) => value.trim())
            .where((value) => value.isNotEmpty && !value.contains('全校'))
            .toSet()
            .toList()
          ..sort();
    final countries = partners.map((school) => school.country).toSet().toList()
      ..sort();
    final currentYear = DateTime.now().year;
    final targetTerms = [
      '${currentYear + 1} 春季',
      '${currentYear + 1} 秋季',
      '${currentYear + 2} 春季',
      '${currentYear + 2} 秋季',
    ];

    return FeaturePageScaffold(
      title: '資格初判',
      children: [
        GlassCard(
          child: Column(
            children: [
              DropdownButtonFormField<String>(
                initialValue: college.isEmpty ? null : college,
                decoration: const InputDecoration(labelText: '所屬學院'),
                items: colleges
                    .map(
                      (value) =>
                          DropdownMenuItem(value: value, child: Text(value)),
                    )
                    .toList(),
                onChanged: (value) => setState(() => college = value ?? ''),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: degree.isEmpty ? null : degree,
                decoration: const InputDecoration(labelText: '目前學制'),
                items: const [
                  DropdownMenuItem(value: '大學部', child: Text('大學部')),
                  DropdownMenuItem(value: '研究所', child: Text('研究所')),
                ],
                onChanged: (value) => setState(() => degree = value ?? ''),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: scoreController,
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                decoration: const InputDecoration(
                  labelText: '學業平均成績',
                  hintText: '例如 82',
                ),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: languageTest.isEmpty ? null : languageTest,
                decoration: const InputDecoration(labelText: '語言測驗'),
                items: const [
                  DropdownMenuItem(value: 'toeic', child: Text('TOEIC')),
                  DropdownMenuItem(value: 'ielts', child: Text('IELTS')),
                  DropdownMenuItem(value: 'toefl', child: Text('TOEFL iBT')),
                  DropdownMenuItem(value: 'duolingo', child: Text('Duolingo')),
                  DropdownMenuItem(value: 'other', child: Text('其他或尚未準備')),
                ],
                onChanged: (value) =>
                    setState(() => languageTest = value ?? ''),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: languageScoreController,
                enabled: languageTest != 'other',
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                decoration: const InputDecoration(
                  labelText: '語言分數',
                  hintText: '依測驗填寫',
                ),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: targetTerm.isEmpty ? null : targetTerm,
                decoration: const InputDecoration(labelText: '預計交換學期'),
                items: targetTerms
                    .map(
                      (value) =>
                          DropdownMenuItem(value: value, child: Text(value)),
                    )
                    .toList(),
                onChanged: (value) => setState(() => targetTerm = value ?? ''),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: preferredCountry.isEmpty
                    ? null
                    : preferredCountry,
                decoration: const InputDecoration(labelText: '偏好國家（選填）'),
                items: countries
                    .map(
                      (value) =>
                          DropdownMenuItem(value: value, child: Text(value)),
                    )
                    .toList(),
                onChanged: (value) =>
                    setState(() => preferredCountry = value ?? ''),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: monthlyBudgetController,
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                decoration: const InputDecoration(
                  labelText: '每月預算（選填）',
                  prefixText: 'NT\$ ',
                ),
              ),
              const SizedBox(height: 6),
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                value: needsScholarship,
                minTileHeight: 48,
                title: const Text('我需要補助或獎學金'),
                onChanged: (value) =>
                    setState(() => needsScholarship = value ?? false),
              ),
              const SizedBox(height: 18),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: () => _check(store),
                  icon: const Icon(Icons.manage_search_rounded),
                  label: const Text('查看初判結果'),
                ),
              ),
            ],
          ),
        ),
        if (result != null) ...[
          const SizedBox(height: 16),
          _EligibilityResultCard(result: result!),
        ],
        const SizedBox(height: 12),
        Text(
          '初判只協助縮小範圍，正式資格仍以長庚大學與合作校最新公告為準。',
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }
}

class DocumentsScreen extends StatelessWidget {
  const DocumentsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final rules =
        store.dashboard?.ruleExplanations ?? const <RuleExplanation>[];
    return FeaturePageScaffold(
      title: '文件庫',
      onRefresh: store.refresh,
      children: [
        GlassCard(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const ExchangeIconBadge(Icons.checklist_rounded),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '申請文件進度',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        Text(
                          '${store.documentReadyCount}/${applicationDocumentLabels.length} 已完成',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              LinearProgressIndicator(
                value:
                    store.documentReadyCount / applicationDocumentLabels.length,
                minHeight: 7,
                borderRadius: BorderRadius.circular(999),
              ),
              const SizedBox(height: 12),
              ...applicationDocumentLabels.map(
                (label) => _DocumentStatusRow(
                  label: label,
                  status: store.documentStatus(label),
                  onChanged: (status) => store.setDocumentStatus(label, status),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        Text('官方文件重點', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 10),
        if (store.isLoading && store.dashboard == null)
          const LoadingCards(count: 4)
        else if (rules.isEmpty)
          const EmptyState(
            icon: Icons.folder_off_outlined,
            title: '目前沒有文件摘要',
            message: '資料更新後會顯示在這個頁面。',
          )
        else
          ...rules.map(
            (rule) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _RuleCard(rule: rule),
            ),
          ),
      ],
    );
  }
}

class FavoritesScreen extends StatelessWidget {
  const FavoritesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final favorites =
        (store.dashboard?.partnerUniversities ?? const <PartnerUniversity>[])
            .where((school) => store.favorites.contains(school.schoolName))
            .toList();
    return FeaturePageScaffold(
      title: '收藏與比較',
      children: [
        if (favorites.isEmpty)
          EmptyState(
            icon: Icons.bookmark_add_outlined,
            title: '還沒有收藏學校',
            message: '先到找學校頁收藏候選學校，再回來集中比較。',
          )
        else
          ...favorites.map(
            (school) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _FavoriteSchoolCard(school: school, store: store),
            ),
          ),
      ],
    );
  }
}

class FeaturePageScaffold extends StatelessWidget {
  const FeaturePageScaffold({
    required this.title,
    required this.children,
    super.key,
    this.onRefresh,
  });

  final String title;
  final List<Widget> children;
  final Future<void> Function()? onRefresh;

  @override
  Widget build(BuildContext context) {
    final list = ListView(
      padding: const EdgeInsets.fromLTRB(18, 18, 18, 40),
      children: children,
    );
    return ExchangePageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          backgroundColor: Colors.white.withValues(alpha: .72),
          surfaceTintColor: Colors.transparent,
          title: Text(title),
          leading: IconButton(
            tooltip: '返回',
            onPressed: () => Navigator.of(context).pop(),
            constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
            icon: const Icon(Icons.arrow_back_rounded),
          ),
        ),
        body: SafeArea(
          top: false,
          child: onRefresh == null
              ? list
              : RefreshIndicator(onRefresh: onRefresh!, child: list),
        ),
      ),
    );
  }
}

class _DeadlineCard extends StatelessWidget {
  const _DeadlineCard({required this.deadline});

  final DeadlineRecord deadline;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: EdgeInsets.zero,
      child: ExpansionTile(
        minTileHeight: 64,
        shape: const Border(),
        collapsedShape: const Border(),
        leading: const ExchangeIconBadge(
          Icons.schedule_rounded,
          color: ExchangeColors.amber,
          background: ExchangeColors.amberSoft,
        ),
        title: Text(
          deadline.title,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: deadline.publishedAt.isEmpty
            ? null
            : Text(deadline.publishedAt),
        childrenPadding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
        children: [
          ...deadline.snippets.map(BulletPoint.new),
          if (deadline.sourceUrl.isNotEmpty)
            Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton.icon(
                onPressed: () => _openUrl(deadline.sourceUrl),
                icon: const Icon(Icons.open_in_new_rounded),
                label: const Text('查看官方來源'),
              ),
            ),
        ],
      ),
    );
  }
}

class _StudentInfoCard extends StatelessWidget {
  const _StudentInfoCard({required this.item, required this.icon, this.badge});

  final StudentInfoItem item;
  final IconData icon;
  final String? badge;

  @override
  Widget build(BuildContext context) {
    final sourceUrl = item.source?.sourceUrl ?? '';
    return GlassCard(
      padding: EdgeInsets.zero,
      child: ExpansionTile(
        minTileHeight: 64,
        shape: const Border(),
        collapsedShape: const Border(),
        leading: ExchangeIconBadge(
          icon,
          color: ExchangeColors.teal,
          background: ExchangeColors.tealSoft,
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(
                item.title,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (badge != null) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: ExchangeColors.tealSoft,
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  badge!,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: ExchangeColors.teal,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ],
        ),
        childrenPadding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
        children: [
          ...item.details.map(BulletPoint.new),
          if (sourceUrl.isNotEmpty)
            Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton.icon(
                onPressed: () => _openUrl(sourceUrl),
                icon: const Icon(Icons.open_in_new_rounded),
                label: const Text('查看官方來源'),
              ),
            ),
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
    final sourceUrl = rule.documentUrl.isNotEmpty
        ? rule.documentUrl
        : rule.source.sourceUrl;
    return GlassCard(
      padding: EdgeInsets.zero,
      child: ExpansionTile(
        minTileHeight: 64,
        shape: const Border(),
        collapsedShape: const Border(),
        leading: const ExchangeIconBadge(Icons.description_outlined),
        title: Text(rule.title, maxLines: 2, overflow: TextOverflow.ellipsis),
        childrenPadding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
        children: [
          if (rule.summary.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(studentFacingText(rule.summary)),
            ),
          ...rule.keyPoints.map(BulletPoint.new),
          if (sourceUrl.isNotEmpty)
            Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton.icon(
                onPressed: () => _openUrl(sourceUrl),
                icon: const Icon(Icons.open_in_new_rounded),
                label: const Text('查看完整官方文件'),
              ),
            ),
        ],
      ),
    );
  }
}

class _FavoriteSchoolCard extends StatelessWidget {
  const _FavoriteSchoolCard({required this.school, required this.store});

  final PartnerUniversity school;
  final ExchangeStore store;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(12),
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => SchoolDetailScreen(school: school)),
      ),
      child: Row(
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
                Text(
                  school.country,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 3),
                Text(
                  school.schoolName,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 4),
                Text(
                  studentFacingText(school.mobileListSummary),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          IconButton(
            tooltip: '取消收藏',
            onPressed: () => store.toggleFavorite(school.schoolName),
            constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
            icon: const Icon(
              Icons.bookmark_rounded,
              color: ExchangeColors.teal,
            ),
          ),
        ],
      ),
    );
  }
}

class _EligibilityResult {
  const _EligibilityResult({
    required this.academicPass,
    required this.languagePass,
    required this.languageNeedsReview,
    required this.matchedSchools,
    required this.languageMinimum,
    required this.recommendations,
  });

  final bool academicPass;
  final bool languagePass;
  final bool languageNeedsReview;
  final int matchedSchools;
  final double? languageMinimum;
  final List<SchoolMatch> recommendations;
}

class _EligibilityResultCard extends StatelessWidget {
  const _EligibilityResultCard({required this.result});

  final _EligibilityResult result;

  @override
  Widget build(BuildContext context) {
    final ready = result.academicPass && result.languagePass;
    return GlassCard(
      tint: ready ? ExchangeColors.tealSoft : ExchangeColors.amberSoft,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                ready ? Icons.verified_rounded : Icons.info_outline_rounded,
                color: ready ? ExchangeColors.success : ExchangeColors.amber,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  ready ? '符合校內基本門檻' : '仍有條件需要確認',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          BulletPoint(
            result.academicPass ? '平均成績已達 70 分基本門檻。' : '平均成績尚未達 70 分基本門檻。',
          ),
          BulletPoint(
            result.languageNeedsReview
                ? '語言條件需依國家與合作學校另行確認。'
                : result.languagePass
                ? '語言成績已達校內參考門檻 ${result.languageMinimum?.toStringAsFixed(1)}。'
                : '語言成績尚未達校內參考門檻 ${result.languageMinimum?.toStringAsFixed(1)}。',
          ),
          BulletPoint('目前有 ${result.matchedSchools} 間合作校符合學院與學制篩選。'),
          if (result.recommendations.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text('優先查看', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            ...result.recommendations.map(
              (match) => _RecommendedSchoolRow(match: match),
            ),
          ],
          const SizedBox(height: 10),
          FilledButton.icon(
            onPressed: () => Navigator.of(
              context,
            ).push(MaterialPageRoute(builder: (_) => const SchoolsScreen())),
            icon: const Icon(Icons.school_outlined),
            label: const Text('前往找學校'),
          ),
        ],
      ),
    );
  }
}

class _DocumentStatusRow extends StatelessWidget {
  const _DocumentStatusRow({
    required this.label,
    required this.status,
    required this.onChanged,
  });

  final String label;
  final DocumentPreparationStatus status;
  final ValueChanged<DocumentPreparationStatus> onChanged;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      DocumentPreparationStatus.todo => ExchangeColors.secondaryInk,
      DocumentPreparationStatus.preparing => ExchangeColors.amber,
      DocumentPreparationStatus.ready => ExchangeColors.success,
    };
    return Container(
      constraints: const BoxConstraints(minHeight: 64),
      padding: const EdgeInsets.symmetric(vertical: 8),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: ExchangeColors.line)),
      ),
      child: Row(
        children: [
          Icon(
            status == DocumentPreparationStatus.ready
                ? Icons.check_circle_rounded
                : Icons.description_outlined,
            color: color,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(label, style: Theme.of(context).textTheme.bodyMedium),
          ),
          const SizedBox(width: 8),
          DropdownButtonHideUnderline(
            child: DropdownButton<DocumentPreparationStatus>(
              value: status,
              borderRadius: BorderRadius.circular(14),
              items: DocumentPreparationStatus.values
                  .map(
                    (item) =>
                        DropdownMenuItem(value: item, child: Text(item.label)),
                  )
                  .toList(),
              onChanged: (value) {
                if (value != null) onChanged(value);
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _RecommendedSchoolRow extends StatelessWidget {
  const _RecommendedSchoolRow({required this.match});

  final SchoolMatch match;

  @override
  Widget build(BuildContext context) {
    final school = match.school;
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => SchoolDetailScreen(school: school)),
      ),
      child: Container(
        constraints: const BoxConstraints(minHeight: 72),
        padding: const EdgeInsets.symmetric(vertical: 9),
        decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: ExchangeColors.line)),
        ),
        child: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: SizedBox(
                width: 64,
                height: 52,
                child: SchoolPhoto(school: school),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    school.schoolName,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                  const SizedBox(height: 3),
                  Text(
                    match.reasons.take(2).join(' · '),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Text(
              '${match.score}',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: ExchangeColors.teal,
                fontWeight: FontWeight.w800,
              ),
            ),
            const Icon(Icons.chevron_right_rounded, size: 20),
          ],
        ),
      ),
    );
  }
}

String _scholarshipBadge(StudentInfoItem item, StudentPlanProfile? profile) {
  if (profile?.needsScholarship == true) return '優先查看';
  final text = [item.title, ...item.details].join(' ');
  if (RegExp(r'低收入|中低收入|原住民|清寒|身分').hasMatch(text)) {
    return '需確認身分';
  }
  return '補助要點';
}

Future<void> _openUrl(String value) async {
  final uri = Uri.tryParse(value);
  if (uri == null) return;
  await launchUrl(uri, mode: LaunchMode.externalApplication);
}
