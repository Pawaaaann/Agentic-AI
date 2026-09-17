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

REPORT_PROMPT = """You are an expert AI Research Analyst. Synthesize the provided multi-source research into a comprehensive, highly accurate, and objective Markdown research report on the topic: "{topic}".

Your report MUST be written cleanly in Markdown and include the following sections:
# Research Report: {topic}

## Executive Summary
Provide a high-level overview summarizing the core findings and context.

## Key Findings & Detailed Analysis
Detailed findings synthesized from the research context. Use bullet points, comparison tables, or clear sub-headings where appropriate.

## Strategic Implications & Insights
Discuss broader consequences, technical or industry impacts, or future outlook.

## Key Sources & Citations
List and link all primary web sources provided in the research context using standard Markdown format `[Title](URL)`.

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
    max_chars = int(os.getenv("MAX_RESEARCH_CHARS", "16000"))
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
    max_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))

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
        response = requests.post(endpoint, json=payload, timeout=60)
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

