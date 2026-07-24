import SwiftUI

struct ExchangeHomeView: View {
    @EnvironmentObject private var store: DashboardStore
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    @Binding var selectedTab: ExchangeRootTab

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
        .navigationTitle("總覽")
        .navigationBarTitleDisplayMode(.large)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    selectedTab = .eligibility
                } label: {
                    Image(systemName: "person.crop.circle.fill")
                        .font(.title2)
                        .foregroundStyle(ExchangeColor.accent)
                        .frame(minWidth: ExchangeLayout.minimumTarget, minHeight: ExchangeLayout.minimumTarget)
                }
                .accessibilityLabel("查看我的資格")
            }
        }
        .exchangePageBackground()
    }

    private func content(_ dashboard: StudentDashboard) -> some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: ExchangeSpacing.xl) {
                greetingHeader
                campusIdentity(dashboard)
                adaptiveTaskAndChartLayout(dashboard)
                latestInformation(dashboard)
            }
            .frame(maxWidth: 1080, alignment: .leading)
            .padding(.horizontal, horizontalSizeClass == .regular ? ExchangeLayout.regularMargin : ExchangeLayout.compactMargin)
            .padding(.bottom, ExchangeSpacing.section)
        }
        .refreshable { await store.load(force: true) }
    }

    private var greetingHeader: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.xxs) {
            Text("你好，準備交換的同學")
                .font(ExchangeTypography.title3)
                .foregroundStyle(ExchangeColor.labelPrimary)
            Text("先完成今天最重要的一件事")
                .font(ExchangeTypography.subheadline)
                .foregroundStyle(ExchangeColor.labelSecondary)
        }
    }

    @ViewBuilder
    private func adaptiveTaskAndChartLayout(_ dashboard: StudentDashboard) -> some View {
        if horizontalSizeClass == .regular {
            HStack(alignment: .top, spacing: ExchangeSpacing.md) {
                taskPanel
                    .frame(maxWidth: .infinity, alignment: .top)
                ExchangeCoverageChart(dashboard: dashboard)
                    .frame(maxWidth: .infinity, alignment: .top)
            }
        } else {
            taskPanel
            ExchangeCoverageChart(dashboard: dashboard)
        }
    }

    private var taskPanel: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
            ExchangeSectionHeader(title: "今天想先做什麼？")
                .padding(.bottom, ExchangeSpacing.xxs)

            ExchangeTaskButton(
                title: "找可申請學校",
                detail: "依國家、學院與學制篩選",
                symbol: "building.columns.fill",
                tint: ExchangeColor.accent
            ) { selectedTab = .schools }
            ExchangeTaskButton(
                title: "掌握截止日期",
                detail: "比較校內與合作校時程",
                symbol: "calendar.badge.clock",
                tint: ExchangeColor.warning
            ) { selectedTab = .deadlines }
            ExchangeTaskButton(
                title: "查看補助",
                detail: "先讀重點，再開官方規章",
                symbol: "banknote.fill",
                tint: ExchangeColor.success
            ) { selectedTab = .support }
            ExchangeTaskButton(
                title: "資格初步檢查",
                detail: "確認成績、語言與可看學校",
                symbol: "person.text.rectangle",
                tint: ExchangeColor.indigo
            ) { selectedTab = .eligibility }
        }
    }

    @ViewBuilder
    private func latestInformation(_ dashboard: StudentDashboard) -> some View {
        if horizontalSizeClass == .regular {
            HStack(alignment: .top, spacing: ExchangeSpacing.md) {
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

    @ViewBuilder
    private func recentDeadline(_ dashboard: StudentDashboard) -> some View {
        if let period = dashboard.applicationPeriods.first {
            VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
                ExchangeSectionHeader(title: "最近申請時程")
                ExchangeDeadlineRow(
                    title: period.title,
                    detail: period.details.first ?? "請開啟官方來源確認日期"
                )
            }
        }
    }

    @ViewBuilder
    private func featuredUniversity(_ dashboard: StudentDashboard) -> some View {
        if let university = dashboard.partnerUniversities.first {
            VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
                ExchangeSectionHeader(title: "先從這所學校開始")
                NavigationLink {
                    ExchangeSchoolDetailView(university: university)
                } label: {
                    ExchangeUniversityRow(university: university)
                        .exchangeCard()
                }
                .buttonStyle(.plain)
            }
        }
    }

    private func campusIdentity(_ dashboard: StudentDashboard) -> some View {
        let height: CGFloat = horizontalSizeClass == .regular ? 240 : 190

        return ZStack(alignment: .bottomLeading) {
            Image("cgu-campus")
                .resizable()
                .scaledToFill()
                .frame(height: height)
                .clipped()
                .exchangeBackgroundExtension()
                .accessibilityLabel("長庚大學校園與 CGU 地標")
            LinearGradient(
                colors: [.clear, .black.opacity(0.55)],
                startPoint: .center,
                endPoint: .bottom
            )
            VStack(alignment: .leading, spacing: ExchangeSpacing.xxs) {
                Text(dashboard.schoolName)
                    .font(ExchangeTypography.title2)
                    .foregroundStyle(.white)
                Text("桃園 · 台灣")
                    .font(ExchangeTypography.subheadline)
                    .foregroundStyle(.white.opacity(0.82))
            }
            .padding(ExchangeSpacing.md)
        }
        .frame(height: height)
        .clipShape(RoundedRectangle(cornerRadius: ExchangeRadius.card, style: .continuous))
    }
}
