import unittest
from dataclasses import replace
from production import sample_plan, validate_plan

class ProductionTests(unittest.TestCase):
    def test_sample_is_valid(self):
        self.assertEqual(validate_plan(sample_plan()), [])

    def test_publishing_cannot_be_approved_by_generator(self):
        self.assertIn("Draft generator must not grant publishing approval", validate_plan(replace(sample_plan(), publishing_approved=True)))

    def test_short_duration(self):
        plan = sample_plan()
        self.assertIn("Short duration must be 12-60 seconds", validate_plan(replace(plan, scenes=plan.scenes[:1])))

if __name__ == "__main__":
    unittest.main()
