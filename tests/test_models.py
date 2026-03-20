import unittest

from pydantic import ValidationError

from part_generator_api.models import ScrewRequest, WasherRequest


class TestScrewRequest(unittest.TestCase):

    def test_valid_screw(self):
        req = ScrewRequest(diameter=12.0, length=80.0)
        self.assertEqual(req.diameter, 12.0)
        self.assertEqual(req.length, 80.0)

    def test_zero_diameter_rejected(self):
        with self.assertRaises(ValidationError):
            ScrewRequest(diameter=0, length=80.0)

    def test_negative_diameter_rejected(self):
        with self.assertRaises(ValidationError):
            ScrewRequest(diameter=-5.0, length=80.0)

    def test_negative_length_rejected(self):
        with self.assertRaises(ValidationError):
            ScrewRequest(diameter=12.0, length=-1.0)

    def test_zero_length_rejected(self):
        with self.assertRaises(ValidationError):
            ScrewRequest(diameter=12.0, length=0)

    def test_missing_field_rejected(self):
        with self.assertRaises(ValidationError):
            ScrewRequest(diameter=12.0)


class TestWasherRequest(unittest.TestCase):

    def test_valid_washer(self):
        req = WasherRequest(inner_diameter=13.0, outer_diameter=24.0, thickness=2.0)
        self.assertEqual(req.inner_diameter, 13.0)
        self.assertEqual(req.outer_diameter, 24.0)
        self.assertEqual(req.thickness, 2.0)

    def test_negative_inner_diameter_rejected(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=-1.0, outer_diameter=24.0, thickness=2.0)

    def test_zero_inner_diameter_rejected(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=0, outer_diameter=24.0, thickness=2.0)

    def test_negative_outer_diameter_rejected(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=13.0, outer_diameter=-1.0, thickness=2.0)

    def test_zero_outer_diameter_rejected(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=13.0, outer_diameter=0, thickness=2.0)

    def test_negative_thickness_rejected(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=13.0, outer_diameter=24.0, thickness=-1.0)

    def test_zero_thickness_rejected(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=13.0, outer_diameter=24.0, thickness=0)

    def test_inner_equal_to_outer_rejected(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=24.0, outer_diameter=24.0, thickness=2.0)

    def test_inner_greater_than_outer_rejected(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=30.0, outer_diameter=24.0, thickness=2.0)

    def test_missing_field_rejected(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=13.0, outer_diameter=24.0)


if __name__ == "__main__":
    unittest.main()
