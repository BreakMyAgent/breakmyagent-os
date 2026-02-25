import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.errors import TelemetryError


class WaitlistEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    @patch("backend.main.add_waitlist_lead")
    def test_waitlist_submission_succeeds(self, add_lead_mock) -> None:
        response = self.client.post("/api/waitlist", json={"email": "user@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        add_lead_mock.assert_called_once_with("user@example.com")

    def test_waitlist_submission_rejects_invalid_email(self) -> None:
        response = self.client.post("/api/waitlist", json={"email": "not-an-email"})
        self.assertEqual(response.status_code, 422)

    @patch("backend.main.add_waitlist_lead")
    def test_waitlist_submission_maps_storage_error(self, add_lead_mock) -> None:
        add_lead_mock.side_effect = TelemetryError("database unavailable")
        response = self.client.post("/api/waitlist", json={"email": "user@example.com"})
        self.assertEqual(response.status_code, 500)
        self.assertIn("Failed to save waitlist lead", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
