import SwiftUI

struct ExchangeDeadlinesView: View {
    @EnvironmentObject private var store: DashboardStore
    @State private var query = ""

    private var partnerDeadlines: [PartnerUniversity] {
        guard let universities = store.dashboard?.partnerUniversities else { return [] }
        let normalized = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        return universities
            .filter { university in
                guard let deadline = university.applicationDeadline, !deadline.isEmpty else { return false }
                if normalized.isEmpty { return true }
                return "\(university.schoolName) \(university.country ?? "") \(deadline)"
                    .lowercased()
                    .contains(normalized)
            }
            .sorted { $0.schoolName.localizedStandardCompare($1.schoolName) == .orderedAscending }
    }

    var body: some View {
        Group {
            if let dashboard = store.dashboard {
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: ExchangeSpacing.xl) {
                        ExchangeSectionHeader(
                            eyebrow: "第二優先",
                            title: "掌握截止日期",
                            detail: "先看長庚校內甄選，再確認合作校的提名與送件期限。"
                        )

                        ExchangeInlineBanner(
                            title: "日期可能隨梯次調整",
                            message: "所有日期都附官方來源；送件前仍須核對當期公告。",
                            kind: .warning
                        )

                        VStack(alignment: .leading, spacing: ExchangeSpacing.md) {
                            ExchangeSectionHeader(title: "長庚校內時程", detail: "校內甄選通常早於合作校申請")
                            if dashboard.applicationPeriods.isEmpty {
                                ExchangeEmptyState(
                                    title: "尚無時程",
                                    message: "請稍後重新整理或查看國際處公告。",
                                    symbol: "calendar.badge.exclamationmark"
                                )
                            } else {
                                ForEach(dashboard.applicationPeriods) { period in
                                    VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
                                        ExchangeDeadlineRow(
                                            title: period.title,
                                            detail: period.details.first ?? "請開啟官方來源確認日期"
                                        )
                                        if period.details.count > 1 {
                                            ExchangeBulletGroup(title: "時程重點", items: Array(period.details.dropFirst()))
                                        }
                                        if let source = period.source {
                                            ExchangeSourceLink(title: "查看當期官方公告", url: source.sourceUrl)
                                        }
                                    }
                                }
                            }
                        }

                        VStack(alignment: .leading, spacing: ExchangeSpacing.md) {
                            ExchangeSectionHeader(
                                title: "合作校截止日",
                                detail: "搜尋學校或國家，點入可看限制、流程與學生心得"
                            )
                            ExchangeSearchField(prompt: "搜尋學校、國家或日期", text: $query)
                            Text("\(partnerDeadlines.count) 所有日期資料的學校")
                                .font(ExchangeTypography.caption)
                                .foregroundStyle(ExchangeColor.labelSecondary)

                            if partnerDeadlines.isEmpty {
                                ExchangeEmptyState(
                                    title: "找不到截止日",
                                    message: "調整搜尋內容，或到找學校頁查看完整清單。",
                                    symbol: "calendar"
                                )
                            } else {
                                ForEach(partnerDeadlines) { university in
                                    NavigationLink {
                                        ExchangeSchoolDetailView(university: university)
                                    } label: {
                                        ExchangeUniversityRow(university: university)
                                            .padding(ExchangeSpacing.md)
                                            .background(ExchangeColor.backgroundSecondary)
                                            .clipShape(RoundedRectangle(cornerRadius: ExchangeRadius.card, style: .continuous))
                                            .overlay {
                                                RoundedRectangle(cornerRadius: ExchangeRadius.card, style: .continuous)
                                                    .stroke(ExchangeColor.separator, lineWidth: 1)
                                            }
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                        }
                    }
                    .padding(ExchangeLayout.compactMargin)
                    .padding(.bottom, ExchangeSpacing.section)
                }
                .refreshable { await store.load(force: true) }
            } else if let error = store.errorMessage {
                ExchangeErrorState(message: error) {
                    Task { await store.load(force: true) }
                }
            } else {
                ExchangeLoadingState(message: "正在整理截止日期")
            }
        }
        .navigationTitle("截止日期")
        .navigationBarTitleDisplayMode(.inline)
        .exchangePageBackground()
    }
}
