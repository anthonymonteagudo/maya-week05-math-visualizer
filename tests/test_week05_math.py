import math
import unittest

from lesson_materials.week_05_applied_math.math_core import PRESETS, analyze


class MathTests(unittest.TestCase):
    def test_bent_arm(self):
        r = analyze(*PRESETS["Bent arm"])
        self.assertEqual(r["dot"], -7)
        self.assertEqual(r["cross"], (0, 0, -24))
        self.assertEqual(r["projection"], (3, 0, 0))
        self.assertEqual(r["helper"], (3, 6, 0))
        self.assertAlmostEqual(r["angle"], 106.26020470831197)

    def test_undefined_cases(self):
        self.assertIsNone(analyze(*PRESETS["Straight"])["normal"])
        self.assertIsNone(analyze(*PRESETS["Straight"])["helper"])
        self.assertIsNone(analyze(*PRESETS["Coincident shoulder/wrist"])["projection"])
        self.assertIsNone(analyze(*PRESETS["Zero upper segment"])["angle"])

    def test_translation(self):
        r = analyze(*[tuple(v + 10 for v in p) for p in PRESETS["Bent arm"]])
        self.assertEqual(r["projection"], (13, 10, 10))
        self.assertEqual(r["bend"], (0, 4, 0))
        self.assertEqual(r["cross"], (0, 0, -24))

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            analyze((math.nan, 0, 0), (0, 0, 0), (1, 0, 0))


if __name__ == "__main__":
    unittest.main()
