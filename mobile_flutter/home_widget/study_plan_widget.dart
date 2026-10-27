import 'package:home_widget_generator/home_widget_generator.dart';

@HomeWidget(
  name: 'StudyPlanWidget',
  description: '快速查看下一個交換申請任務與準備進度。',
  android: HomeWidgetAndroidConfiguration(
    packageName: 'tw.edu.cgu.exchange_guide_flutter',
    minWidth: 180,
    minHeight: 88,
    minResizeWidth: 120,
    minResizeHeight: 72,
    targetCellWidth: 4,
    targetCellHeight: 2,
    resizeMode: HWAndroidResizeMode.horizontalAndVertical,
    widgetCategory: HWAndroidWidgetCategory.homeScreen,
    updatePeriodMillis: 1800000,
    backgroundColor: HWColor.themed(
      light: HWColor.fixed(0xFFF7FAFB),
      dark: HWColor.fixed(0xFF17232C),
    ),
  ),
  iOS: HomeWidgetIOSConfiguration(
    groupId: 'group.tw.uniway.app',
    supportedFamilies: [
      HWWidgetFamily.systemSmall,
      HWWidgetFamily.systemMedium,
      HWWidgetFamily.accessoryInline,
      HWWidgetFamily.accessoryCircular,
      HWWidgetFamily.accessoryRectangular,
    ],
    backgroundColor: HWColor.themed(
      light: HWColor.fixed(0xFFF7FAFB),
      dark: HWColor.fixed(0xFF17232C),
    ),
  ),
  widget: HWFill(
    child: HWColumn(
      crossAxisAlignment: HWCrossAxisAlignment.start,
      mainAxisAlignment: HWMainAxisAlignment.spaceBetween,
      children: [
        HWText.fixed(
          '交換計畫',
          style: HWRoleTextStyle(
            role: HWTextStyleRole.caption,
            color: HWColor.themed(
              light: HWColor.fixed(0xFF087C8C),
              dark: HWColor.fixed(0xFF74D6DE),
            ),
            fontWeight: HWFontWeight.bold,
          ),
        ),
        HWText(
          HWString('nextTitle', defaultValue: '設定你的交換目標'),
          style: HWRoleTextStyle(
            role: HWTextStyleRole.headline,
            color: HWColor.themed(
              light: HWColor.fixed(0xFF15212C),
              dark: HWColor.fixed(0xFFF6FAFC),
            ),
            fontWeight: HWFontWeight.bold,
          ),
        ),
        HWText(
          HWString('nextDateLabel', defaultValue: '開啟 App 開始規劃'),
          style: HWRoleTextStyle(
            role: HWTextStyleRole.caption,
            color: HWColor.themed(
              light: HWColor.fixed(0xFF596875),
              dark: HWColor.fixed(0xFFB8C7D0),
            ),
          ),
        ),
        HWText(
          HWString('progressLabel', defaultValue: '準備進度 0%'),
          style: HWRoleTextStyle(
            role: HWTextStyleRole.captionSmall,
            color: HWColor.themed(
              light: HWColor.fixed(0xFF087C8C),
              dark: HWColor.fixed(0xFF74D6DE),
            ),
            fontWeight: HWFontWeight.w700,
          ),
        ),
      ],
    ),
  ),
)
class StudyPlanWidgetDefinition {}
