import unittest
from unittest.mock import patch

from researchmind.pipeline import run_research_pipeline


class PipelineTests(unittest.TestCase):
    @patch("researchmind.agents.web_search")
    @patch("researchmind.agents.scrape_urls_concurrent")
    @patch("researchmind.agents.generate_report")
    def test_run_research_pipeline_success(self, mock_gen_report, mock_scrape, mock_search):
        mock_search.return_value = [
            {"title": "Sample Title", "url": "https://sample.com", "snippet": "Sample snippet"}
        ]
        mock_scrape.return_value = [
            {
                "url": "https://sample.com",
                "title": "Sample Title Page",
                "content": "Sample detailed scraped text.",
                "status": "success",
                "error": None,
            }
        ]
        mock_gen_report.return_value = "# Research Report: Test Topic\n\n## Executive Summary\nTest report content."

        progress_logs = []

        def callback(msg: str):
            progress_logs.append(msg)

        result = run_research_pipeline("Test Topic", depth="Fast", progress_callback=callback)

        self.assertEqual(result["topic"], "Test Topic")
        self.assertIn("writer", result)
        self.assertIn("audit", result)
        self.assertIn("fact_check", result)
        self.assertIn("telemetry", result)
        self.assertIn("dag_mermaid", result)
        self.assertEqual(len(result["telemetry"]), 5)
        self.assertGreater(len(progress_logs), 0)
        self.assertEqual(result["audit"]["total_sources_scraped"], 1)


if __name__ == "__main__":
    unittest.main()

