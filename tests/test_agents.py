import os
import unittest
from unittest.mock import MagicMock, patch

from researchmind.agents import AuditorAgent, ExtractorAgent, FactCheckerAgent, PlannerAgent
from researchmind.tools import scrape_url, scrape_urls_concurrent


class AgentsTests(unittest.TestCase):
    def test_fact_checker_agent(self):
        fact_checker = FactCheckerAgent()
        report = """# Research Report: Quantum Computing
- Qubits enable quantum superposition and entanglement in computational space.
- Advanced fault-tolerant quantum algorithms are actively being researched worldwide.
"""
        sources = [
            {
                "url": "https://quantum.com",
                "content": "Qubits enable quantum superposition and entanglement in computational algorithms worldwide.",
                "snippet": "Advanced quantum computing systems",
            }
        ]
        res = fact_checker.verify_facts(report, sources)
        self.assertIn("verifiability_score", res)
        self.assertGreater(res["verifiability_score"], 50)
        self.assertTrue(res["fact_check_passed"])
        self.assertGreater(len(res["claim_evaluations"]), 0)

    def test_planner_agent_queries(self):
        planner = PlannerAgent()
        fast_queries = planner.plan_research("Quantum Computing", depth="Fast")
        self.assertEqual(len(fast_queries), 1)

        balanced_queries = planner.plan_research("Quantum Computing", depth="Balanced")
        self.assertEqual(len(balanced_queries), 3)

        deep_queries = planner.plan_research("Quantum Computing", depth="Deep")
        self.assertEqual(len(deep_queries), 4)

    def test_auditor_agent_metrics(self):
        auditor = AuditorAgent()
        # Report with > 150 words to pass audit criteria
        report = """# Research Report: Quantum Computing
## Executive Summary
Quantum computing is a rapidly evolving field of computation that utilizes the fundamentals of quantum mechanics to solve complex computational problems significantly faster than classical supercomputers. Researchers across academia and global technology enterprises are making continuous breakthroughs in hardware stability and error correction.

## Key Findings & Detailed Analysis
- Qubits enable quantum superposition and entanglement, allowing parallel operations across vast state spaces that classical bits cannot replicate.
- Advanced fault-tolerant quantum algorithms are actively being researched by major institutes worldwide to achieve real-world quantum advantage.
- Recent physical hardware implementations include superconducting circuits, trapped ions, and photonic processors with scaling roadmaps.
- Quantum key distribution (QKD) and post-quantum cryptography (PQC) standards are gaining industry adoption to safeguard critical communications.

## Strategic Implications & Future Outlook
As quantum capabilities mature, sectors such as drug discovery, materials science, financial modeling, and cryptographic security will undergo fundamental transformations.

## Conclusion & Sources
- Citation: [IBM Quantum](https://ibm.com/quantum)
"""
        sources = [
            {"title": "IBM Quantum", "url": "https://ibm.com/quantum", "status": "success"},
            {"title": "Google Quantum", "url": "https://quantum.google", "status": "error"},
        ]
        metrics = auditor.audit_report(report, sources)
        self.assertGreater(metrics["word_count"], 100)
        self.assertEqual(metrics["total_sources_scraped"], 2)
        self.assertEqual(metrics["successful_sources"], 1)
        self.assertEqual(metrics["cited_source_count"], 1)
        self.assertTrue(metrics["audit_passed"])


    @patch("researchmind.agents.web_search")
    @patch("researchmind.agents.scrape_urls_concurrent")
    def test_extractor_agent_success(self, mock_scrape_concurrent, mock_web_search):
        mock_web_search.return_value = [
            {"title": "Test Source", "url": "https://example.com/test", "snippet": "Test snippet"}
        ]
        mock_scrape_concurrent.return_value = [
            {
                "url": "https://example.com/test",
                "title": "Test Page",
                "content": "Full extracted article content.",
                "status": "success",
                "error": None,
            }
        ]

        extractor = ExtractorAgent()
        res = extractor.extract_research(["test query"])

        self.assertEqual(len(res["sources"]), 1)
        self.assertEqual(res["sources"][0]["title"], "Test Page")
        self.assertEqual(res["sources"][0]["content"], "Full extracted article content.")

    def test_scrape_url_invalid(self):
        res = scrape_url("ftp://invalid-url")
        self.assertEqual(res["status"], "error")
        self.assertIn("Absolute HTTP(S) URL is required", res["error"])

    def test_scrape_urls_concurrent_empty(self):
        res = scrape_urls_concurrent([])
        self.assertEqual(res, [])


if __name__ == "__main__":
    unittest.main()

