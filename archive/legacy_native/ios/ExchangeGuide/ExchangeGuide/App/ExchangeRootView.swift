import SwiftUI
import UIKit

enum ExchangeRootTab: String, CaseIterable, Hashable, Identifiable {
    case home, schools, deadlines, support, eligibility

    var id: String { rawValue }

    var title: String {
        switch self {
        case .home: "首頁"
        case .schools: "找學校"
        case .deadlines: "截止日期"
        case .support: "補助與文件"
        case .eligibility: "我的資格"
        }
    }

    var compactTitle: String {
        switch self {
        case .deadlines: "截止日"
        case .support: "補助"
        default: title
        }
    }

    var symbol: String {
        switch self {
        case .home: "house.fill"
        case .schools: "magnifyingglass"
        case .deadlines: "calendar"
        case .support: "doc.text.fill"
        case .eligibility: "person.crop.circle"
        }
    }
}

struct ExchangeRootView: View {
    @EnvironmentObject private var store: DashboardStore
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    @State private var selectedTab: ExchangeRootTab = .home

    private var usesSidebar: Bool {
        UIDevice.current.userInterfaceIdiom == .pad && horizontalSizeClass == .regular
    }

    var body: some View {
        Group {
            if usesSidebar {
                regularLayout
            } else {
                compactLayout
            }
        }
    }

    private var compactLayout: some View {
        TabView(selection: $selectedTab) {
            ForEach(ExchangeRootTab.allCases) { tab in
                NavigationStack {
                    destination(for: tab)
                }
                .tabItem { Label(tab.compactTitle, systemImage: tab.symbol) }
                .tag(tab)
            }
        }
        .toolbar(.hidden, for: .tabBar)
        .safeAreaInset(edge: .bottom, spacing: 0) {
            ExchangeLiquidTabBar(
                selection: $selectedTab,
                documentCount: store.dashboard?.documentExplanations.count ?? 0
            )
        }
    }

    private var regularLayout: some View {
        NavigationSplitView {
            List {
                Section {
                    sidebarIdentity
                        .listRowInsets(EdgeInsets(top: 8, leading: 12, bottom: 12, trailing: 12))
                        .listRowBackground(Color.clear)
                }

                Section("學生任務") {
                    ForEach(ExchangeRootTab.allCases) { tab in
                        Button {
                            selectedTab = tab
                        } label: {
                            HStack(spacing: ExchangeSpacing.sm) {
                                Image(systemName: tab.symbol)
                                    .frame(width: 24)
                                    .foregroundStyle(selectedTab == tab ? ExchangeColor.accent : ExchangeColor.labelSecondary)
                                    .accessibilityHidden(true)
                                Text(tab.title)
                                    .font(ExchangeTypography.headline)
                                    .foregroundStyle(ExchangeColor.labelPrimary)
                                Spacer(minLength: ExchangeSpacing.xs)
                            }
                            .padding(.horizontal, ExchangeSpacing.sm)
                            .frame(maxWidth: .infinity, minHeight: 52, alignment: .leading)
                            .contentShape(Rectangle())
                            .background(
                                selectedTab == tab ? ExchangeColor.backgroundSelected : Color.clear,
                                in: RoundedRectangle(cornerRadius: ExchangeRadius.card, style: .continuous)
                            )
                        }
                        .buttonStyle(.plain)
                        .accessibilityValue(selectedTab == tab ? "已選取" : "未選取")
                    }
                }

                Section("資料狀態") {
                    sidebarStatus
                }
            }
            .listStyle(.sidebar)
            .navigationTitle("交換指南")
            .navigationSplitViewColumnWidth(min: 240, ideal: 280, max: 340)
        } detail: {
            NavigationStack {
                destination(for: selectedTab)
            }
        }
        .navigationSplitViewStyle(.balanced)
    }

    private var sidebarIdentity: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
            Image("cgu-campus")
                .resizable()
                .scaledToFill()
                .frame(height: 112)
                .clipped()
                .clipShape(RoundedRectangle(cornerRadius: ExchangeRadius.card, style: .continuous))
                .accessibilityLabel("長庚大學校園與 CGU 地標")

            VStack(alignment: .leading, spacing: ExchangeSpacing.xxs) {
                Text("長庚大學")
                    .font(ExchangeTypography.title3)
                    .foregroundStyle(ExchangeColor.labelPrimary)
                Text("交換申請資訊中心")
                    .font(ExchangeTypography.subheadline)
                    .foregroundStyle(ExchangeColor.labelSecondary)
            }
        }
        .accessibilityElement(children: .combine)
    }

    @ViewBuilder
    private var sidebarStatus: some View {
        if let dashboard = store.dashboard {
            VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
                LabeledContent("合作學校", value: "\(dashboard.partnerUniversities.count) 所")
                LabeledContent("文件摘要", value: "\(dashboard.documentExplanations.count) 份")
                if let checked = dashboard.lastChecked {
                    Label(checked, systemImage: "checkmark.circle.fill")
                        .font(ExchangeTypography.caption)
                        .foregroundStyle(ExchangeColor.success)
                        .lineLimit(2)
                }
            }
            .font(ExchangeTypography.subheadline)
            .accessibilityElement(children: .combine)
        } else if store.isLoading {
            HStack(spacing: ExchangeSpacing.xs) {
                ProgressView()
                Text("整理公開資料")
            }
            .frame(minHeight: ExchangeLayout.minimumTarget)
        } else {
            Label("資料暫時無法載入", systemImage: "exclamationmark.triangle")
                .font(ExchangeTypography.subheadline)
                .foregroundStyle(ExchangeColor.warning)
        }
    }

    @ViewBuilder
    private func destination(for tab: ExchangeRootTab) -> some View {
        switch tab {
        case .home:
            ExchangeHomeView(selectedTab: $selectedTab)
        case .schools:
            ExchangeSchoolsView()
        case .deadlines:
            ExchangeDeadlinesView()
        case .support:
            ExchangeSupportView()
        case .eligibility:
            ExchangeEligibilityView()
        }
    }
}

private struct ExchangeLiquidTabBar: View {
    @Binding var selection: ExchangeRootTab
    let documentCount: Int

    private let visualOrder: [ExchangeRootTab] = [
        .home,
        .deadlines,
        .schools,
        .support,
        .eligibility
    ]

    var body: some View {
        HStack(spacing: 6) {
            ForEach(visualOrder) { tab in
                ExchangeLiquidTabButton(
                    tab: tab,
                    isSelected: selection == tab,
                    badgeCount: tab == .support ? documentCount : 0
                ) {
                    selection = tab
                }
            }
        }
        .padding(.horizontal, 10)
        .padding(.top, 8)
        .padding(.bottom, 6)
        .frame(maxWidth: .infinity)
    }
}

private struct ExchangeLiquidTabButton: View {
    let tab: ExchangeRootTab
    let isSelected: Bool
    let badgeCount: Int
    let action: () -> Void

    private var isSearch: Bool { tab == .schools }

    var body: some View {
        Button(action: action) {
            Group {
                if isSearch {
                    HStack(spacing: 9) {
                        Image(systemName: tab.symbol)
                            .font(.system(size: 20, weight: .semibold))
                            .foregroundStyle(isSelected ? ExchangeColor.labelPrimary : ExchangeColor.labelSecondary.opacity(0.74))
                        Text("搜尋")
                            .font(.headline.weight(.semibold))
                            .foregroundStyle(isSelected ? ExchangeColor.labelPrimary : ExchangeColor.labelPrimary.opacity(0.70))
                            .lineLimit(1)
                    }
                } else {
                    Image(systemName: tab.symbol)
                        .font(.system(size: 22, weight: .semibold))
                        .foregroundStyle(isSelected ? ExchangeColor.labelPrimary : ExchangeColor.labelSecondary.opacity(0.74))
                }
            }
            .frame(width: isSearch ? 110 : 54, height: 54)
            .modifier(ExchangeLiquidTabSurface(isSearch: isSearch, isSelected: isSelected))
            .overlay(alignment: .topTrailing) {
                if badgeCount > 0 {
                    Text("1")
                        .font(.caption2.weight(.bold))
                        .foregroundStyle(.white)
                        .padding(.horizontal, 6)
                        .frame(minWidth: 22, minHeight: 22)
                        .background(ExchangeColor.success, in: Capsule())
                        .offset(x: 3, y: -4)
                        .accessibilityHidden(true)
                }
            }
        }
        .buttonStyle(.plain)
        .accessibilityLabel(tab.title)
        .accessibilityValue(isSelected ? "已選取" : "未選取")
    }
}

private struct ExchangeLiquidTabSurface: ViewModifier {
    let isSearch: Bool
    let isSelected: Bool

    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency

    @ViewBuilder
    func body(content: Content) -> some View {
        if reduceTransparency {
            fallback(content: content, opaque: true)
        } else if #available(iOS 26.0, *) {
            if isSearch {
                content.glassEffect(
                    .regular.interactive(true),
                    in: .capsule
                )
            } else {
                content.glassEffect(
                    .regular.interactive(true),
                    in: .circle
                )
            }
        } else {
            fallback(content: content, opaque: false)
        }
    }

    @ViewBuilder
    private func fallback(content: Content, opaque: Bool) -> some View {
        if isSearch {
            content
                .background(opaque ? AnyShapeStyle(ExchangeColor.backgroundSecondary) : AnyShapeStyle(.ultraThinMaterial), in: Capsule())
                .overlay(Capsule().stroke(ExchangeColor.separator.opacity(0.7), lineWidth: 1))
                .shadow(color: .black.opacity(0.10), radius: isSelected ? 12 : 9, y: 5)
        } else {
            content
                .background(opaque ? AnyShapeStyle(ExchangeColor.backgroundSecondary) : AnyShapeStyle(.ultraThinMaterial), in: Circle())
                .overlay(Circle().stroke(ExchangeColor.separator.opacity(0.7), lineWidth: 1))
                .shadow(color: .black.opacity(0.10), radius: isSelected ? 12 : 9, y: 5)
        }
    }
}
