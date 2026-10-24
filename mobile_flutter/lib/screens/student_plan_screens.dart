import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/application_calendar.dart';
import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';
import '../core/student_plan.dart';
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
      children: [
        if (schools.isEmpty)
          const EmptyState(
            icon: Icons.calculate_outlined,
            title: '尚無合作校資料',
            message: '資料載入後即可開始估算。',
          )
        else ...[
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                DropdownButtonFormField<String>(
                  initialValue: selectedSchool,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: '估算學校'),
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
                const SizedBox(height: 14),
                _BudgetField(
                  controller: monthsController,
                  label: '研修月數',
                  suffix: '個月',
                  onChanged: () => setState(() {}),
                ),
                const SizedBox(height: 12),
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
                const SizedBox(height: 18),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () => _save(store),
                    icon: const Icon(Icons.save_outlined),
                    label: const Text('儲存估算'),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          if (plan != null) _BudgetResult(plan: plan),
          if (selected != null && selected.tuitionPoints.isNotEmpty) ...[
            const SizedBox(height: 14),
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
    await store.requestHomeWidgetPin();
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('已開啟系統的小工具加入流程。')));
  }

  @override
  Widget build(BuildContext context) {
    final store = ExchangeStoreScope.of(context);
    final event = store.personalCalendarEvents
        .where(
          (item) => !dateOnly(item.date).isBefore(dateOnly(DateTime.now())),
        )
        .firstOrNull;
    final isAndroid =
        !kIsWeb && defaultTargetPlatform == TargetPlatform.android;

    return FeaturePageScaffold(
      title: '桌面小工具',
      children: [
        GlassCard(
          tint: ExchangeColors.blueSoft,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '交換計畫',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: ExchangeColors.teal,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                event?.title ?? store.nextPlanAction,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              Text(
                event == null
                    ? (store.planProfile?.goalLabel.isNotEmpty == true
                          ? store.planProfile!.goalLabel
                          : '開啟 App 開始規劃')
                    : '${countdownLabel(event.date)} · ${event.date.month}/${event.date.day}',
              ),
              const SizedBox(height: 14),
              LinearProgressIndicator(
                value: store.planCompletionPercent / 100,
                minHeight: 7,
                borderRadius: BorderRadius.circular(999),
              ),
              const SizedBox(height: 7),
              Text(
                '準備進度 ${store.planCompletionPercent}%',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (isAndroid)
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: checking || !canPin ? null : () => _pin(store),
              icon: checking
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.add_to_home_screen_outlined),
              label: Text(canPin ? '加入 Android 桌面' : '請從桌面小工具選單加入'),
            ),
          ),
        if (isAndroid) const SizedBox(height: 12),
        const _WidgetInstruction(
          icon: Icons.android_rounded,
          title: 'Android 桌面小工具',
          points: [
            '長按桌面空白處，開啟「小工具」並選擇 UniWay。',
            '加入後可長按調整大小；寬版會顯示待辦。開啟 App 後同步最新進度。',
          ],
        ),
        const SizedBox(height: 12),
        if (!isAndroid)
          const _WidgetInstruction(
            icon: Icons.phone_iphone_rounded,
            title: 'iPhone 桌面與鎖定畫面',
            points: ['長按主畫面後加入「交換計畫」小工具。', 'iOS 16 以上可在鎖定畫面加入直列、圓形或矩形版本。'],
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
            style: const TextStyle(fontWeight: FontWeight.w700),
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
          const SizedBox(height: 14),
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
