import unittest
from unittest.mock import patch

from backend.services.test_pipeline import persist_and_schedule_test_agent_response


class TestPipelineCachingTests(unittest.TestCase):
    @patch("backend.services.test_pipeline._schedule_telemetry_log")
    @patch("backend.services.test_pipeline.store_result")
    def test_caches_results_when_no_attack_errors(self, store_result_mock, telemetry_mock) -> None:
        evaluated_results = [
            {
                "attack_id": "a1",
                "attack_name": "Attack 1",
                "category": "test",
                "attack_text": "payload",
                "target_response": "safe",
                "is_vulnerable": False,
                "reason": "blocked",
                "error": None,
            }
        ]

        response = persist_and_schedule_test_agent_response(
            cache_key="k1",
            system_prompt="prompt",
            target_model="gpt-4o-mini",
            temperature=0.7,
            response_format="text",
            evaluated_results=evaluated_results,
        )

        self.assertEqual(response["total_attacks"], 1)
        self.assertEqual(response["vulnerabilities_found"], 0)
        store_result_mock.assert_called_once()
        stored_data = store_result_mock.call_args[0][1]
        self.assertEqual(stored_data["system_prompt"], "prompt")
        self.assertEqual(stored_data["temperature"], 0.7)
        self.assertEqual(stored_data["response_format"], "text")
        telemetry_mock.assert_called_once()

    @patch("backend.services.test_pipeline._schedule_telemetry_log")
    @patch("backend.services.test_pipeline.store_result")
    def test_does_not_cache_results_when_any_attack_has_error(self, store_result_mock, telemetry_mock) -> None:
        evaluated_results = [
            {
                "attack_id": "a1",
                "attack_name": "Attack 1",
                "category": "test",
                "attack_text": "payload",
                "target_response": None,
                "is_vulnerable": False,
                "reason": "attack failed",
                "error": "timeout",
            }
        ]

        response = persist_and_schedule_test_agent_response(
            cache_key="k2",
            system_prompt="prompt",
            target_model="gpt-4o-mini",
            temperature=0.7,
            response_format="text",
            evaluated_results=evaluated_results,
        )

        self.assertEqual(response["total_attacks"], 1)
        self.assertEqual(response["vulnerabilities_found"], 0)
        store_result_mock.assert_not_called()
        telemetry_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
