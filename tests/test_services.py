import os
import tempfile
import unittest

from researchmind.services import generate_report


class ServicesTests(unittest.TestCase):
    def setUp(self):
        self.cache_directory = tempfile.TemporaryDirectory()
        self.previous_cache = os.environ.get("CACHE_DIR")
        self.previous_key = os.environ.pop("GOOGLE_API_KEY", None)
        os.environ["CACHE_DIR"] = self.cache_directory.name

    def tearDown(self):
        if self.previous_cache is None:
            os.environ.pop("CACHE_DIR", None)
        else:
            os.environ["CACHE_DIR"] = self.previous_cache
        if self.previous_key is not None:
            os.environ["GOOGLE_API_KEY"] = self.previous_key
        self.cache_directory.cleanup()

    def test_missing_google_api_key_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            generate_report(
                "Testing",
                "Title: Example\nURL: https://example.com\nSnippet: A reliable example source.",
            )
        self.assertIn("GOOGLE_API_KEY is not configured", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

