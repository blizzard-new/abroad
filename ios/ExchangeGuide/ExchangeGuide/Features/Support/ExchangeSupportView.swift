import SwiftUI

private enum SupportSegment: String, CaseIterable, Identifiable {
    case scholarships = "補助重點"
    case documents = "申請文件"

    var id: String { rawValue }
}

struct ExchangeSupportView: View {
    @EnvironmentObject private var store: DashboardStore
    @State private var segment: SupportSegment = .scholarships
    @State private var query = ""

    private var allDocuments: [RuleExplanation] {
        store.dashboard?.documentExplanations ?? []
    }

    private var visibleDocuments: [RuleExplanation] {
        let scholarshipKeywords = ["補助", "獎學金", "學海", "領航者"]
        let normalized = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        return allDocuments.filter { document in
            let haystack = "\(document.title) \(document.documentType) \(document.summary)".lowercased()
            let segmentMatches: Bool
            switch segment {
            case .scholarships:
                segmentMatches = scholarshipKeywords.contains { haystack.contains($0) }
            case .documents:
                segmentMatches = !scholarshipKeywords.contains { haystack.contains($0) }
            }
            return segmentMatches && (normalized.isEmpty || haystack.contains(normalized))
        }
    }

    var body: some View {
        Group {
            if store.dashboard != nil {
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: ExchangeSpacing.lg) {
                        ExchangeSectionHeader(
                            eyebrow: "第三優先",
                            title: "補助與申請文件",
                            detail: "先看學生版摘要與粗體重點，需要逐字核對時再開官方完整文件。"
                        )

                        Picker("資料類型", selection: $segment) {
                            ForEach(SupportSegment.allCases) { option in
                                Text(option.rawValue).tag(option)
                            }
                        }
                        .pickerStyle(.segmented)
                        .frame(minHeight: ExchangeLayout.minimumTarget)

                        ExchangeSearchField(prompt: "搜尋補助或文件名稱", text: $query)

                        ExchangeInlineBanner(
                            title: "摘要不取代官方規章",
                            message: "金額、資格、期限與表單版本可能更新；每份整理都保留來源與完整文件。",
                            kind: .info
                        )

                        Text("\(visibleDocuments.count) 份整理")
                            .font(ExchangeTypography.caption)
                            .foregroundStyle(ExchangeColor.labelSecondary)

                        if visibleDocuments.isEmpty {
                            ExchangeEmptyState(
                                title: "沒有符合的整理",
                                message: "切換分類或調整搜尋關鍵字。",
                                symbol: "doc.text.magnifyingglass"
                            )
                        } else {
                            ForEach(visibleDocuments) { document in
                                documentCard(document)
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
                ExchangeLoadingState(message: "正在整理補助與文件")
            }
        }
        .navigationTitle("補助與文件")
        .navigationBarTitleDisplayMode(.inline)
        .exchangePageBackground()
    }

    private func documentCard(_ document: RuleExplanation) -> some View {
        DisclosureGroup {
            VStack(alignment: .leading, spacing: ExchangeSpacing.md) {
                Text(document.summary)
                    .font(ExchangeTypography.body.weight(.semibold))
                    .foregroundStyle(ExchangeColor.labelPrimary)
                    .fixedSize(horizontal: false, vertical: true)

                if !document.appliesTo.isEmpty {
                    ExchangeBulletGroup(title: "適用對象", items: document.appliesTo, symbol: "person.2")
                }
                if !document.keyPoints.isEmpty {
                    ExchangeBulletGroup(title: "學生最需要知道", items: document.keyPoints, symbol: "highlighter")
                }

                if let documentURL = document.documentUrl {
                    ExchangeSourceLink(title: "開啟官方完整文件", url: documentURL)
                }
                ExchangeSourceLink(title: "查看官方來源頁", url: document.source.sourceUrl)
            }
            .padding(.top, ExchangeSpacing.sm)
        } label: {
            ExchangeDocumentRow(
                title: document.title,
                summary: document.summary,
                type: document.documentType
            )
        }
        .tint(ExchangeColor.accent)
        .accessibilityHint("展開學生版重點與官方來源")
    }
}
