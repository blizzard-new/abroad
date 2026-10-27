import SwiftUI
import WidgetKit

enum UniWayWidgetStyle {
  case overview, countdown, checklist, progress
  var title: String {
    switch self {
    case .overview: return "交換總覽"
    case .countdown: return "出發倒數"
    case .checklist: return "準備清單"
    case .progress: return "準備進度"
    }
  }
  var symbol: String {
    switch self {
    case .overview: return "airplane.departure"
    case .countdown: return "calendar"
    case .checklist: return "checklist"
    case .progress: return "chart.donut"
    }
  }
  var accent: Color {
    switch self {
    case .countdown: return Color(red: 0.67, green: 0.29, blue: 0.20)
    case .checklist: return Color(red: 0, green: 0.42, blue: 0.40)
    default: return Color(red: 0.19, green: 0.36, blue: 0.66)
    }
  }
}

struct PlanEntry: TimelineEntry {
  let date: Date
  let title: String
  let dateLabel: String
  let progressLabel: String
  let tasks: [String]
  let deadline: Date?
  let updated: String
  var progress: Double {
    guard let percent = progressLabel.range(of: #"\d+(?=%)"#, options: .regularExpression) else { return 0 }
    return min(max((Double(progressLabel[percent]) ?? 0) / 100, 0), 1)
  }
  var days: Int? {
    guard let deadline else { return nil }
    return Calendar.current.dateComponents([.day], from: Calendar.current.startOfDay(for: date), to: deadline).day
  }
  static func read(_ prefs: UserDefaults?, at date: Date = Date()) -> PlanEntry {
    let prefix = "home_widget.StudyPlanWidgetDefinition."
    let format = DateFormatter()
    format.locale = Locale(identifier: "en_US_POSIX")
    format.dateFormat = "yyyy-MM-dd"
    return PlanEntry(date: date,
      title: prefs?.string(forKey: prefix + "nextTitle") ?? "登入後開始交換計畫",
      dateLabel: prefs?.string(forKey: prefix + "nextDateLabel") ?? "點一下開啟 UniWay",
      progressLabel: prefs?.string(forKey: prefix + "progressLabel") ?? "尚未登入",
      tasks: (prefs?.string(forKey: prefix + "tasks") ?? "").split(separator: "\n").map(String.init),
      deadline: format.date(from: prefs?.string(forKey: prefix + "deadlineIso") ?? ""),
      updated: prefs?.string(forKey: prefix + "updatedLabel") ?? "")
  }
}

struct PlanProvider: TimelineProvider {
  func placeholder(in context: Context) -> PlanEntry { PlanEntry.read(nil) }
  func getSnapshot(in context: Context, completion: @escaping (PlanEntry) -> Void) {
    completion(PlanEntry.read(UserDefaults(suiteName: "group.tw.uniway.app")))
  }
  func getTimeline(in context: Context, completion: @escaping (Timeline<PlanEntry>) -> Void) {
    let prefs = UserDefaults(suiteName: "group.tw.uniway.app")
    let now = Date()
    // Midnight entries update countdowns without opening the app.
    let tomorrow = Calendar.current.date(byAdding: .day, value: 1, to: Calendar.current.startOfDay(for: now))!
    completion(Timeline(entries: [PlanEntry.read(prefs, at: now), PlanEntry.read(prefs, at: tomorrow)], policy: .after(tomorrow)))
  }
}

struct PlanWidgetView: View {
  let entry: PlanEntry
  let style: UniWayWidgetStyle
  @Environment(\.widgetFamily) private var family
  var body: some View {
    Group {
      switch family {
      case .accessoryInline:
        Label(entry.title, systemImage: style.symbol)
      case .accessoryCircular:
        Gauge(value: entry.progress) { Image(systemName: style.symbol) } currentValueLabel: {
          Text("\(Int(entry.progress * 100))").font(.caption2)
        }.gaugeStyle(.accessoryCircular)
      case .accessoryRectangular:
        VStack(alignment: .leading) {
          Label(style.title, systemImage: style.symbol).font(.caption2)
          Text(entry.title).font(.caption.bold()).lineLimit(1)
          Text(entry.dateLabel).font(.caption2).lineLimit(1)
        }
      default: home
      }
    }
    .widgetURL(URL(string: "tw.uniway.app://journey"))
    .applyContainerBackground(
      LinearGradient(colors: [Color(red: 0.89, green: 0.95, blue: 0.93), Color.white], startPoint: .topLeading, endPoint: .bottomTrailing))
  }
  private var home: some View {
    VStack(alignment: .leading, spacing: 8) {
      Label(style.title, systemImage: style.symbol).font(.caption.weight(.semibold)).foregroundStyle(style.accent)
      Spacer(minLength: 0)
      if style == .countdown, let days = entry.days {
        HStack(alignment: .firstTextBaseline, spacing: 4) {
          Text(days < 0 ? "—" : "\(days)").font(.system(size: 40, weight: .semibold, design: .rounded)).monospacedDigit()
          Text(days < 0 ? "期限已過" : (days == 0 ? "今天" : "天後")).font(.caption)
        }.foregroundStyle(Color(red: 0.09, green: 0.18, blue: 0.22))
        Text(entry.title).font(.caption).lineLimit(2)
      } else if style == .checklist, !entry.tasks.isEmpty {
        ForEach(Array(entry.tasks.prefix(family == .systemSmall ? 2 : 3).enumerated()), id: \.offset) { _, task in
          Label(task, systemImage: "circle").font(.caption).lineLimit(1)
        }
      } else if style == .progress {
        HStack(spacing: 12) {
          ZStack {
            Circle().stroke(style.accent.opacity(0.15), lineWidth: 7)
            Circle().trim(from: 0, to: entry.progress).stroke(style.accent, style: StrokeStyle(lineWidth: 7, lineCap: .round)).rotationEffect(.degrees(-90))
            Text("\(Int(entry.progress * 100))%").font(.headline).monospacedDigit()
          }.frame(width: 64, height: 64)
          if family != .systemSmall { Text(entry.title).font(.caption).lineLimit(3) }
        }
      } else {
        Text(entry.title).font(.headline).lineLimit(2)
        Text(entry.dateLabel).font(.caption).foregroundStyle(Color(red: 0.32, green: 0.40, blue: 0.43)).lineLimit(1)
      }
      Spacer(minLength: 0)
      Text(entry.updated.isEmpty ? entry.progressLabel : entry.updated).font(.caption2).foregroundStyle(style.accent).lineLimit(1)
    }
    .foregroundStyle(Color(red: 0.09, green: 0.18, blue: 0.22))
    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
  }
}

struct StudyPlanWidgetDefinitionHomeWidget: Widget {
  var body: some WidgetConfiguration {
    StaticConfiguration(kind: "StudyPlanWidgetDefinitionHomeWidget", provider: PlanProvider()) { PlanWidgetView(entry: $0, style: .overview) }
      .configurationDisplayName("交換總覽").description("下一步與申請日期")
      .supportedFamilies([.systemSmall, .systemMedium, .accessoryInline, .accessoryCircular, .accessoryRectangular])
  }
}
struct CountdownWidget: Widget {
  var body: some WidgetConfiguration {
    StaticConfiguration(kind: "CountdownWidget", provider: PlanProvider()) { PlanWidgetView(entry: $0, style: .countdown) }
      .configurationDisplayName("出發倒數").description("你已儲存的下一個申請日期")
      .supportedFamilies([.systemSmall, .systemMedium])
  }
}
struct ChecklistWidget: Widget {
  var body: some WidgetConfiguration {
    StaticConfiguration(kind: "ChecklistWidget", provider: PlanProvider()) { PlanWidgetView(entry: $0, style: .checklist) }
      .configurationDisplayName("準備清單").description("尚未完成的申請文件")
      .supportedFamilies([.systemSmall, .systemMedium])
  }
}
struct ProgressWidget: Widget {
  var body: some WidgetConfiguration {
    StaticConfiguration(kind: "ProgressWidget", provider: PlanProvider()) { PlanWidgetView(entry: $0, style: .progress) }
      .configurationDisplayName("準備進度").description("交換準備完成比例")
      .supportedFamilies([.systemSmall, .systemMedium])
  }
}

extension View {
  @ViewBuilder
  func applyContainerBackground<T: View>(_ backgroundView: T) -> some View {
    if #available(iOSApplicationExtension 17.0, *) {
      self.containerBackground(for: .widget) { backgroundView }
    } else { self.padding().background(backgroundView) }
  }
}
