package tw.edu.cgu.exchangeguide;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import tw.edu.cgu.exchangeguide.ui.screens.EligibilityAssessment;
import tw.edu.cgu.exchangeguide.ui.screens.LanguageTest;

public class EligibilityAssessmentTest {
    @Test
    public void passingAcademicAndLanguageScoresAreReady() {
        EligibilityAssessment result = new EligibilityAssessment(82.0, LanguageTest.IELTS, 6.0, 4);

        assertTrue(result.getAcademicPass());
        assertTrue(result.getLanguagePass());
        assertTrue(result.isReady());
    }

    @Test
    public void languageBelowThresholdNeedsImprovement() {
        EligibilityAssessment result = new EligibilityAssessment(88.0, LanguageTest.TOEIC, 650.0, 0);

        assertTrue(result.getAcademicPass());
        assertFalse(result.getLanguagePass());
        assertFalse(result.isReady());
    }
}
