import unittest

try:
    from .numeric_semantic_diagnostic import classify
except ImportError:
    from numeric_semantic_diagnostic import classify


class NumericDiagnosticTest(unittest.TestCase):
    def test_explicit_percent_and_rounding(self):
        self.assertEqual(classify("0.65644", "65.6%", "percent_fraction"), "ROUNDING_COMPATIBLE")
        self.assertEqual(classify("0.05624", "5.62%", "percent_fraction"), "ROUNDING_COMPATIBLE")
        self.assertEqual(classify("0.05624", "5.6%", "percent_fraction"), "ROUNDING_COMPATIBLE")
        self.assertEqual(classify("0.05624", "56.2%", "percent_fraction"), "INCOMPATIBLE")

    def test_units_are_not_silently_conflated(self):
        self.assertEqual(classify("0.65644", "65.6", "percent_fraction"), "UNRESOLVED_BARE_PERCENT")
        self.assertEqual(classify("0.12", "$12", "percent_fraction"), "UNRESOLVED_FORMAT_OR_UNIT")
        self.assertEqual(classify("12", "12%", "unitless"), "UNRESOLVED_FORMAT_OR_UNIT")

    def test_sign_and_integer_rounding(self):
        self.assertEqual(classify("-5", "5", "unitless"), "INCOMPATIBLE")
        self.assertEqual(classify("41932.20339", "41932", "unitless"), "ROUNDING_COMPATIBLE")
        self.assertEqual(classify("41933", "41932", "unitless"), "INCOMPATIBLE")


if __name__ == "__main__":
    unittest.main()
