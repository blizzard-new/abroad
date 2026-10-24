import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/application_calendar.dart';
import '../core/exchange_widgets.dart';
import '../core/student_ui.dart';
import '../core/student_plan.dart';
import '../core/study_plan_widget_service.dart';
import 'widget_style_preview.dart';
import '../state/exchange_store.dart';
import 'feature_screens.dart';

class BudgetScreen extends StatefulWidget {
  const BudgetScreen({super.key});

  @override
  State<BudgetScreen> createState() => _BudgetScreenState();
}

class _BudgetScreenState extends State<BudgetScreen> {
  final monthsController = TextEditingController(text: '5');
  final housingController = TextEditingController();
  final foodController = TextEditingController();
  final transportController = TextEditingController();
  final otherController = TextEditingController();
  final oneTimeController = TextEditingController();
  final scholarshipController = TextEditingController();
  String selectedSchool = '';
  String currency = 'TWD';
  bool initialized = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (initialized) return;
    initialized = true;
    final store = ExchangeStoreScope.of(context);
    final schools = store.dashboard?.partnerUniversities ?? const [];
    if (schools.isEmpty) return;
    selectedSchool = store.favorites.firstOrNull ?? schools.first.schoolName;
    _loadPlan(store);
  }

  @override
  void dispose() {
    monthsController.dispose();
    housingController.dispose();
    foodController.dispose();
    transportController.dispose();
    otherController.dispose();
    oneTimeController.dispose();
    scholarshipController.dispose();
    super.dispose();
  }

  void _loadPlan(ExchangeStore store) {
    final plan = store.budgetFor(selectedSchool);
    currency = plan?.currency ?? 'TWD';
    monthsController.text = (plan?.months ?? 5).toString();
    housingController.text = _inputValue(plan?.monthlyHousing);
    foodController.text = _inputValue(plan?.monthlyFood);
    transportController.text = _inputValue(plan?.monthlyTransport);
    otherController.text = _inputValue(plan?.monthlyOther);
    oneTimeController.text = _inputValue(plan?.oneTimeCosts);
    scholarshipController.text = _inputValue(plan?.scholarship);
    setState(() {});
  }

  ExchangeBudgetPlan _currentPlan() => ExchangeBudgetPlan(
    schoolName: selectedSchool,
    currency: currency,
    months: int.tryParse(monthsController.text.trim()) ?? 5,
    monthlyHousing: _number(housingController),
    monthlyFood: _number(foodController),
    monthlyTransport: _number(transportController),
    monthlyOther: _number(otherController),
    oneTimeCosts: _number(oneTimeController),
    scholarship: _number(scholarshipController),
  );

  Future<void> _save(ExchangeStore store) async {
    if (selectedSchool.isEmpty) return;
    final plan = _currentPlan();
    if (plan.months < 1 || plan.months > 24) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('研修月數請填 1 到 24 個月。')));
      return;
    }
    await store.saveBudgetPlan(plan);
    if (!mounted) return;
    setState(() {});
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('交換預算已儲存。')));
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final schools = store.dashboard?.partnerUniversities ?? const [];
    final selected = schools
        .where((school) => school.schoolName == selectedSchool)
        .firstOrNull;
    final plan = selectedSchool.isEmpty ? null : _currentPlan();

    return FeaturePageScaffold(
      title: '交換預算',
      bottomBar: schools.isEmpty
          ? null
          : StudentActionBar(
              primary: FilledButton.icon(
                onPressed: () => _save(store),
                icon: const Icon(Icons.save_outlined),
                label: const Text('儲存估算'),
              ),
            ),
      children: [
        if (schools.isEmpty)
          const EmptyState(
            icon: Icons.calculate_outlined,
            title: '尚無合作校資料',
            message: '資料載入後即可開始估算。',
          )
        else ...[
          const StudentSectionTitle(
            '目的地與期間',
            icon: Icons.flight_takeoff_rounded,
          ),
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                DropdownButtonFormField<String>(
                  initialValue: selectedSchool,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: '估算學校',
                    prefixIcon: Icon(Icons.school_outlined),
                  ),
                  items: schools
                      .map(
                        (school) => DropdownMenuItem(
                          value: school.schoolName,
                          child: Text(
                            school.schoolName,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (value) {
                    if (value == null) return;
                    selectedSchool = value;
                    _loadPlan(store);
                  },
                ),
                const SizedBox(height: 16),
                _BudgetField(
                  controller: monthsController,
                  label: '研修月數',
                  suffix: '個月',
                  onChanged: () => setState(() {}),
                ),
                const SizedBox(height: 12),
                const StudentSectionTitle(
                  '每月花費',
                  icon: Icons.payments_outlined,
                ),
                _BudgetField(
                  controller: housingController,
                  currency: currency,
                  label: '每月住宿',
                  onChanged: () => setState(() {}),
                ),
                const SizedBox(height: 12),
                _BudgetField(
                  controller: foodController,
                  currency: currency,
                  label: '每月飲食',
                  onChanged: () => setState(() {}),
                ),
                const SizedBox(height: 12),
                _BudgetField(
                  controller: transportController,
                  currency: currency,
                  label: '每月交通',
                  onChanged: () => setState(() {}),
                ),
                const SizedBox(height: 12),
                _BudgetField(
                  controller: otherController,
                  currency: currency,
                  label: '每月其他支出',
                  onChanged: () => setState(() {}),
                ),
                const SizedBox(height: 12),
                const StudentSectionTitle(
                  '一次支出與補助',
                  icon: Icons.account_balance_wallet_outlined,
                ),
                _BudgetField(
                  controller: oneTimeController,
                  currency: currency,
                  label: '機票、簽證與保險',
                  onChanged: () => setState(() {}),
                ),
                const SizedBox(height: 12),
                _BudgetField(
                  controller: scholarshipController,
                  currency: currency,
                  label: '預計補助',
                  onChanged: () => setState(() {}),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          if (plan != null) _BudgetResult(plan: plan),
          if (selected != null && selected.tuitionPoints.isNotEmpty) ...[
            const SizedBox(height: 16),
            GlassCard(
              padding: EdgeInsets.zero,
              child: ExpansionTile(
                minTileHeight: 60,
                shape: const Border(),
                collapsedShape: const Border(),
                leading: const ExchangeIconBadge(Icons.menu_book_outlined),
                title: const Text('官方費用參考'),
                childrenPadding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
                children: [
                  ...selected.tuitionPoints.map(BulletPoint.new),
                  if (selected.sourceUrl.isNotEmpty)
                    Align(
                      alignment: Alignment.centerLeft,
                      child: OutlinedButton.icon(
                        onPressed: () => launchUrl(
                          Uri.parse(selected.sourceUrl),
                          mode: LaunchMode.externalApplication,
                        ),
                        icon: const Icon(Icons.open_in_new_rounded),
                        label: const Text('查看官方來源'),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ],
      ],
    );
  }
}

class WidgetSettingsScreen extends StatefulWidget {
  const WidgetSettingsScreen({super.key});

  @override
  State<WidgetSettingsScreen> createState() => _WidgetSettingsScreenState();
}

class _WidgetSettingsScreenState extends State<WidgetSettingsScreen> {
  bool started = false;
  bool checking = true;
  bool canPin = false;
  StudyPlanWidgetStyle selectedStyle = StudyPlanWidgetStyle.overview;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (started) return;
    started = true;
    final store = ExchangeStoreScope.of(context);
    store.canRequestHomeWidgetPin().then((value) {
      if (!mounted) return;
      setState(() {
        canPin = value;
        checking = false;
      });
    });
  }

  Future<void> _pin(ExchangeStore store) async {
    await store.requestHomeWidgetPin(style: selectedStyle);
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('已開啟系統的小工具加入流程。')));
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final events = store.personalCalendarEvents.toList()
      ..sort((a, b) => a.date.compareTo(b.date));
    final event = events
        .where(
          (item) => !dateOnly(item.date).isBefore(dateOnly(DateTime.now())),
        )
        .firstOrNull;
    final isAndroid =
        !kIsWeb && defaultTargetPlatform == TargetPlatform.android;
    final signedIn = store.account != null;
    return FeaturePageScaffold(
      title: '桌面小工具',
      bottomBar: isAndroid
          ? StudentActionBar(
              primary: FilledButton.icon(
                onPressed: checking || !canPin ? null : () => _pin(store),
                icon: const Icon(Icons.add_to_home_screen_outlined),
                label: Text(
                  checking
                      ? '準備中…'
                      : canPin
                      ? '加入桌面'
                      : '從桌面選單加入',
                ),
              ),
            )
          : null,
      children: [
        const StudentSectionTitle(
          '選擇樣式',
          icon: Icons.widgets_outlined,
          detail: '可加入多款，長按桌面調整大小',
        ),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: StudyPlanWidgetStyle.values
              .map(
                (style) => ChoiceChip(
                  avatar: Icon(WidgetStylePreview.icon(style), size: 18),
                  label: Text(style.label),
                  selected: selectedStyle == style,
                  onSelected: (_) => setState(() => selectedStyle = style),
                ),
              )
              .toList(),
        ),
        const SizedBox(height: 24),
        WidgetStylePreview(
          style: selectedStyle,
          title: signedIn
              ? (event?.title ?? store.nextPlanAction)
              : '登入後開始交換計畫',
          dateLabel: event == null
              ? '儲存申請日期後顯示倒數'
              : '${event.date.year}/${event.date.month}/${event.date.day}',
          deadline: signedIn ? event?.date : null,
          percent: signedIn ? store.planCompletionPercent : 0,
          tasks: signedIn
              ? applicationDocumentLabels
                    .where(
                      (label) =>
                          store.documentStatus(label) !=
                          DocumentPreparationStatus.ready,
                    )
                    .take(3)
                    .toList()
              : const [],
        ),
        const SizedBox(height: 16),
        StudentNotice(
          selectedStyle.detail,
          icon: WidgetStylePreview.icon(selectedStyle),
        ),
        const SizedBox(height: 24),
        if (isAndroid)
          const _WidgetInstruction(
            icon: Icons.android_rounded,
            title: '加入手機桌面',
            points: ['點下方按鈕，再確認加入。', '也可長按桌面 → 小工具 → UniWay。'],
          )
        else
          const _WidgetInstruction(
            icon: Icons.phone_iphone_rounded,
            title: 'iPhone 加入方式',
            points: ['長按主畫面 → 編輯 → 加入小工具 → UniWay。', '交換總覽也支援鎖定畫面的小工具。'],
          ),
        const SizedBox(height: 16),
        const StudentNotice(
          '開啟 App 同步最新進度；桌面會顯示已儲存的計畫。',
          icon: Icons.sync_rounded,
        ),
      ],
    );
  }
}

class _BudgetField extends StatelessWidget {
  const _BudgetField({
    required this.controller,
    required this.label,
    required this.onChanged,
    this.suffix,
    this.currency = 'TWD',
  });

  final TextEditingController controller;
  final String label;
  final VoidCallback onChanged;
  final String? suffix;
  final String currency;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      onChanged: (_) => onChanged(),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(switch (label) {
          '每月住宿' => Icons.home_outlined,
          '每月飲食' => Icons.restaurant_outlined,
          '每月交通' => Icons.directions_transit_outlined,
          '研修月數' => Icons.date_range_outlined,
          '機票、簽證與保險' => Icons.flight_outlined,
          _ => Icons.payments_outlined,
        }),
        prefixText: suffix == null ? '$currency ' : null,
        suffixText: suffix,
      ),
    );
  }
}

class _BudgetResult extends StatelessWidget {
  const _BudgetResult({required this.plan});

  final ExchangeBudgetPlan plan;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('扣除預計補助後', style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 4),
          Text(
            '${plan.currency} ${_money(plan.netTotal)}',
            style: Theme.of(context).textTheme.displaySmall,
          ),
          const SizedBox(height: 16),
          _BudgetLine(
            currency: plan.currency,
            label: '每月生活',
            value: plan.monthlyTotal,
          ),
          _BudgetLine(
            currency: plan.currency,
            label: '${plan.months} 個月生活費',
            value: plan.monthlyTotal * plan.months,
          ),
          _BudgetLine(
            currency: plan.currency,
            label: '一次性支出',
            value: plan.oneTimeCosts,
          ),
          _BudgetLine(
            currency: plan.currency,
            label: '預計補助',
            value: -plan.scholarship,
          ),
        ],
      ),
    );
  }
}

class _BudgetLine extends StatelessWidget {
  const _BudgetLine({
    required this.label,
    required this.value,
    required this.currency,
  });

  final String label;
  final double value;
  final String currency;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Expanded(child: Text(label)),
          Text(
            '${value < 0 ? '-' : ''}$currency ${_money(value.abs())}',
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}

class _WidgetInstruction extends StatelessWidget {
  const _WidgetInstruction({
    required this.icon,
    required this.title,
    required this.points,
  });

  final IconData icon;
  final String title;
  final List<String> points;

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
            ],
          ),
          const SizedBox(height: 16),
          ...points.map(BulletPoint.new),
        ],
      ),
    );
  }
}

double _number(TextEditingController controller) =>
    double.tryParse(controller.text.replaceAll(',', '').trim()) ?? 0;

String _inputValue(double? value) {
  if (value == null || value == 0) return '';
  if (value == value.roundToDouble()) return value.toInt().toString();
  return value.toStringAsFixed(1);
}

String _money(double value) {
  final digits = value.round().toString();
  return digits.replaceAllMapped(RegExp(r'\B(?=(\d{3})+(?!\d))'), (_) => ',');
}
