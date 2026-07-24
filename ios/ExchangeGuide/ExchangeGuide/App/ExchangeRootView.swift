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
        case .schools: "building.columns.fill"
        case .deadlines: "calendar.badge.clock"
        case .support: "banknote.fill"
        case .eligibility: "person.crop.circle.badge.checkmark"
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
