"""Orchestrates the 4-agent ResearchMind pipeline: Planner, Extractor, Writer, and Auditor."""

from __future__ import annotations

from typing import Any, Callable

from .agents import AuditorAgent, ExtractorAgent, PlannerAgent, WriterAgent


def run_research_pipeline(
    topic: str, depth: str = "Balanced", progress_callback: Callable[[str], None] | None = None
) -> dict[str, Any]:
    """Execute the multi-agent research pipeline using strict API calls.

    Args:
        topic: The target research topic string.
        depth: "Fast", "Balanced", or "Deep".
        progress_callback: Optional callable for UI progress updates.
    """
    def _notify(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    # 1. Agent 1: Planner Agent
    _notify("🤖 Agent 1 (Planner): Analyzing research topic and generating search queries...")
    planner = PlannerAgent()
    queries = planner.plan_research(topic, depth=depth)

    # 2. Agent 2: Extractor Agent
    _notify("🔍 Agent 2 (Extractor): Querying Tavily API and concurrently scraping web sources...")
    extractor = ExtractorAgent()
    max_results = 2 if depth == "Fast" else (3 if depth == "Balanced" else 4)
    extraction_data = extractor.extract_research(queries, max_results_per_query=max_results)

    # 3. Agent 3: Writer Agent
    _notify("📝 Agent 3 (Writer): Synthesizing multi-source context with Google Gemini API...")
    writer = WriterAgent()
    report_md = writer.write_report(topic, extraction_data)

    # 4. Agent 4: Auditor Agent
    _notify("📊 Agent 4 (Auditor): Auditing report quality, metrics, and source citations...")
    auditor = AuditorAgent()
    audit_data = auditor.audit_report(report_md, extraction_data["sources"])

    _notify("✅ Pipeline Complete!")

    # Format backwards-compatible search and reader strings
    search_lines = []
    for hit in extraction_data.get("search_hits", []):
        search_lines.append(f"Title: {hit.get('title')}\nURL: {hit.get('url')}\nSnippet: {hit.get('snippet')}\n")
    search_summary = "\n----\n".join(search_lines)

    scraped_lines = []
    for src in extraction_data.get("sources", []):
        status = src.get("status", "unknown")
        scraped_lines.append(f"URL: {src.get('url')}\nStatus: {status}\nText: {src.get('content', '')[:500]}\n")
    scraped_summary = "\n----\n".join(scraped_lines)

    return {
        "topic": topic,
        "depth": depth,
        "queries": queries,
        "sources": extraction_data["sources"],
        "writer": report_md,
        "audit": audit_data,
        "search": search_summary,
        "reader": scraped_summary,
    }

