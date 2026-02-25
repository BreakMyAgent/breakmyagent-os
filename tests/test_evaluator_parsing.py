import unittest

from backend.core.evaluator import parse_evaluator_response
from backend.services.errors import JudgeModelError


class EvaluatorParsingTests(unittest.TestCase):
    def test_parses_plain_json(self) -> None:
        parsed = parse_evaluator_response('{"is_vulnerable": false, "reason": "Blocked injection."}')
        self.assertEqual(parsed, {"is_vulnerable": False, "reason": "Blocked injection."})

    def test_parses_fenced_json(self) -> None:
        parsed = parse_evaluator_response(
            "```json\n{\"is_vulnerable\": true, \"reason\": \"Prompt leaked.\"}\n```"
        )
        self.assertEqual(parsed, {"is_vulnerable": True, "reason": "Prompt leaked."})

    def test_raises_on_invalid_payload(self) -> None:
        with self.assertRaises(JudgeModelError):
            parse_evaluator_response("{\"is_vulnerable\": \"yes\", \"reason\": 123}")


if __name__ == "__main__":
    unittest.main()
