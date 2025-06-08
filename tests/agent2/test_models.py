import unittest
from pydantic import ValidationError

from agents.agent2.models import FeasibilityAssessment

class TestFeasibilityAssessment(unittest.TestCase):

    def test_successful_creation(self):
        assessment_data = {
            "data_obtainability": "PUBLIC",
            "tools_availability": "OPEN_SOURCE",
            "confidence_score": 0.8,
            "summary": "All required data is publicly available and open-source tools are suitable."
        }
        assessment = FeasibilityAssessment(**assessment_data)
        self.assertEqual(assessment.data_obtainability, "PUBLIC")
        self.assertEqual(assessment.tools_availability, "OPEN_SOURCE")
        self.assertEqual(assessment.confidence_score, 0.8)
        self.assertEqual(assessment.summary, "All required data is publicly available and open-source tools are suitable.")

    def test_invalid_data_obtainability(self):
        with self.assertRaises(ValidationError):
            FeasibilityAssessment(
                data_obtainability="NON_EXISTENT_VALUE",
                tools_availability="OPEN_SOURCE",
                confidence_score=0.8,
                summary="Test summary"
            )

    def test_invalid_tools_availability(self):
        with self.assertRaises(ValidationError):
            FeasibilityAssessment(
                data_obtainability="PUBLIC",
                tools_availability="INVALID_TOOL_STATUS",
                confidence_score=0.8,
                summary="Test summary"
            )

    def test_invalid_confidence_score_too_low(self):
        with self.assertRaises(ValidationError):
            FeasibilityAssessment(
                data_obtainability="PUBLIC",
                tools_availability="OPEN_SOURCE",
                confidence_score=-0.1,
                summary="Test summary"
            )

    def test_invalid_confidence_score_too_high(self):
        with self.assertRaises(ValidationError):
            FeasibilityAssessment(
                data_obtainability="PRIVATE",
                tools_availability="COMMERCIAL",
                confidence_score=1.1,
                summary="Test summary"
            )

    def test_missing_summary(self): # Summary is a required field
        with self.assertRaises(ValidationError):
            FeasibilityAssessment(
                data_obtainability="UNAVAILABLE",
                tools_availability="REQUIRES_DEVELOPMENT",
                confidence_score=0.1
            )

    def test_literal_values_data_obtainability(self):
        valid_values = ['PUBLIC', 'PRIVATE', 'UNAVAILABLE']
        for value in valid_values:
            try:
                FeasibilityAssessment(
                    data_obtainability=value,
                    tools_availability="OPEN_SOURCE",
                    confidence_score=0.5,
                    summary=f"Testing {value}"
                )
            except ValidationError:
                self.fail(f"ValidationError raised for valid data_obtainability: {value}")

    def test_literal_values_tools_availability(self):
        valid_values = ['OPEN_SOURCE', 'COMMERCIAL', 'REQUIRES_DEVELOPMENT']
        for value in valid_values:
            try:
                FeasibilityAssessment(
                    data_obtainability="PUBLIC",
                    tools_availability=value,
                    confidence_score=0.5,
                    summary=f"Testing {value}"
                )
            except ValidationError:
                self.fail(f"ValidationError raised for valid tools_availability: {value}")

if __name__ == '__main__':
    unittest.main()
