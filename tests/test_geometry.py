import unittest

from part_generator_api.geometry import ScrewGenerator, WasherGenerator


class TestScrewGenerator(unittest.TestCase):

    def test_step_bytes_not_empty(self):
        generator = ScrewGenerator(diameter=12.0, length=80.0)
        data = generator.to_step_bytes()
        self.assertGreater(len(data), 0)

    def test_step_bytes_valid_format(self):
        generator = ScrewGenerator(diameter=12.0, length=80.0)
        data = generator.to_step_bytes()
        self.assertIn(b"ISO-10303-21", data[:100])

    def test_valid_bounding_box(self):
        """Validates retrieval from ISO 4762 DICT"""
        generator = ScrewGenerator(12.0, 80.0)
        bb = generator.generate().bounding_box()
        self.assertAlmostEqual(bb.size.Z, 92.0, places=1)
        self.assertAlmostEqual(bb.size.X, 18.0, places=1)
        self.assertAlmostEqual(bb.size.Y, 18.0, places=1)

class TestWasherGenerator(unittest.TestCase):

    def test_step_bytes_not_empty(self):
        generator = WasherGenerator(inner_diameter=13.0, outer_diameter=24.0, thickness=2.0)
        data = generator.to_step_bytes()
        self.assertGreater(len(data), 0)

    def test_step_bytes_valid_format(self):
        generator = WasherGenerator(inner_diameter=13.0, outer_diameter=24.0, thickness=2.0)
        data = generator.to_step_bytes()
        self.assertIn(b"ISO-10303-21", data[:100])


if __name__ == "__main__":
    unittest.main()
