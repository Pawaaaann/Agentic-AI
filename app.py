"""Streamlit entry point for ResearchMind - Production Multi-Agent Research System."""

from __future__ import annotations

import json
import os
from urllib.parse import urlparse
import streamlit as st

from researchmind.pipeline import run_research_pipeline
from researchmind.services import clear_cache

# Page configuration
st.set_page_config(
    page_title="ResearchMind • Multi-Agent Autonomous AI Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Advanced CSS Design System
st.markdown(
    """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}
code, pre {
    font-family: 'JetBrains Mono', monospace !important;
}
.hero-container {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(124, 58, 237, 0.08) 100%);
    border: 1px solid rgba(124, 58, 237, 0.2);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
}
.hero-title {
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 50%, #db2777 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}
.hero-subtitle {
    font-size: 1.1rem;
    color: #64748b;
    margin-bottom: 1.25rem;
}
.agent-pill-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
}
.agent-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(203, 213, 225, 0.8);
    border-radius: 9999px;
    padding: 0.35rem 0.85rem;
    font-size: 0.85rem;
    font-weight: 600;
    color: #334155;
}
.metric-card-glow {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(226, 232, 240, 0.2);
    border-radius: 14px;
    padding: 1.25rem;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card-glow:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.1);
}
.metric-num {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-lbl {
    font-size: 0.8rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.25rem;
}
.source-card-modern {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(226, 232, 240, 0.15);
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 1rem;
}
.badge-success {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
}
.badge-error {
    background-color: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
}
.domain-code {
    background: rgba(37, 99, 235, 0.08);
    color: #2563eb;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    font-size: 0.8rem;
}
</style>""",
    unsafe_allow_html=True,
)

# Sidebar System Configuration & Status
with st.sidebar:
    st.markdown("### ⚡ ResearchMind Platform")
    st.caption("Enterprise Autonomous Multi-Agent AI System")
    st.markdown("---")

    st.subheader("🔑 API Service Credentials")
    tavily_key = os.getenv("TAVILY_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")

    col_api1, col_api2 = st.columns(2)
    with col_api1:
        if tavily_key:
            st.success("Tavily API\nConnected")
        else:
            st.error("Tavily API\nMissing")
    with col_api2:
        if google_key:
            st.success("Gemini API\nConnected")
        else:
            st.error("Gemini API\nMissing")

    st.markdown("---")
    st.subheader("⚙️ Autonomous Agent Controls")
    depth_option = st.radio(
        "Research Depth Strategy",
        options=["Fast", "Balanced", "Deep"],
        index=1,
        help="Fast (1-2 search queries), Balanced (3 search queries), Deep (4+ search queries & comprehensive analysis)",
    )

    st.markdown("---")
    st.subheader("🧹 System Maintenance")
    if st.button("Clear Report Cache", use_container_width=True):
        clear_cache()
        st.toast("Local report cache cleared successfully!", icon="🧹")

    st.markdown("---")
    st.caption("Engine: Tavily Search • Gemini AI • 4-Agent Pipeline")

# Hero Header Component
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">ResearchMind AI</div>
        <div class="hero-subtitle">High-efficiency, production-ready research platform orchestrated by 4 specialized autonomous AI agents.</div>
        <div class="agent-pill-container">
            <span class="agent-pill">🤖 <b>Agent 1:</b> Planner</span>
            <span class="agent-pill">🔍 <b>Agent 2:</b> Multi-Extractor</span>
            <span class="agent-pill">📝 <b>Agent 3:</b> Gemini Synthesizer</span>
            <span class="agent-pill">📊 <b>Agent 4:</b> Quality Auditor</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Topic Entry Bar
col_topic, col_submit = st.columns([4, 1])
with col_topic:
    topic_input = st.text_input(
        "Research Topic",
        placeholder="Enter research topic (e.g. Next-generation solid-state battery tech 2026)",
        label_visibility="collapsed",
    )
with col_submit:
    submit_btn = st.button("🚀 Start Research", type="primary", use_container_width=True)

# Main Research Handler
if submit_btn:
    if not topic_input.strip():
        st.warning("Please enter a research topic to proceed.")
    elif not tavily_key or not google_key:
        st.error(
            "Missing required API credentials. Ensure `TAVILY_API_KEY` and `GOOGLE_API_KEY` are set in `.env`."
        )
    else:
        try:
            status_box = st.status("Initializing Autonomous 4-Agent Pipeline...", expanded=True)

            def log_progress(message: str) -> None:
                status_box.write(message)

            results = run_research_pipeline(
                topic=topic_input.strip(), depth=depth_option, progress_callback=log_progress
            )
            st.session_state.results = results
            status_box.update(
                label="🎉 Multi-Agent Research Completed Successfully!", state="complete", expanded=False
            )
        except Exception as error:
            st.error(f"❌ Pipeline Execution Failed: {error}")

# Deliverables Dashboard Display
results = st.session_state.get("results")
if results:
    st.markdown("---")
    audit = results.get("audit", {})

    # Top Metric Dashboard Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="metric-card-glow"><div class="metric-num">{audit.get("total_sources_scraped", 0)}</div><div class="metric-lbl">Sources Analyzed</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card-glow"><div class="metric-num">{audit.get("word_count", 0)}</div><div class="metric-lbl">Report Words</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-card-glow"><div class="metric-num">{audit.get("read_time_minutes", 0)}m</div><div class="metric-lbl">Reading Time</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="metric-card-glow"><div class="metric-num">{audit.get("quality_score", 0)}/100</div><div class="metric-lbl">Audit Score</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("###")

    # Deliverables Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📄 Executive Report",
            "🤖 Agent Workflow Audit",
            "🌐 Source Matrix",
            "📊 Performance Analytics",
            "💾 Export Hub",
        ]
    )

    with tab1:
        st.markdown(results["writer"])

    with tab2:
        st.subheader("Agent 1: Planner Queries Formulated")
        for q in results.get("queries", []):
            st.info(f"🔎 Query: {q}")

        st.markdown("---")
        st.subheader("Agent 4: Auditor Verification Summary")
        col_aud1, col_aud2 = st.columns(2)
        with col_aud1:
            st.metric("Cited Sources in Report", audit.get("cited_source_count", 0))
            st.metric("Successful Web Scrapes", audit.get("successful_sources", 0))
        with col_aud2:
            st.metric("Audit Passed Status", "PASSED ✅" if audit.get("audit_passed") else "ATTENTION ⚠️")
            st.metric("Total Scraped Sources", audit.get("total_sources_scraped", 0))

    with tab3:
        st.subheader("Extracted Source Records")
        sources = results.get("sources", [])
        if not sources:
            st.info("No sources recorded.")
        else:
            for idx, src in enumerate(sources, 1):
                is_ok = src.get("status") == "success"
                badge_html = (
                    '<span class="badge-success">HTTP 200 SUCCESS</span>'
                    if is_ok
                    else '<span class="badge-error">FETCH ERROR</span>'
                )
                domain = urlparse(src.get("url", "")).netloc or "web"

                st.markdown(
                    f"""
                    <div class="source-card-modern">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <strong style="font-size: 1.05rem;">[{idx}] {src.get('title', 'Untitled')}</strong>
                            {badge_html}
                        </div>
                        <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 0.6rem;">
                            Domain: <span class="domain-code">{domain}</span> | <a href="{src.get('url')}" target="_blank">View Direct Source</a>
                        </div>
                        <div style="font-size: 0.9rem; color: #475569; font-style: italic;">
                            "{src.get('snippet', 'No snippet available.')[:280]}..."
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab4:
        st.subheader("System Performance & Audit Metadata")
        st.json(audit)

    with tab5:
        st.subheader("Export Final Research Deliverables")
        report_text = results["writer"]

        # Pre-compute HTML body replacement to avoid f-string backslash syntax errors in Python <3.12
        formatted_html_body = report_text.replace("\n", "<br>")

        json_export = json.dumps(results, indent=2, ensure_ascii=False)
        html_export = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Research Report - {results.get('topic')}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 850px; margin: 2rem auto; padding: 0 1.5rem; color: #1e293b; background: #f8fafc; }}
        h1, h2, h3 {{ color: #0f172a; }}
        code {{ background: #e2e8f0; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; }}
        a {{ color: #2563eb; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    {formatted_html_body}
</body>
</html>"""

        ex_col1, ex_col2, ex_col3 = st.columns(3)
        with ex_col1:
            st.download_button(
                "📥 Export Markdown (.md)",
                data=report_text,
                file_name=f"research_report_{results.get('topic', 'deliverable')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with ex_col2:
            st.download_button(
                "📥 Export JSON Data (.json)",
                data=json_export,
                file_name=f"research_data_{results.get('topic', 'deliverable')}.json",
                mime="application/json",
                use_container_width=True,
            )
        with ex_col3:
            st.download_button(
                "📥 Export Printable HTML (.html)",
                data=html_export,
                file_name=f"research_report_{results.get('topic', 'deliverable')}.html",
                mime="text/html",
                use_container_width=True,
            )


