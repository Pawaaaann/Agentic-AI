"""Orchestrates the 5-agent ResearchMind pipeline: Planner, Extractor, Writer, Auditor, and Fact-Checker."""

from __future__ import annotations

import time
from typing import Any, Callable

from .agents import AuditorAgent, ExtractorAgent, FactCheckerAgent, PlannerAgent, WriterAgent


def run_research_pipeline(
    topic: str, depth: str = "Balanced", progress_callback: Callable[[str], None] | None = None
) -> dict[str, Any]:
    """Execute the 5-agent research pipeline with node execution telemetry and fact verification.

    Args:
        topic: The target research topic string.
        depth: "Fast", "Balanced", or "Deep".
        progress_callback: Optional callable for UI progress updates.
    """
    def _notify(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    telemetry: list[dict[str, Any]] = []

    # 1. Agent 1: Planner Agent
    _notify("🤖 Agent 1 (Planner): Analyzing research topic and generating search queries...")
    t0 = time.perf_counter()
    planner = PlannerAgent()
    queries = planner.plan_research(topic, depth=depth)
    dt1 = round(time.perf_counter() - t0, 2)
    telemetry.append(
        {
            "agent_id": 1,
            "name": "Planner Agent",
            "icon": "🤖",
            "duration_sec": dt1,
            "status": "success",
            "summary": f"Generated {len(queries)} search queries",
        }
    )

    # 2. Agent 2: Extractor Agent
    _notify("🔍 Agent 2 (Extractor): Querying Tavily API and concurrently scraping web sources...")
    t0 = time.perf_counter()
    extractor = ExtractorAgent()
    max_results = 2 if depth == "Fast" else (3 if depth == "Balanced" else 4)
    extraction_data = extractor.extract_research(queries, max_results_per_query=max_results)
    dt2 = round(time.perf_counter() - t0, 2)
    sources = extraction_data["sources"]
    successful_sources = sum(1 for s in sources if s.get("status") == "success")
    telemetry.append(
        {
            "agent_id": 2,
            "name": "Extractor Agent",
            "icon": "🔍",
            "duration_sec": dt2,
            "status": "success",
            "summary": f"Scraped {len(sources)} sources ({successful_sources} HTTP 200)",
        }
    )

    # 3. Agent 3: Writer Agent
    _notify("📝 Agent 3 (Writer): Synthesizing multi-source context with Google Gemini API...")
    t0 = time.perf_counter()
    writer = WriterAgent()
    report_md = writer.write_report(topic, extraction_data)
    dt3 = round(time.perf_counter() - t0, 2)
    telemetry.append(
        {
            "agent_id": 3,
            "name": "Writer Agent",
            "icon": "📝",
            "duration_sec": dt3,
            "status": "success",
            "summary": f"Synthesized {len(report_md.split())} words via Gemini AI",
        }
    )

    # 4. Agent 4: Auditor Agent
    _notify("📊 Agent 4 (Auditor): Auditing report quality, metrics, and source citations...")
    t0 = time.perf_counter()
    auditor = AuditorAgent()
    audit_data = auditor.audit_report(report_md, sources)
    dt4 = round(time.perf_counter() - t0, 2)
    telemetry.append(
        {
            "agent_id": 4,
            "name": "Auditor Agent",
            "icon": "📊",
            "duration_sec": dt4,
            "status": "success",
            "summary": f"Quality score: {audit_data.get('quality_score')}/100",
        }
    )

    # 5. Agent 5: Fact-Checker Agent
    _notify("🛡️ Agent 5 (Fact-Checker): Cross-referencing claims against raw source text...")
    t0 = time.perf_counter()
    fact_checker = FactCheckerAgent()
    fact_check_data = fact_checker.verify_facts(report_md, sources)
    dt5 = round(time.perf_counter() - t0, 2)
    telemetry.append(
        {
            "agent_id": 5,
            "name": "Fact-Checker Agent",
            "icon": "🛡️",
            "duration_sec": dt5,
            "status": "success",
            "summary": f"Verifiability: {fact_check_data.get('verifiability_score')}%",
        }
    )

    _notify("✅ 5-Agent Pipeline Execution Complete!")

    # Format Mermaid DAG Flow Graph
    dag_mermaid = f"""graph LR
    A["🤖 1. Planner<br/>({len(queries)} queries, {dt1}s)"] --> B["🔍 2. Extractor<br/>({len(sources)} sources, {dt2}s)"]
    B --> C["📝 3. Writer<br/>(Gemini AI, {dt3}s)"]
    C --> D["📊 4. Auditor<br/>(Score: {audit_data.get('quality_score')}/100, {dt4}s)"]
    D --> E["🛡️ 5. Fact-Checker<br/>(Grounding: {fact_check_data.get('verifiability_score')}%, {dt5}s)"]
"""

    # Backwards-compatible search and reader strings
    search_lines = [
        f"Title: {hit.get('title')}\nURL: {hit.get('url')}\nSnippet: {hit.get('snippet')}\n"
        for hit in extraction_data.get("search_hits", [])
    ]
    search_summary = "\n----\n".join(search_lines)

    scraped_lines = [
        f"URL: {src.get('url')}\nStatus: {src.get('status')}\nText: {src.get('content', '')[:500]}\n"
        for src in sources
    ]
    scraped_summary = "\n----\n".join(scraped_lines)

    return {
        "topic": topic,
        "depth": depth,
        "queries": queries,
        "sources": sources,
        "writer": report_md,
        "audit": audit_data,
        "fact_check": fact_check_data,
        "telemetry": telemetry,
        "dag_mermaid": dag_mermaid,
        "search": search_summary,
        "reader": scraped_summary,
    }


