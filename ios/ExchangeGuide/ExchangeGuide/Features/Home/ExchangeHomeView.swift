import SwiftUI

struct ExchangeHomeView: View {
    @EnvironmentObject private var store: DashboardStore
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    @Binding var selectedTab: ExchangeRootTab
    @State private var deadlineExpanded = false

    var body: some View {
        Group {
            if let dashboard = store.dashboard {
                content(dashboard)
            } else if let error = store.errorMessage {
                ExchangeErrorState(message: error) {
                    Task { await store.load(force: true) }
                }
            } else {
                ExchangeLoadingState(message: "正在整理交換資訊")
            }
        }
        .navigationTitle("交換指南")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    Task { await store.load(force: true) }
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .frame(minWidth: ExchangeLayout.minimumTarget, minHeight: ExchangeLayout.minimumTarget)
                }
                .accessibilityLabel("重新整理")
            }
        }
        .exchangePageBackground()
    }

    private func content(_ dashboard: StudentDashboard) -> some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: ExchangeSpacing.xl) {
                campusIdentity(dashboard)
                taskPanel
                focusPanel(dashboard)
                ExchangeCoverageChart(dashboard: dashboard)
            }
            .frame(maxWidth: 1080, alignment: .leading)
            .padding(.horizontal, horizontalSizeClass == .regular ? ExchangeLayout.regularMargin : ExchangeLayout.compactMargin)
            .padding(.top, ExchangeSpacing.sm)
            .padding(.bottom, ExchangeSpacing.section)
        }
        .refreshable { await store.load(force: true) }
    }

    private var taskPanel: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
            ExchangeSectionHeader(
                title: "開始",
                detail: "選一個圖示，詳細內容會在下一頁展開"
            )

            LazyVGrid(columns: actionColumns, spacing: ExchangeSpacing.sm) {
                ExchangeTaskButton(
                    title: "找學校",
                    detail: "依國家、學院與學制篩選",
                    symbol: "building.columns.fill",
                    tint: ExchangeColor.accent
                ) { selectedTab = .schools }
                ExchangeTaskButton(
                    title: "截止日",
                    detail: "比較校內與合作校時程",
                    symbol: "calendar",
                    tint: ExchangeColor.warning
                ) { selectedTab = .deadlines }
                ExchangeTaskButton(
                    title: "補助文件",
                    detail: "閱讀摘要與官方規章",
                    symbol: "doc.text.fill",
                    tint: ExchangeColor.success
                ) { selectedTab = .support }
                ExchangeTaskButton(
                    title: "我的資格",
                    detail: "確認成績、語言與可看學校",
                    symbol: "person.crop.circle.badge.checkmark",
                    tint: ExchangeColor.indigo
                ) { selectedTab = .eligibility }
            }
        }
    }

    private var actionColumns: [GridItem] {
        let count = horizontalSizeClass == .regular ? 4 : 2
        return Array(
            repeating: GridItem(.flexible(), spacing: ExchangeSpacing.sm),
            count: count
        )
    }

    @ViewBuilder
    private func focusPanel(_ dashboard: StudentDashboard) -> some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
            ExchangeSectionHeader(title: "焦點")

            if horizontalSizeClass == .regular {
                HStack(alignment: .top, spacing: ExchangeSpacing.sm) {
                    recentDeadline(dashboard)
                        .frame(maxWidth: .infinity, alignment: .top)
                    featuredUniversity(dashboard)
                        .frame(maxWidth: .infinity, alignment: .top)
                }
            } else {
                recentDeadline(dashboard)
                featuredUniversity(dashboard)
            }
        }
    }

    @ViewBuilder
    private func recentDeadline(_ dashboard: StudentDashboard) -> some View {
        if let period = dashboard.applicationPeriods.first {
            DisclosureGroup(isExpanded: $deadlineExpanded) {
                Text(period.details.first ?? "請開啟官方來源確認日期")
                    .font(ExchangeTypography.subheadline)
                    .foregroundStyle(ExchangeColor.labelSecondary)
                    .padding(.top, ExchangeSpacing.sm)
                    .fixedSize(horizontal: false, vertical: true)
            } label: {
                focusLabel(
                    title: "最近截止",
                    summary: period.title,
                    symbol: "calendar",
                    tint: ExchangeColor.warning
                )
            }
            .tint(ExchangeColor.labelSecondary)
            .exchangeCard()
        }
    }

    @ViewBuilder
    private func featuredUniversity(_ dashboard: StudentDashboard) -> some View {
        if let university = dashboard.partnerUniversities.first {
            NavigationLink {
                ExchangeSchoolDetailView(university: university)
            } label: {
                HStack(spacing: ExchangeSpacing.sm) {
                    focusLabel(
                        title: "推薦學校",
                        summary: university.schoolName,
                        symbol: "building.columns.fill",
                        tint: ExchangeColor.accent
                    )
                    Image(systemName: "chevron.right")
                        .font(.footnote.weight(.semibold))
                        .foregroundStyle(ExchangeColor.labelTertiary)
                }
                .exchangeCard()
            }
            .buttonStyle(.plain)
            .accessibilityHint("開啟學校詳細資訊")
        }
    }

    private func focusLabel(
        title: String,
        summary: String,
        symbol: String,
        tint: Color
    ) -> some View {
        HStack(spacing: ExchangeSpacing.sm) {
            Image(systemName: symbol)
                .font(.body.weight(.semibold))
                .foregroundStyle(tint)
                .frame(width: 40, height: 40)
                .background(tint.opacity(0.13), in: Circle())
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(ExchangeTypography.caption)
                    .foregroundStyle(ExchangeColor.labelSecondary)
                Text(summary)
                    .font(ExchangeTypography.headline)
                    .foregroundStyle(ExchangeColor.labelPrimary)
                    .lineLimit(1)
            }
            Spacer(minLength: ExchangeSpacing.xs)
        }
        .accessibilityElement(children: .combine)
    }

    private func campusIdentity(_ dashboard: StudentDashboard) -> some View {
        let height: CGFloat = horizontalSizeClass == .regular ? 190 : 150

        return ZStack(alignment: .bottomLeading) {
            Image("cgu-campus")
                .resizable()
                .scaledToFill()
                .frame(height: height)
                .clipped()
                .exchangeBackgroundExtension()
                .accessibilityLabel("長庚大學校園與 CGU 地標")
            LinearGradient(
                colors: [.clear, .black.opacity(0.68)],
                startPoint: .top,
                endPoint: .bottom
            )
            HStack(alignment: .bottom, spacing: ExchangeSpacing.sm) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(dashboard.schoolName)
                        .font(ExchangeTypography.title2)
                        .foregroundStyle(.white)
                    Text("交換探索")
                        .font(ExchangeTypography.subheadline)
                        .foregroundStyle(.white.opacity(0.82))
                }
                Spacer(minLength: ExchangeSpacing.sm)
                Text("\(dashboard.partnerUniversities.count)")
                    .font(ExchangeTypography.headline)
                    .foregroundStyle(.white)
                    .padding(.horizontal, 13)
                    .padding(.vertical, 8)
                    .background(.white.opacity(0.20), in: Capsule())
            }
            .padding(ExchangeSpacing.md)
        }
        .frame(height: height)
        .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
    }
}
