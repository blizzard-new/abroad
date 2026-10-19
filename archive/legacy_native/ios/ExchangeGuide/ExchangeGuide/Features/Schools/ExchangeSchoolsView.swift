import SwiftUI

struct ExchangeSchoolsView: View {
    @EnvironmentObject private var store: DashboardStore
    @State private var query = ""
    @State private var selectedCountry = "全部"

    private var countries: [String] {
        let values = store.dashboard?.partnerUniversities.compactMap(\.country) ?? []
        return ["全部"] + Array(Set(values)).sorted()
    }

    private var filteredUniversities: [PartnerUniversity] {
        guard let universities = store.dashboard?.partnerUniversities else { return [] }
        let normalizedQuery = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        return universities.filter { university in
            let countryMatches = selectedCountry == "全部" || university.country == selectedCountry
            let content = [
                university.schoolName,
                university.country,
                university.colleges,
                university.degreeLevels,
                university.eligibility
            ].compactMap { $0 }.joined(separator: " ").lowercased()
            return countryMatches && (normalizedQuery.isEmpty || content.contains(normalizedQuery))
        }
    }

    var body: some View {
        Group {
            if store.dashboard != nil {
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: ExchangeSpacing.md) {
                        ExchangeSectionHeader(
                            eyebrow: "第一優先",
                            title: "找可申請學校",
                            detail: "先縮小選擇，再查看每所學校的限制與完整流程。"
                        )
                        ExchangeSearchField(prompt: "搜尋學校、國家或語言門檻", text: $query)

                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: ExchangeSpacing.xs) {
                                ForEach(countries, id: \.self) { country in
                                    ExchangeFilterChip(
                                        title: country,
                                        isSelected: selectedCountry == country
                                    ) { selectedCountry = country }
                                }
                            }
                        }
                        .accessibilityLabel("國家篩選")

                        Text("\(filteredUniversities.count) 所學校")
                            .font(ExchangeTypography.caption)
                            .foregroundStyle(ExchangeColor.labelSecondary)

                        if filteredUniversities.isEmpty {
                            ExchangeEmptyState(
                                title: "找不到符合的學校",
                                message: "調整關鍵字或國家後再試一次。",
                                symbol: "magnifyingglass"
                            )
                        } else {
                            ForEach(filteredUniversities) { university in
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
                    .padding(ExchangeLayout.compactMargin)
                    .padding(.bottom, ExchangeSpacing.section)
                }
            } else if let error = store.errorMessage {
                ExchangeErrorState(message: error) {
                    Task { await store.load(force: true) }
                }
            } else {
                ExchangeLoadingState(message: "正在載入合作學校")
            }
        }
        .navigationTitle("找學校")
        .navigationBarTitleDisplayMode(.inline)
        .exchangePageBackground()
    }
}
