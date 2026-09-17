"""Multi-Agent System for ResearchMind.

Contains 4 distinct agents:
1. PlannerAgent: Analyzes research topic and formulates target search queries.
2. ExtractorAgent: Executes Tavily web searches and concurrently extracts scraped web context.
3. WriterAgent: Generates structured Markdown report using Google Gemini API.
4. AuditorAgent: Verifies report citations, word count, reading time, and research quality.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from .services import generate_report
from .tools import scrape_urls_concurrent, web_search

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Agent 1: Decomposes research topic into targeted queries based on depth."""

    def plan_research(self, topic: str, depth: str = "Balanced") -> list[str]:
        cleaned_topic = topic.strip()
        if not cleaned_topic:
            raise ValueError("Research topic cannot be empty.")

        depth_lower = depth.lower()
        if depth_lower == "fast":
            return [f"overview and key facts about {cleaned_topic}"]
        elif depth_lower == "deep":
            return [
                f"{cleaned_topic} overview and core concepts",
                f"{cleaned_topic} recent developments and updates",
                f"{cleaned_topic} technical analysis and implementation details",
                f"{cleaned_topic} challenges risks and future outlook",
            ]
        else:  # Balanced
            return [
                f"{cleaned_topic} overview and key facts",
                f"{cleaned_topic} recent updates and key developments",
                f"{cleaned_topic} analysis and implications",
            ]


class ExtractorAgent:
    """Agent 2: Executes Tavily API searches and concurrently scrapes source web pages."""

    def extract_research(
        self, queries: list[str], max_results_per_query: int = 2
    ) -> dict[str, Any]:
        all_search_hits: list[dict[str, str]] = []
        urls_to_scrape: list[str] = []

        # Execute search for each query via Tavily API
        for q in queries:
            try:
                hits = web_search(query=q, max_results=max_results_per_query)
                for h in hits:
                    all_search_hits.append(h)
                    if h.get("url"):
                        urls_to_scrape.append(h["url"])
            except Exception as error:
                logger.warning("Search query '%s' failed: %s", q, error)
                raise

        if not urls_to_scrape:
            raise RuntimeError("No search URLs returned from Tavily API for the given research queries.")

        # Deduplicate URLs while preserving order
        unique_urls = list(dict.fromkeys(urls_to_scrape))

        # Concurrently scrape web pages
        scraped_sources = scrape_urls_concurrent(unique_urls, max_workers=min(len(unique_urls), 4))

        # Merge search snippets with scraped content
        url_to_snippet = {h["url"]: h.get("snippet", "") for h in all_search_hits if "url" in h}
        sources_merged = []

        for item in scraped_sources:
            url = item["url"]
            snippet = url_to_snippet.get(url, "")
            sources_merged.append(
                {
                    "title": item.get("title") or "Source Document",
                    "url": url,
                    "snippet": snippet,
                    "content": item.get("content", ""),
                    "status": item.get("status", "unknown"),
                    "error": item.get("error"),
                }
            )

        return {
            "queries": queries,
            "search_hits": all_search_hits,
            "sources": sources_merged,
        }


class WriterAgent:
    """Agent 3: Invokes Google Gemini API to synthesize research into Markdown report."""

    def write_report(self, topic: str, research_data: dict[str, Any]) -> str:
        sources = research_data.get("sources", [])
        if not sources:
            raise RuntimeError("No source research context available to synthesize report.")

        formatted_chunks = []
        for idx, src in enumerate(sources, 1):
            if src.get("status") == "success" and src.get("content"):
                chunk = f"Source [{idx}]: {src['title']}\nURL: {src['url']}\nExtracted Content:\n{src['content'][:2500]}"
            else:
                chunk = f"Source [{idx}]: {src['title']}\nURL: {src['url']}\nSnippet:\n{src.get('snippet', '')}"
            formatted_chunks.append(chunk)

        combined_research = "\n\n---\n\n".join(formatted_chunks)

        # Calling services.generate_report (which strictly requires GOOGLE_API_KEY)
        return generate_report(topic, combined_research)


class AuditorAgent:
    """Agent 4: Validates output, computes reading metrics, citation links, and quality score."""

    def audit_report(self, report_md: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
        words = len(re.findall(r"\w+", report_md))
        est_read_time = max(1, round(words / 200, 1))

        successful_sources = [s for s in sources if s.get("status") == "success"]

        # Check how many URLs are cited in the report
        cited_urls = [s["url"] for s in sources if s.get("url") and s["url"] in report_md]

        # Calculate Quality Score out of 100
        score = 50  # Base
        if words > 300:
            score += 20
        if len(successful_sources) >= 2:
            score += 15
        if cited_urls:
            score += 15

        return {
            "word_count": words,
            "read_time_minutes": est_read_time,
            "total_sources_scraped": len(sources),
            "successful_sources": len(successful_sources),
            "cited_source_count": len(cited_urls),
            "quality_score": min(100, score),
            "audit_passed": words >= 150 and len(sources) >= 1,
        }
