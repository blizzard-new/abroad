import SwiftUI

enum ExchangeStatusKind {
    case info, success, warning, danger

    var color: Color {
        switch self {
        case .info: ExchangeColor.accent
        case .success: ExchangeColor.success
        case .warning: ExchangeColor.warning
        case .danger: ExchangeColor.danger
        }
    }

    var background: Color {
        switch self {
        case .info: ExchangeColor.infoBackground
        case .success: ExchangeColor.successBackground
        case .warning: ExchangeColor.warningBackground
        case .danger: ExchangeColor.dangerBackground
        }
    }

    var symbol: String {
        switch self {
        case .info: "info.circle.fill"
        case .success: "checkmark.circle.fill"
        case .warning: "exclamationmark.triangle.fill"
        case .danger: "xmark.octagon.fill"
        }
    }
}

struct ExchangeSectionHeader: View {
    let eyebrow: String?
    let title: String
    let detail: String?

    init(eyebrow: String? = nil, title: String, detail: String? = nil) {
        self.eyebrow = eyebrow
        self.title = title
        self.detail = detail
    }

    var body: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.xxs) {
            if let eyebrow {
                Text(eyebrow)
                    .font(ExchangeTypography.caption)
                    .foregroundStyle(ExchangeColor.accent)
            }
            Text(title)
                .font(ExchangeTypography.title3)
                .foregroundStyle(ExchangeColor.labelPrimary)
                .accessibilityAddTraits(.isHeader)
            if let detail {
                Text(detail)
                    .font(ExchangeTypography.subheadline)
                    .foregroundStyle(ExchangeColor.labelSecondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}

struct ExchangeStatusPill: View {
    let text: String
    let kind: ExchangeStatusKind

    var body: some View {
        Label(text, systemImage: kind.symbol)
            .font(ExchangeTypography.caption)
            .foregroundStyle(kind.color)
            .padding(.horizontal, ExchangeSpacing.sm)
            .padding(.vertical, 6)
            .background(kind.background)
            .clipShape(Capsule())
            .accessibilityElement(children: .combine)
    }
}

struct ExchangeMetricTile: View {
    let value: String
    let label: String
    let symbol: String
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.xs) {
            Image(systemName: symbol)
                .font(.title3.weight(.semibold))
                .foregroundStyle(tint)
                .accessibilityHidden(true)
            Text(value)
                .font(ExchangeTypography.title2)
                .foregroundStyle(ExchangeColor.labelPrimary)
            Text(label)
                .font(ExchangeTypography.caption)
                .foregroundStyle(ExchangeColor.labelSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .exchangeCard()
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(label)，\(value)")
    }
}

struct ExchangeTaskButton: View {
    let title: String
    let detail: String
    let symbol: String
    let tint: Color
    let action: () -> Void

    @State private var tapCount = 0

    var body: some View {
        Button {
            tapCount += 1
            action()
        } label: {
            HStack(spacing: ExchangeSpacing.sm) {
                Image(systemName: symbol)
                    .font(.body.weight(.semibold))
                    .foregroundStyle(tint)
                    .frame(width: 40, height: 40)
                    .background(
                        tint.opacity(0.13),
                        in: RoundedRectangle(cornerRadius: 12, style: .continuous)
                    )
                VStack(alignment: .leading, spacing: ExchangeSpacing.xxs) {
                    Text(title)
                        .font(ExchangeTypography.headline)
                        .foregroundStyle(ExchangeColor.labelPrimary)
                    Text(detail)
                        .font(ExchangeTypography.caption)
                        .foregroundStyle(ExchangeColor.labelSecondary)
                }
                Spacer(minLength: ExchangeSpacing.xs)
                Image(systemName: "chevron.right")
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(ExchangeColor.labelTertiary)
            }
            .padding(ExchangeSpacing.md)
            .frame(maxWidth: .infinity, minHeight: 72, alignment: .leading)
            .contentShape(RoundedRectangle(cornerRadius: ExchangeRadius.control, style: .continuous))
            .exchangeGlassControl(interactive: true)
        }
        .buttonStyle(.plain)
        .hoverEffect(.highlight)
        .sensoryFeedback(.impact(flexibility: .soft), trigger: tapCount)
        .accessibilityHint(detail)
    }
}

struct ExchangeSearchField: View {
    let prompt: String
    @Binding var text: String

    var body: some View {
        HStack(spacing: ExchangeSpacing.xs) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(ExchangeColor.labelTertiary)
                .accessibilityHidden(true)
            TextField(prompt, text: $text)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
            if !text.isEmpty {
                Button {
                    text = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(ExchangeColor.labelTertiary)
                        .frame(width: ExchangeLayout.minimumTarget, height: ExchangeLayout.minimumTarget)
                }
                .accessibilityLabel("清除搜尋")
            }
        }
        .padding(.leading, ExchangeSpacing.sm)
        .frame(minHeight: ExchangeLayout.fieldHeight)
        .background(ExchangeColor.backgroundTertiary)
        .clipShape(RoundedRectangle(cornerRadius: ExchangeRadius.control, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: ExchangeRadius.control, style: .continuous)
                .stroke(ExchangeColor.separator, lineWidth: 1)
        }
    }
}

struct ExchangeFilterChip: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(ExchangeTypography.caption)
                .foregroundStyle(isSelected ? Color(uiColor: UIColor(hex: 0x061018)) : ExchangeColor.labelSecondary)
                .padding(.horizontal, ExchangeSpacing.sm)
                .frame(minHeight: ExchangeLayout.minimumTarget)
                .background(isSelected ? ExchangeColor.accent : ExchangeColor.backgroundTertiary)
                .clipShape(Capsule())
        }
        .buttonStyle(.plain)
        .accessibilityValue(isSelected ? "已選取" : "未選取")
    }
}

struct ExchangeInlineBanner: View {
    let title: String
    let message: String
    let kind: ExchangeStatusKind

    var body: some View {
        HStack(alignment: .top, spacing: ExchangeSpacing.sm) {
            Image(systemName: kind.symbol)
                .foregroundStyle(kind.color)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: ExchangeSpacing.xxs) {
                Text(title)
                    .font(ExchangeTypography.headline)
                    .foregroundStyle(ExchangeColor.labelPrimary)
                Text(message)
                    .font(ExchangeTypography.subheadline)
                    .foregroundStyle(ExchangeColor.labelSecondary)
            }
        }
        .padding(ExchangeSpacing.md)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(kind.background)
        .clipShape(RoundedRectangle(cornerRadius: ExchangeRadius.card, style: .continuous))
        .overlay(alignment: .leading) {
            Rectangle().fill(kind.color).frame(width: 3)
        }
        .accessibilityElement(children: .combine)
    }
}

struct ExchangeLoadingState: View {
    let message: String

    var body: some View {
        VStack(spacing: ExchangeSpacing.md) {
            ProgressView()
                .controlSize(.large)
                .tint(ExchangeColor.accent)
            Text(message)
                .font(ExchangeTypography.subheadline)
                .foregroundStyle(ExchangeColor.labelSecondary)
        }
        .frame(maxWidth: .infinity, minHeight: 180)
        .accessibilityElement(children: .combine)
        .accessibilityLabel(message)
    }
}

struct ExchangeEmptyState: View {
    let title: String
    let message: String
    let symbol: String

    var body: some View {
        ContentUnavailableView(
            title,
            systemImage: symbol,
            description: Text(message)
        )
    }
}

struct ExchangeErrorState: View {
    let message: String
    let retry: () -> Void

    var body: some View {
        VStack(spacing: ExchangeSpacing.lg) {
            ExchangeInlineBanner(title: "資料載入失敗", message: message, kind: .danger)
            Button("重新載入", action: retry)
                .exchangeProminentButtonStyle()
        }
        .padding(ExchangeSpacing.md)
    }
}

struct ExchangeInfoRow: View {
    let label: String
    let value: String
    var symbol: String? = nil

    var body: some View {
        HStack(alignment: .top, spacing: ExchangeSpacing.sm) {
            if let symbol {
                Image(systemName: symbol)
                    .foregroundStyle(ExchangeColor.labelTertiary)
                    .frame(width: 20)
                    .accessibilityHidden(true)
            }
            Text(label)
                .font(ExchangeTypography.subheadline)
                .foregroundStyle(ExchangeColor.labelSecondary)
            Spacer(minLength: ExchangeSpacing.md)
            Text(value)
                .font(ExchangeTypography.subheadline)
                .foregroundStyle(ExchangeColor.labelPrimary)
                .multilineTextAlignment(.trailing)
        }
        .padding(.vertical, ExchangeSpacing.xs)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(label)：\(value)")
    }
}

struct ExchangeUniversityRow: View {
    let university: PartnerUniversity

    var body: some View {
        HStack(alignment: .top, spacing: ExchangeSpacing.sm) {
            Image(systemName: "building.columns.fill")
                .font(.title3)
                .foregroundStyle(ExchangeColor.accent)
                .frame(width: 30)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: ExchangeSpacing.xxs) {
                Text(university.schoolName)
                    .font(ExchangeTypography.headline)
                    .foregroundStyle(ExchangeColor.labelPrimary)
                Text([university.country, university.programType].compactMap { $0 }.joined(separator: " · "))
                    .font(ExchangeTypography.subheadline)
                    .foregroundStyle(ExchangeColor.labelSecondary)
                if let deadline = university.applicationDeadline, !deadline.isEmpty {
                    Label(deadline, systemImage: "calendar")
                        .font(ExchangeTypography.caption)
                        .foregroundStyle(ExchangeColor.warning)
                        .lineLimit(2)
                }
            }
            Spacer(minLength: ExchangeSpacing.xs)
            Image(systemName: "chevron.right")
                .font(.footnote.weight(.semibold))
                .foregroundStyle(ExchangeColor.labelTertiary)
                .accessibilityHidden(true)
        }
        .padding(.vertical, ExchangeSpacing.xs)
        .contentShape(Rectangle())
        .accessibilityElement(children: .combine)
        .accessibilityHint("開啟申請條件、流程與學生心得")
    }
}

struct ExchangeDeadlineRow: View {
    let title: String
    let detail: String

    var body: some View {
        HStack(alignment: .top, spacing: ExchangeSpacing.sm) {
            Image(systemName: "calendar.badge.clock")
                .font(.title3)
                .foregroundStyle(ExchangeColor.warning)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: ExchangeSpacing.xxs) {
                Text(title)
                    .font(ExchangeTypography.headline)
                    .foregroundStyle(ExchangeColor.labelPrimary)
                Text(detail)
                    .font(ExchangeTypography.subheadline)
                    .foregroundStyle(ExchangeColor.labelSecondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .exchangeCard()
        .accessibilityElement(children: .combine)
    }
}

struct ExchangeDocumentRow: View {
    let title: String
    let summary: String
    let type: String

    var body: some View {
        HStack(alignment: .top, spacing: ExchangeSpacing.sm) {
            Image(systemName: "doc.text.fill")
                .font(.title3)
                .foregroundStyle(ExchangeColor.indigo)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: ExchangeSpacing.xxs) {
                Text(type)
                    .font(ExchangeTypography.caption)
                    .foregroundStyle(ExchangeColor.indigo)
                Text(title)
                    .font(ExchangeTypography.headline)
                    .foregroundStyle(ExchangeColor.labelPrimary)
                Text(summary)
                    .font(ExchangeTypography.subheadline)
                    .foregroundStyle(ExchangeColor.labelSecondary)
                    .lineLimit(3)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .exchangeCard()
        .accessibilityElement(children: .combine)
    }
}

struct ExchangeSourceLink: View {
    let title: String
    let url: String

    var body: some View {
        if let destination = URL(string: url) {
            Link(destination: destination) {
                HStack(spacing: ExchangeSpacing.xs) {
                    Text(title)
                        .font(ExchangeTypography.subheadline)
                    Spacer(minLength: ExchangeSpacing.xs)
                    Image(systemName: "arrow.up.right.square")
                }
                .frame(minHeight: ExchangeLayout.minimumTarget)
                .foregroundStyle(ExchangeColor.accent)
            }
            .accessibilityHint("開啟官方網站")
        }
    }
}

struct ExchangeWorkflowStepView: View {
    let step: ApplicationStep
    let total: Int
    @State private var isExpanded: Bool

    init(step: ApplicationStep, total: Int) {
        self.step = step
        self.total = total
        _isExpanded = State(initialValue: step.order == 1)
    }

    var body: some View {
        DisclosureGroup(isExpanded: $isExpanded) {
            VStack(alignment: .leading, spacing: ExchangeSpacing.md) {
                Text(step.summary)
                    .font(ExchangeTypography.body)
                    .foregroundStyle(ExchangeColor.labelPrimary)
                if step.needsConfirmation {
                    ExchangeInlineBanner(
                        title: "送件前必須確認",
                        message: "此步驟有日期或規定差異，請以官方通知為準。",
                        kind: .warning
                    )
                }
                if !step.details.isEmpty {
                    ExchangeBulletGroup(title: "具體要做", items: step.details)
                }
                if !step.requiredDocuments.isEmpty {
                    ExchangeBulletGroup(title: "這一步要準備", items: step.requiredDocuments, symbol: "doc.badge.checkmark")
                }
                if let actionURL = step.actionUrl {
                    ExchangeSourceLink(title: "開啟這一步的官方頁面", url: actionURL)
                }
            }
            .padding(.top, ExchangeSpacing.sm)
        } label: {
            HStack(alignment: .top, spacing: ExchangeSpacing.sm) {
                Text("\(step.order)")
                    .font(ExchangeTypography.caption)
                    .foregroundStyle(Color(uiColor: UIColor(hex: 0x061018)))
                    .frame(width: 32, height: 32)
                    .background(step.needsConfirmation ? ExchangeColor.warning : ExchangeColor.accent)
                    .clipShape(Circle())
                    .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: ExchangeSpacing.xxs) {
                    Text("\(step.phase) · \(step.responsibleParty)")
                        .font(ExchangeTypography.caption)
                        .foregroundStyle(ExchangeColor.accent)
                    Text(step.title)
                        .font(ExchangeTypography.headline)
                        .foregroundStyle(ExchangeColor.labelPrimary)
                    if let timing = step.timing {
                        Label(timing, systemImage: "calendar.badge.clock")
                            .font(ExchangeTypography.caption)
                            .foregroundStyle(ExchangeColor.labelSecondary)
                    }
                }
            }
        }
        .padding(ExchangeSpacing.md)
        .background(ExchangeColor.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: ExchangeRadius.card, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: ExchangeRadius.card, style: .continuous)
                .stroke(ExchangeColor.separator, lineWidth: 1)
        }
        .accessibilityHint("申請步驟 \(step.order)，共 \(total) 步")
    }
}

struct ExchangeBulletGroup: View {
    let title: String
    let items: [String]
    var symbol: String = "checkmark.circle"

    var body: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.xs) {
            Text(title)
                .font(ExchangeTypography.headline)
                .foregroundStyle(ExchangeColor.labelPrimary)
            ForEach(items, id: \.self) { item in
                Label {
                    Text(item)
                        .font(ExchangeTypography.subheadline)
                        .foregroundStyle(ExchangeColor.labelSecondary)
                } icon: {
                    Image(systemName: symbol)
                        .foregroundStyle(ExchangeColor.accent)
                }
                .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}

struct ExchangeExperienceCard: View {
    let source: StudentExperienceSource

    var body: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
            HStack {
                ExchangeStatusPill(text: source.sourceType.localizedLabel, kind: .info)
                Spacer()
                Text(source.platform)
                    .font(ExchangeTypography.caption)
                    .foregroundStyle(ExchangeColor.labelTertiary)
            }
            Text(source.title)
                .font(ExchangeTypography.headline)
                .foregroundStyle(ExchangeColor.labelPrimary)
            Text(source.summary)
                .font(ExchangeTypography.subheadline)
                .foregroundStyle(ExchangeColor.labelSecondary)
            ExchangeSourceLink(
                title: source.sourceType == "video" ? "觀看原始影片" : "閱讀完整心得",
                url: source.sourceUrl
            )
        }
        .exchangeCard()
    }
}

private extension String {
    var localizedLabel: String {
        switch self {
        case "video": "影片"
        case "community": "社群討論"
        default: "文章"
        }
    }
}
