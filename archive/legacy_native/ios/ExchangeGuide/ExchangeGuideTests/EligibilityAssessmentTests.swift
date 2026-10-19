import XCTest
@testable import ExchangeGuide

final class EligibilityAssessmentTests: XCTestCase {
    func testReadyWhenAcademicAndLanguageThresholdsPass() {
        let assessment = EligibilityAssessment(
            academicScore: 82,
            languageTest: .ielts,
            languageScore: 6,
            matchedSchoolCount: 12
        )

        XCTAssertTrue(assessment.academicPass)
        XCTAssertTrue(assessment.languagePass)
        XCTAssertTrue(assessment.isReady)
        XCTAssertTrue(assessment.summary.contains("12"))
    }

    func testNotReadyWhenEitherThresholdFails() {
        let assessment = EligibilityAssessment(
            academicScore: 69,
            languageTest: .toeic,
            languageScore: 800,
            matchedSchoolCount: 4
        )

        XCTAssertFalse(assessment.academicPass)
        XCTAssertTrue(assessment.languagePass)
        XCTAssertFalse(assessment.isReady)
    }

    func testLanguageThresholdsMatchPublishedBasicRules() {
        XCTAssertEqual(LanguageTest.toeic.minimum, 700)
        XCTAssertEqual(LanguageTest.ielts.minimum, 5.5)
        XCTAssertEqual(LanguageTest.toefl.minimum, 61)
        XCTAssertEqual(LanguageTest.duolingo.minimum, 105)
    }
}
