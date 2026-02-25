import unittest

from backend.services.cache_service import make_cache_key


class CacheKeyTests(unittest.TestCase):
    def test_cache_key_is_stable_for_same_inputs(self) -> None:
        first = make_cache_key("prompt", "gpt-4o-mini", 0.7, "text")
        second = make_cache_key("prompt", "gpt-4o-mini", 0.7, "text")
        self.assertEqual(first, second)

    def test_cache_key_changes_when_inputs_change(self) -> None:
        base = make_cache_key("prompt", "gpt-4o-mini", 0.7, "text")
        changed_model = make_cache_key("prompt", "gpt-4.1-mini", 0.7, "text")
        changed_temperature = make_cache_key("prompt", "gpt-4o-mini", 0.8, "text")
        changed_format = make_cache_key("prompt", "gpt-4o-mini", 0.7, "json_schema")

        self.assertNotEqual(base, changed_model)
        self.assertNotEqual(base, changed_temperature)
        self.assertNotEqual(base, changed_format)


if __name__ == "__main__":
    unittest.main()
