// Generated with home_widget, then customized for home and lock screen widgets.

import SwiftUI
import WidgetKit

struct Provider: TimelineProvider {
  func placeholder(in context: Context) -> StudyPlanWidgetDefinitionHomeWidgetEntry {
    StudyPlanWidgetDefinitionHomeWidgetEntry(date: Date(), data: StudyPlanWidgetDefinitionData.fromUserDefaults(nil))
  }

  func getSnapshot(in context: Context, completion: @escaping (StudyPlanWidgetDefinitionHomeWidgetEntry) -> Void) {
    let prefs = UserDefaults(suiteName: "group.tw.edu.cgu.exchangeGuideFlutter")
    let data = StudyPlanWidgetDefinitionData.fromUserDefaults(prefs)

    completion(StudyPlanWidgetDefinitionHomeWidgetEntry(date: Date(), data: data))

  }

  func getTimeline(in context: Context, completion: @escaping (Timeline<Entry>) -> Void) {
    let prefs = UserDefaults(suiteName: "group.tw.edu.cgu.exchangeGuideFlutter")
    let data = StudyPlanWidgetDefinitionData.fromUserDefaults(prefs)

    completion(Timeline(entries: [StudyPlanWidgetDefinitionHomeWidgetEntry(date: Date(), data: data)], policy: .atEnd))

  }
}

struct StudyPlanWidgetDefinitionHomeWidgetEntry: TimelineEntry {
  let date: Date
  let data: StudyPlanWidgetDefinitionData
}


struct StudyPlanWidgetDefinitionHomeWidgetEntryView: View {
  var entry: Provider.Entry

  @Environment(\.colorScheme) var colorScheme
  @Environment(\.widgetFamily) var family

  private var progress: Double {
    let digits = (entry.data.progressLabel ?? "").filter { $0.isNumber }
    return min(max((Double(digits) ?? 0) / 100, 0), 1)
  }

  @ViewBuilder
  var body: some View {
    switch family {
    case .accessoryInline:
      Label(entry.data.nextTitle ?? "交換計畫", systemImage: "airplane.departure")
    case .accessoryCircular:
      Gauge(value: progress) {
        Image(systemName: "airplane.departure")
      } currentValueLabel: {
        Text("\(Int(progress * 100))")
          .font(.caption2.bold())
      }
      .gaugeStyle(.accessoryCircular)
    case .accessoryRectangular:
      VStack(alignment: .leading, spacing: 2) {
        Label("交換計畫", systemImage: "airplane.departure")
          .font(.caption2.bold())
        Text(entry.data.nextTitle ?? "設定交換目標")
          .font(.caption.bold())
          .lineLimit(1)
        Text(entry.data.nextDateLabel ?? "開啟 App 開始規劃")
          .font(.caption2)
          .lineLimit(1)
      }
    default:
      homeWidget
    }
  }

  private var homeWidget: some View {
    VStack(alignment: .leading, spacing: 8) {
      Label("交換計畫", systemImage: "airplane.departure")
        .font(.caption.bold())
        .foregroundStyle(accentColor)
      Spacer(minLength: 2)
      Text(entry.data.nextTitle ?? "設定你的交換目標")
        .font(.headline.bold())
        .lineLimit(2)
        .foregroundStyle(primaryTextColor)
      Text(entry.data.nextDateLabel ?? "開啟 App 開始規劃")
        .font(.caption)
        .lineLimit(1)
        .foregroundStyle(secondaryTextColor)
      Text(entry.data.progressLabel ?? "準備進度 0%")
        .font(.caption2.bold())
        .foregroundStyle(accentColor)
    }
    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
    .applyContainerBackground(backgroundColor)
  }

  private var accentColor: Color {
    colorScheme == .dark ? Color(red: 0.45, green: 0.84, blue: 0.87) : Color(red: 0.03, green: 0.49, blue: 0.55)
  }

  private var primaryTextColor: Color {
    colorScheme == .dark ? Color(red: 0.96, green: 0.98, blue: 0.99) : Color(red: 0.08, green: 0.13, blue: 0.17)
  }

  private var secondaryTextColor: Color {
    colorScheme == .dark ? Color(red: 0.72, green: 0.78, blue: 0.82) : Color(red: 0.35, green: 0.41, blue: 0.46)
  }

  private var backgroundColor: Color {
    colorScheme == .dark ? Color(red: 0.09, green: 0.14, blue: 0.17) : Color(red: 0.97, green: 0.98, blue: 0.98)
  }
}

struct StudyPlanWidgetDefinitionHomeWidget: Widget {
  let kind: String = "StudyPlanWidgetDefinitionHomeWidget"

  var body: some WidgetConfiguration {
    StaticConfiguration(kind: kind, provider: Provider()) { entry in
      StudyPlanWidgetDefinitionHomeWidgetEntryView(entry: entry)
        .widgetURL(URL(string: "exchangeguide://plan"))
    }
    .configurationDisplayName("交換計畫")
    .description("快速查看下一個交換申請任務與準備進度。")
    .supportedFamilies([.systemSmall, .systemMedium, .accessoryInline, .accessoryCircular, .accessoryRectangular])
  }
}

extension View {
  @ViewBuilder
  func applyContainerBackground<T: View>(_ backgroundView: T) -> some View {
    if #available(iOSApplicationExtension 17.0, *) {
      self.containerBackground(for: .widget) { backgroundView }
    } else {
      self.background(backgroundView)
    }
  }
}

struct StudyPlanWidgetDefinitionData {
  let nextTitle: String?
  let nextDateLabel: String?
  let progressLabel: String?

  static let paramPrefix = "home_widget.StudyPlanWidgetDefinition"

  static func fromUserDefaults(_ defaults: UserDefaults?) -> StudyPlanWidgetDefinitionData {
    return StudyPlanWidgetDefinitionData(
      nextTitle: (defaults?.string(forKey: "\(paramPrefix).nextTitle") ?? "設定你的交換目標"),
      nextDateLabel: (defaults?.string(forKey: "\(paramPrefix).nextDateLabel") ?? "開啟 App 開始規劃"),
      progressLabel: (defaults?.string(forKey: "\(paramPrefix).progressLabel") ?? "準備進度 0%"),
    )
  }
}
