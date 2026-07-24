import Foundation

enum LanguageTest: String, CaseIterable, Identifiable {
    case toeic = "TOEIC"
    case ielts = "IELTS"
    case toefl = "TOEFL iBT"
    case duolingo = "Duolingo"

    var id: String { rawValue }

    var minimum: Double {
        switch self {
        case .toeic: 700
        case .ielts: 5.5
        case .toefl: 61
        case .duolingo: 105
        }
    }

    var scorePrompt: String {
        switch self {
        case .toeic: "例如 750"
        case .ielts: "例如 6.0"
        case .toefl: "例如 80"
        case .duolingo: "例如 110"
        }
    }
}

struct EligibilityAssessment: Equatable {
    let academicScore: Double
    let languageTest: LanguageTest
    let languageScore: Double
    let matchedSchoolCount: Int

    var academicPass: Bool { academicScore >= 70 }
    var languagePass: Bool { languageScore >= languageTest.minimum }
    var isReady: Bool { academicPass && languagePass }

    var title: String {
        isReady ? "符合公開基本門檻" : "還有條件需要補強"
    }

    var summary: String {
        if isReady {
            return "可先查看符合學院與學制的 \(matchedSchoolCount) 所學校，再逐校確認額外限制。"
        }
        return "這是依公開校內基本門檻的初判，不代表正式錄取或校方資格認定。"
    }
}
