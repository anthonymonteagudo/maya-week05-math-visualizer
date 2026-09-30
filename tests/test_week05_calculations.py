import unittest
from lesson_materials.week_05_applied_math import calculations as c
from lesson_materials.week_05_applied_math.math_core import PRESETS, analyze


def sample(preset):
    points = PRESETS[preset]
    return dict(analyze(*points), points=points, units="cm")


class WorkedMathTests(unittest.TestCase):
    def test_known_examples(self):
        data = sample("Bent arm")
        self.assertIn("(3, 4, 0)", c.vectors(data, "Vectors"))
        self.assertIn("= sqrt(25) = 5 cm", c.vectors(data, "Normalize"))
        dot = c.vectors(data, "Dot / projection")
        self.assertIn("= -7", dot)
        self.assertIn("H = (3, 0, 0)", dot)
        self.assertIn("106.2602", dot)
        self.assertIn("(0, 0, -24)", c.vectors(data, "Cross / plane"))

    def test_degenerate_explanations(self):
        self.assertIn("UNDEFINED", c.vectors(sample("Zero upper segment"), "Normalize"))
        self.assertIn("UNDEFINED", c.vectors(sample("Straight"), "Cross / plane"))
        self.assertIn("UNDEFINED", c.vectors(sample("Coincident shoulder/wrist"), "Dot / projection"))

    def test_matrix_translation_and_rotation(self):
        values = (0,1,0,0,-1,0,0,0,0,0,1,0,10,20,30,1)
        self.assertIn("p_world = (8, 21, 33, 1)", c.matrix(values,(1,2,3)))

    def test_interpolation_and_reach(self):
        self.assertIn("(45, 45, 0)", c.interpolation(.5,"euler"))
        self.assertIn("(0.2887, 0.2887, -0.2887, 0.866)", c.interpolation(.5,"slerp"))
        self.assertIn("0 <= 20 <= 10", c.vectors(sample("Bent arm"), "Rig only", (20,0,0)))


if __name__ == "__main__":
    unittest.main()


class HomogeneousTransformTests(unittest.TestCase):
    def test_point_and_direction_translation(self):
        from lesson_materials.week_05_applied_math.math_core import transform_homogeneous
        matrix=(1,0,0,0, 0,1,0,0, 0,0,1,0, 10,20,30,1)
        self.assertEqual(transform_homogeneous((3,4,0,1),matrix),(13,24,30,1))
        self.assertEqual(transform_homogeneous((3,4,0,0),matrix),(3,4,0,0))

    def test_rotation_row_vector_convention(self):
        from lesson_materials.week_05_applied_math.math_core import transform_homogeneous
        matrix=(0,1,0,0, -1,0,0,0, 0,0,1,0, 0,0,0,1)
        self.assertEqual(transform_homogeneous((1,0,0,0),matrix),(0,1,0,0))
