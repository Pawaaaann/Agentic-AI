"""Report generation and safe local caching using Google Gemini API."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from threading import Lock

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
_cache_lock = Lock()

REPORT_PROMPT = """You are a Senior Principal AI Analyst. Synthesize the provided multi-source research into an EXHAUSTIVE, IN-DEPTH, and COMPREHENSIVE Markdown research report on: "{topic}".

DO NOT produce a short summary. Generate an extensive, thorough, and highly detailed report (at least 800-1500 words) containing deep technical analysis, key findings, comparative tables, strategic implications, and complete citations.

Your report MUST be written cleanly in Markdown with these structured sections:
# Comprehensive Research Report: {topic}

## 1. Executive Summary & Core Context
Elaborates on the background, primary significance, core concepts, and key developments surrounding {topic}.

## 2. In-Depth Technical & Domain Analysis
Detailed findings synthesized from all provided research. Use sub-sections (`### Key Aspect`), empirical details, statistics, and step-by-step breakdowns.

## 3. Comparative Analysis & Key Perspectives
Use Markdown comparison tables or structured bullet points to contrast technical approaches, market solutions, or trade-offs.

## 4. Challenges, Bottlenecks & Future Outlook
Identify key technical, operational, or industry challenges, followed by 3-5 year future projections and opportunities.

## 5. Primary Sources & Citations
List and hyperlink all referenced web sources using standard Markdown format `[Title](URL)`.

---
Research Context:
{research}
"""


def _cache_path() -> Path:
    directory = Path(os.getenv("CACHE_DIR", ".cache"))
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "reports.json"


def _load_cache() -> dict[str, str]:
    try:
        return json.loads(_cache_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _set_cache(key: str, value: str) -> None:
    with _cache_lock:
        cache = _load_cache()
        cache[key] = value
        _cache_path().write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def clear_cache() -> None:
    """Clear local report cache file."""
    with _cache_lock:
        path = _cache_path()
        if path.exists():
            try:
                path.unlink()
            except OSError as err:
                logger.warning("Failed to clear cache file: %s", err)


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def generate_report(topic: str, research: str) -> str:
    """Generate a Gemini report. Strictly requires GOOGLE_API_KEY."""
    max_chars = int(os.getenv("MAX_RESEARCH_CHARS", "32000"))
    research = _truncate(research, max_chars)

    cache_key = hashlib.sha256(f"{topic}\0{research}".encode()).hexdigest()
    if cached := _load_cache().get(cache_key):
        return cached

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not configured. Google Gemini API key is strictly required for report generation."
        )

    model = os.getenv("MODEL_NAME", "gemini-2.5-flash")
    prompt = REPORT_PROMPT.format(topic=topic, research=research)
    max_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "4096"))

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": max_tokens,
        },
    }

    if "2.5" in model:
        payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    try:
        response = requests.post(endpoint, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        report = "".join(part.get("text", "") for part in parts).strip()
        if not report:
            raise ValueError("Gemini API returned an empty response.")
    except (requests.RequestException, KeyError, IndexError, ValueError) as error:
        raise RuntimeError(f"Gemini API report generation failed: {error}") from error

    _set_cache(cache_key, report)
    return report



def answer_followup_question(
    topic: str,
    report_md: str,
    sources: list[dict[str, Any]],
    chat_history: list[dict[str, str]],
    user_question: str,
) -> str:
    """Answer interactive follow-up questions about research using Gemini API."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is missing. Configure it to use the AI chatbot.")

    model = os.getenv("MODEL_NAME", "gemini-2.5-flash")

    # Format source summary
    src_texts = []
    for s in sources[:5]:
        src_texts.append(f"- {s.get('title')}: {s.get('snippet', '')[:300]}")
    sources_summary = "\n".join(src_texts)

    system_instruction = (
        f"You are ResearchMind AI Assistant. The user is asking follow-up questions about the research topic: '{topic}'.\n"
        f"Synthesized Research Report Context:\n{report_md[:4000]}\n\n"
        f"Key Sources:\n{sources_summary}\n\n"
        "Provide direct, concise, factual, and helpful responses based on the research context."
    )

    contents = []
    # Build conversation history
    for msg in chat_history[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    # Add current question
    contents.append(
        {
            "role": "user",
            "parts": [
                {
                    "text": f"System context:\n{system_instruction}\n\nUser Question: {user_question}"
                }
            ],
        }
    )

    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 800},
    }
    if "2.5" in model:
        payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        ans = "".join(part.get("text", "") for part in parts).strip()
        return ans or "I couldn't generate a response based on the current context."
    except Exception as error:
        raise RuntimeError(f"Chatbot response failed: {error}") from error


