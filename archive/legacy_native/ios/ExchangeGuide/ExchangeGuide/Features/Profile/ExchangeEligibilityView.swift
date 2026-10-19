import SwiftUI

struct ExchangeEligibilityView: View {
    @EnvironmentObject private var store: DashboardStore
    @AppStorage("appearanceMode") private var appearanceMode = AppearanceMode.dark.rawValue

    @State private var college = ""
    @State private var degree = "大學部"
    @State private var academicScore = ""
    @State private var languageTest = LanguageTest.toeic
    @State private var languageScore = ""
    @State private var assessment: EligibilityAssessment?

    private var colleges: [String] {
        let values = store.dashboard?.partnerUniversities
            .flatMap { splitValues($0.colleges) }
            .filter { !$0.contains("不限") && !$0.contains("全校") } ?? []
        return Array(Set(values)).sorted()
    }

    private var matchingUniversities: [PartnerUniversity] {
        guard let universities = store.dashboard?.partnerUniversities, !college.isEmpty else { return [] }
        return universities.filter { university in
            let collegeMatches = university.colleges?.localizedCaseInsensitiveContains(college) == true
                || university.colleges?.contains("不限") == true
                || university.colleges?.contains("全校") == true
            let degreeMatches = university.degreeLevels?.localizedCaseInsensitiveContains(degree) == true
                || university.degreeLevels?.contains("不限") == true
            return collegeMatches && degreeMatches
        }
    }

    private var formIsValid: Bool {
        !college.isEmpty && Double(academicScore) != nil && Double(languageScore) != nil
    }

    var body: some View {
        Group {
            if store.dashboard != nil {
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: ExchangeSpacing.xl) {
                        ExchangeSectionHeader(
                            eyebrow: "初步檢查",
                            title: "確認自己是否符合",
                            detail: "輸入校內成績與語言成績，快速找出值得進一步核對的合作校。"
                        )

                        ExchangeInlineBanner(
                            title: "這不是正式資格審查",
                            message: "合作校可能另有 GPA、年級、科系或單項語言門檻，請進入學校詳情確認。",
                            kind: .warning
                        )

                        inputForm

                        Button {
                            evaluate()
                        } label: {
                            Label("檢查我的資格", systemImage: "checkmark.seal.fill")
                                .frame(maxWidth: .infinity, minHeight: ExchangeLayout.primaryButtonHeight)
                        }
                        .exchangeProminentButtonStyle()
                        .disabled(!formIsValid)

                        if let assessment {
                            resultCard(assessment)
                        }

                        appearanceSettings
                    }
                    .padding(ExchangeLayout.compactMargin)
                    .padding(.bottom, ExchangeSpacing.section)
                }
            } else if let error = store.errorMessage {
                ExchangeErrorState(message: error) {
                    Task { await store.load(force: true) }
                }
            } else {
                ExchangeLoadingState(message: "正在準備資格檢查")
            }
        }
        .navigationTitle("我的資格")
        .navigationBarTitleDisplayMode(.inline)
        .exchangePageBackground()
    }

    private var inputForm: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.lg) {
            VStack(alignment: .leading, spacing: ExchangeSpacing.xs) {
                Text("所屬學院")
                    .font(ExchangeTypography.headline)
                Picker("所屬學院", selection: $college) {
                    Text("請選擇").tag("")
                    ForEach(colleges, id: \.self) { value in
                        Text(value).tag(value)
                    }
                }
                .pickerStyle(.menu)
                .frame(maxWidth: .infinity, minHeight: ExchangeLayout.fieldHeight, alignment: .leading)
            }

            VStack(alignment: .leading, spacing: ExchangeSpacing.xs) {
                Text("學制")
                    .font(ExchangeTypography.headline)
                Picker("學制", selection: $degree) {
                    Text("大學部").tag("大學部")
                    Text("研究所").tag("研究所")
                }
                .pickerStyle(.segmented)
                .frame(minHeight: ExchangeLayout.minimumTarget)
            }

            scoreField(title: "學業平均", prompt: "例如 82", text: $academicScore)

            VStack(alignment: .leading, spacing: ExchangeSpacing.xs) {
                Text("語言檢定")
                    .font(ExchangeTypography.headline)
                Picker("語言檢定", selection: $languageTest) {
                    ForEach(LanguageTest.allCases) { test in
                        Text(test.rawValue).tag(test)
                    }
                }
                .pickerStyle(.menu)
                .frame(maxWidth: .infinity, minHeight: ExchangeLayout.fieldHeight, alignment: .leading)
                Text("公開基本參考門檻：\(languageTest.minimum.formatted())")
                    .font(ExchangeTypography.caption)
                    .foregroundStyle(ExchangeColor.labelSecondary)
            }

            scoreField(title: "語言成績", prompt: languageTest.scorePrompt, text: $languageScore)
        }
        .exchangeCard()
    }

    private func scoreField(title: String, prompt: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.xs) {
            Text(title)
                .font(ExchangeTypography.headline)
            TextField(prompt, text: text)
                .keyboardType(.decimalPad)
                .padding(.horizontal, ExchangeSpacing.sm)
                .frame(minHeight: ExchangeLayout.fieldHeight)
                .background(ExchangeColor.backgroundTertiary)
                .clipShape(RoundedRectangle(cornerRadius: ExchangeRadius.control, style: .continuous))
                .overlay {
                    RoundedRectangle(cornerRadius: ExchangeRadius.control, style: .continuous)
                        .stroke(ExchangeColor.separator, lineWidth: 1)
                }
        }
    }

    private func resultCard(_ result: EligibilityAssessment) -> some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.md) {
            ExchangeSectionHeader(
                eyebrow: result.isReady ? "可開始選校" : "建議先補強",
                title: result.title,
                detail: result.summary
            )
            ExchangeInfoRow(
                label: "學業平均",
                value: result.academicPass ? "達到 70 分基本門檻" : "未達 70 分基本門檻",
                symbol: result.academicPass ? "checkmark.circle.fill" : "exclamationmark.circle.fill"
            )
            ExchangeInfoRow(
                label: result.languageTest.rawValue,
                value: result.languagePass ? "達到 \(result.languageTest.minimum.formatted())" : "未達 \(result.languageTest.minimum.formatted())",
                symbol: result.languagePass ? "checkmark.circle.fill" : "exclamationmark.circle.fill"
            )

            if !matchingUniversities.isEmpty {
                Divider().overlay(ExchangeColor.separator)
                Text("可優先核對的學校")
                    .font(ExchangeTypography.headline)
                ForEach(matchingUniversities.prefix(8)) { university in
                    NavigationLink {
                        ExchangeSchoolDetailView(university: university)
                    } label: {
                        ExchangeUniversityRow(university: university)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .exchangeCard()
    }

    private var appearanceSettings: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
            ExchangeSectionHeader(title: "外觀", detail: "預設深色，也可跟隨 iPhone 系統設定")
            Picker("外觀模式", selection: $appearanceMode) {
                ForEach(AppearanceMode.allCases) { mode in
                    Text(mode.title).tag(mode.rawValue)
                }
            }
            .pickerStyle(.segmented)
            .frame(minHeight: ExchangeLayout.minimumTarget)
        }
    }

    private func evaluate() {
        guard let academic = Double(academicScore), let language = Double(languageScore) else { return }
        assessment = EligibilityAssessment(
            academicScore: academic,
            languageTest: languageTest,
            languageScore: language,
            matchedSchoolCount: matchingUniversities.count
        )
    }

    private func splitValues(_ value: String?) -> [String] {
        guard let value else { return [] }
        return value
            .components(separatedBy: CharacterSet(charactersIn: "、,，;/／\n"))
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }
}
