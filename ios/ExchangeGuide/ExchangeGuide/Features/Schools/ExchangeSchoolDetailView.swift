import SwiftUI

struct ExchangeSchoolDetailView: View {
    let university: PartnerUniversity

    @State private var workflow: UniversityApplicationWorkflow?
    @State private var experiences: StudentExperienceDigest?
    @State private var isLoading = true
    @State private var errorMessage: String?

    private let api = ExchangeAPIClient.shared

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: ExchangeSpacing.xl) {
                overview

                if isLoading {
                    ExchangeLoadingState(message: "正在整理官方流程與學生心得")
                }

                if let errorMessage {
                    ExchangeInlineBanner(title: "部分資料無法載入", message: errorMessage, kind: .warning)
                }

                if let workflow {
                    workflowSection(workflow)
                }

                if let experiences {
                    lifeSection(experiences)
                    experienceSection(experiences)
                }

                ExchangeCommunityView(schoolName: university.schoolName)
            }
            .padding(ExchangeLayout.compactMargin)
            .padding(.bottom, ExchangeSpacing.section)
        }
        .navigationTitle(university.schoolName)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            if let website = university.website, let url = URL(string: website) {
                ToolbarItem(placement: .topBarTrailing) {
                    Link(destination: url) {
                        Image(systemName: "safari")
                    }
                    .accessibilityLabel("開啟學校官方網站")
                }
            }
        }
        .refreshable { await loadDetails(force: true) }
        .task { await loadDetails() }
        .exchangePageBackground()
    }

    private var overview: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.lg) {
            ExchangeSectionHeader(
                eyebrow: [university.country, university.programType].compactMap { $0 }.joined(separator: " · "),
                title: university.schoolName,
                detail: "先確認限制，再依步驟完成長庚校內與合作校申請。"
            )

            VStack(spacing: 0) {
                ExchangeInfoRow(label: "適用身分", value: [university.colleges, university.degreeLevels].compactMap { $0 }.joined(separator: "／").nilIfEmpty ?? "依公告")
                Divider().overlay(ExchangeColor.separator)
                ExchangeInfoRow(label: "名額", value: university.quota ?? "依公告")
                Divider().overlay(ExchangeColor.separator)
                ExchangeInfoRow(label: "研修期間", value: university.studyPeriod ?? "依公告")
                Divider().overlay(ExchangeColor.separator)
                ExchangeInfoRow(label: "合作校截止日", value: university.applicationDeadline ?? "依公告", symbol: "calendar")
                Divider().overlay(ExchangeColor.separator)
                ExchangeInfoRow(label: "學費", value: university.tuitionInfo ?? "依公告")
            }
            .exchangeCard()

            if let eligibility = university.eligibility, !eligibility.isEmpty {
                DisclosureGroup {
                    Text(eligibility)
                        .font(ExchangeTypography.body)
                        .foregroundStyle(ExchangeColor.labelSecondary)
                        .padding(.top, ExchangeSpacing.sm)
                } label: {
                    Label("申請限制與語言條件", systemImage: "checklist")
                        .font(ExchangeTypography.headline)
                        .foregroundStyle(ExchangeColor.labelPrimary)
                }
                .exchangeCard()
            }
        }
    }

    private func workflowSection(_ workflow: UniversityApplicationWorkflow) -> some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.md) {
            ExchangeSectionHeader(
                eyebrow: "從校內甄選到返國結案",
                title: "詳細申請流程",
                detail: workflow.coverageNote
            )
            ExchangeInlineBanner(
                title: workflow.coverageStatus == "official_verified" ? "官方來源已查核" : "部分細節需確認",
                message: workflow.disclaimer,
                kind: workflow.coverageStatus == "official_verified" ? .success : .warning
            )
            ForEach(workflow.steps) { step in
                ExchangeWorkflowStepView(step: step, total: workflow.steps.count)
            }
            DisclosureGroup("本流程使用的官方來源") {
                VStack(alignment: .leading, spacing: ExchangeSpacing.xs) {
                    ForEach(workflow.sources) { source in
                        ExchangeSourceLink(title: source.title, url: source.sourceUrl)
                    }
                }
                .padding(.top, ExchangeSpacing.xs)
            }
            .font(ExchangeTypography.headline)
            .exchangeCard()
        }
    }

    private func experienceSection(_ digest: StudentExperienceDigest) -> some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.md) {
            ExchangeSectionHeader(
                eyebrow: "公開文章與影片",
                title: "其他學生去過的心得",
                detail: digest.coverageNote
            )

            HStack(spacing: ExchangeSpacing.xs) {
                ExchangeStatusPill(text: "\(digest.articleCount) 篇文章", kind: .info)
                ExchangeStatusPill(text: "\(digest.videoCount) 部影片", kind: .success)
            }

            if digest.sources.isEmpty {
                ExchangeEmptyState(
                    title: "目前沒有足夠心得",
                    message: digest.disclaimer,
                    symbol: "text.bubble"
                )
            } else {
                ForEach(digest.sources.prefix(8)) { source in
                    ExchangeExperienceCard(source: source)
                }
            }
        }
    }

    private func lifeSection(_ digest: StudentExperienceDigest) -> some View {
        let sorted = digest.highlights.sorted {
            if $0.sourceCount == $1.sourceCount { return $0.title < $1.title }
            return $0.sourceCount > $1.sourceCount
        }
        return VStack(alignment: .leading, spacing: ExchangeSpacing.md) {
            ExchangeSectionHeader(
                eyebrow: "有資料的面向優先",
                title: "生活情報重點",
                detail: "只列出文章或影片中可具體整理的內容；完整版本保留原始連結。"
            )
            ForEach(sorted) { highlight in
                DisclosureGroup {
                    VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
                        if highlight.keyPoints.isEmpty {
                            ExchangeInlineBanner(
                                title: "已有來源，具體內容待補充",
                                message: "摘要尚未擷取到足以驗證的細節，因此不以分類句充當重點。",
                                kind: .warning
                            )
                        } else {
                            ForEach(highlight.keyPoints, id: \.self) { point in
                                Label(point, systemImage: "checkmark.circle.fill")
                                    .font(ExchangeTypography.body)
                                    .foregroundStyle(ExchangeColor.labelPrimary)
                            }
                        }
                        ForEach(Array(highlight.sourceUrls.prefix(4).enumerated()), id: \.offset) { index, url in
                            ExchangeSourceLink(title: "查看學生來源 \(index + 1)", url: url)
                        }
                    }
                    .padding(.top, ExchangeSpacing.sm)
                } label: {
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(highlight.title).font(ExchangeTypography.headline)
                            Text("\(highlight.sourceCount) 個來源已整理")
                                .font(ExchangeTypography.caption)
                                .foregroundStyle(ExchangeColor.labelSecondary)
                        }
                        Spacer()
                    }
                }
                .exchangeCard()
            }
        }
    }

    private func loadDetails(force: Bool = false) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            async let loadedWorkflow = loadWorkflow(force: force)
            async let loadedExperiences = loadExperiences(force: force)
            workflow = try await loadedWorkflow
            experiences = try await loadedExperiences
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func loadWorkflow(force: Bool) async throws -> UniversityApplicationWorkflow {
        let cached = try await api.workflow(for: university.schoolName, refresh: force)
        if cached.steps.isEmpty && !force {
            return try await api.workflow(for: university.schoolName, refresh: true)
        }
        return cached
    }

    private func loadExperiences(force: Bool) async throws -> StudentExperienceDigest {
        let cached = try await api.experiences(for: university.schoolName, refresh: force)
        if cached.totalSources == 0 && !force {
            return try await api.experiences(for: university.schoolName, refresh: true)
        }
        return cached
    }
}

private extension String {
    var nilIfEmpty: String? { isEmpty ? nil : self }
}
