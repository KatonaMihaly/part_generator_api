import unittest

from fastapi.testclient import TestClient

from part_generator_api.main import app


class TestGenerateScrew(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_generate_screw_status_200(self):
        response = self.client.post(
            "/v1/generate/screw", json={"diameter": 12.0, "length": 80.0}
        )
        self.assertEqual(response.status_code, 200)

    def test_generate_screw_content_type(self):
        response = self.client.post(
            "/v1/generate/screw", json={"diameter": 12.0, "length": 80.0}
        )
        self.assertIn("application/STEP", response.headers["content-type"])

    def test_generate_screw_step_format(self):
        response = self.client.post(
            "/v1/generate/screw", json={"diameter": 12.0, "length": 80.0}
        )
        self.assertIn(b"ISO-10303-21", response.content[:100])

    def test_generate_screw_filename_header(self):
        response = self.client.post(
            "/v1/generate/screw", json={"diameter": 12.0, "length": 80.0}
        )
        self.assertIn("screw_M12.0x80.0.step", response.headers["content-disposition"])

    def test_generate_screw_invalid_params_422(self):
        response = self.client.post(
            "/v1/generate/screw", json={"diameter": 13, "length": 80.0}
        )
        self.assertEqual(response.status_code, 422)

    def test_generate_screw_missing_params_422(self):
        response = self.client.post(
            "/v1/generate/screw", json={"diameter": 12.0}
        )
        self.assertEqual(response.status_code, 422)


class TestGenerateWasher(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_generate_washer_status_200(self):
        response = self.client.post(
            "/v1/generate/washer",
            json={"inner_diameter": 13.0, "outer_diameter": 24.0, "thickness": 2.0},
        )
        self.assertEqual(response.status_code, 200)

    def test_generate_washer_content_type(self):
        response = self.client.post(
            "/v1/generate/washer",
            json={"inner_diameter": 13.0, "outer_diameter": 24.0, "thickness": 2.0},
        )
        self.assertIn("application/STEP", response.headers["content-type"])

    def test_generate_washer_step_format(self):
        response = self.client.post(
            "/v1/generate/washer",
            json={"inner_diameter": 13.0, "outer_diameter": 24.0, "thickness": 2.0},
        )
        self.assertIn(b"ISO-10303-21", response.content[:100])

    def test_generate_washer_invalid_params_422(self):
        response = self.client.post(
            "/v1/generate/washer",
            json={"inner_diameter": 24.0, "outer_diameter": 13.0, "thickness": 2.0},
        )
        self.assertEqual(response.status_code, 422)

    def test_generate_washer_missing_params_422(self):
        response = self.client.post(
            "/v1/generate/washer",
            json={"inner_diameter": 13.0, "outer_diameter": 24.0},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
