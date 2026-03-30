import unittest

from pydantic import ValidationError

from part_generator_api.models import ScrewRequest, WasherRequest
from part_generator_api.models.requests import ISO_4762_DIAMETERS


class TestScrewRequest(unittest.TestCase):

    def test_valid_standard_diameter(self):
        req = ScrewRequest(diameter=12, length=80.0)
        self.assertEqual(req.diameter, 12.0)
        self.assertEqual(req.length, 80.0)

    def test_non_standard_diameter_rejected(self):
        with self.assertRaises(ValidationError):
            ScrewRequest(diameter=7.1, length=80.0)

    def test_error_message_mentions_iso(self):
        with self.assertRaises(ValidationError) as err:
            ScrewRequest(diameter=7, length=80.0)
        self.assertIn("ISO 4762", str(err.exception))

    def test_all_standard_sizes_accepted(self):
        for d in ISO_4762_DIAMETERS:
            req = ScrewRequest(diameter=d, length=50.0)
            self.assertEqual(req.diameter, float(d))

    def test_negative_length_rejected(self):
        with self.assertRaises(ValidationError):
            ScrewRequest(diameter=12, length=-1.0)

    def test_zero_length_rejected(self):
        with self.assertRaises(ValidationError):
            ScrewRequest(diameter=12, length=0)

    def test_missing_field_rejected(self):
        with self.assertRaises(ValidationError):
            ScrewRequest(diameter=12)

    def test_length_at_upper_bound_accepted(self):
        req = ScrewRequest(diameter=12, length=200.0)
        self.assertEqual(req.length, 200.0)

    def test_length_above_upper_bound_rejected(self):
        with self.assertRaises(ValidationError):
            ScrewRequest(diameter=12, length=200.1)


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

    def test_missing_field_rejected_thickness(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=13.0, outer_diameter=24.0)

    def test_missing_field_rejected_outer_diameter(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=30.0, thickness=2.0)

    def test_missing_field_rejected_inner_diameter(self):
        with self.assertRaises(ValidationError):
            WasherRequest(outer_diameter=24.0, thickness=2.0)

    def test_outer_diameter_at_upper_bound_accepted(self):
        req = WasherRequest(inner_diameter=50.0, outer_diameter=100.0, thickness=2.0)
        self.assertEqual(req.outer_diameter, 100.0)

    def test_outer_diameter_above_upper_bound_rejected(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=50.0, outer_diameter=100.1, thickness=2.0)

    def test_thickness_at_upper_bound_accepted(self):
        req = WasherRequest(inner_diameter=13.0, outer_diameter=24.0, thickness=50.0)
        self.assertEqual(req.thickness, 50.0)

    def test_thickness_above_upper_bound_rejected(self):
        with self.assertRaises(ValidationError):
            WasherRequest(inner_diameter=13.0, outer_diameter=24.0, thickness=50.1)


if __name__ == "__main__":
    unittest.main()
