from tools import web_search, scrape_url
from dotenv import load_dotenv
import os
import logging
import json
import time
import threading
import hashlib
import re
import requests

logging.basicConfig()
logger = logging.getLogger(__name__)

load_dotenv()

# ── Quota-friendly settings ───────────────────────────────────────────────────
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "1024"))
MAX_RESEARCH_CHARS = int(os.getenv("MAX_RESEARCH_CHARS", "900"))
MIN_REPORT_CHARS = int(os.getenv("MIN_REPORT_CHARS", "200"))
_MIN_INTERVAL = float(os.getenv("LLM_MIN_CALL_INTERVAL_SECONDS", "12"))
MODEL_NAME = os.getenv("MODEL_NAME") or "gemini-2.5-flash"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

CACHE_PATH = os.path.join(os.path.dirname(__file__), "llm_cache.json")
_cache_lock = threading.Lock()
_last_call_time = 0.0
_call_lock = threading.Lock()

REPORT_PROMPT = """Write a short research report on: {topic}

Sources:
{research}

Format (under 350 words):
## Introduction
## Key Findings
- 3 bullets
## Conclusion
## Sources"""


def _truncate_text(text: str, max_chars: int) -> str:
    if not text or len(text) <= max_chars:
        return text or ""
    return text[:max_chars].rsplit(" ", 1)[0] + "\n…"


def _stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _load_cache():
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache):
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        logger.debug("Failed to write cache", exc_info=True)


def _get_cached(key):
    return _load_cache().get(key)


def _set_cache(key, value):
    with _cache_lock:
        cache = _load_cache()
        cache[key] = {"value": value, "ts": int(time.time())}
        _save_cache(cache)


def _prepare_research(research: str) -> str:
    return _truncate_text(research, MAX_RESEARCH_CHARS)


def _is_valid_report(text: str) -> bool:
    """Reject truncated Gemini output (2.5-flash thinking can eat the token budget)."""
    if not text or len(text.strip()) < MIN_REPORT_CHARS:
        return False
    if text.count("##") < 2:
        return False
    return True


def _wait_for_rate_limit():
    """Space calls apart — free tier gemini-2.5-flash allows ~5/min."""
    global _last_call_time
    with _call_lock:
        now = time.time()
        wait = _MIN_INTERVAL - (now - _last_call_time)
        if wait > 0:
            time.sleep(wait)
        _last_call_time = time.time()


def _call_gemini_once(prompt: str) -> str:
    """Single REST call — no LangChain retries (each retry burns quota)."""
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY not set in .env")

    _wait_for_rate_limit()

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"
    )
    gen_config = {
        "temperature": 0,
        "maxOutputTokens": MAX_OUTPUT_TOKENS,
    }
    # gemini-2.5-* uses internal "thinking" tokens that count against maxOutputTokens
    if "2.5" in MODEL_NAME:
        gen_config["thinkingConfig"] = {"thinkingBudget": 0}

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_config,
    }
    resp = requests.post(url, json=payload, timeout=90)
    if resp.status_code != 200:
        err = resp.text[:400]
        raise RuntimeError(f"Gemini API {resp.status_code}: {err}")

    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")
    parts = candidates[0].get("content", {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError("Gemini returned empty text")
    return text


def _parse_search_blocks(research: str) -> list[dict]:
    blocks = []
    for chunk in research.split("----"):
        title = re.search(r"Title:\s*(.+)", chunk)
        url = re.search(r"URL:\s*(\S+)", chunk)
        snippet = re.search(r"Snippet:\s*(.+)", chunk, re.DOTALL)
        if title or snippet:
            blocks.append({
                "title": (title.group(1).strip() if title else "Source"),
                "url": (url.group(1).strip() if url else ""),
                "snippet": (snippet.group(1).strip() if snippet else ""),
            })
    return blocks[:5]


def build_fallback_report(topic: str, research: str) -> str:
    """No API call — builds a report from search/scrape data when quota is exhausted."""
    blocks = _parse_search_blocks(research)
    scraped = ""
    if "DETAILED SCRAPED CONTENT:" in research:
        scraped = research.split("DETAILED SCRAPED CONTENT:", 1)[-1].strip()
        scraped = _truncate_text(scraped, 600)

    lines = [
        f"# Research Report: {topic}",
        "",
        "> Generated from web search results (Gemini quota unavailable).",
        "",
        "## Introduction",
        f"This report summarizes publicly available information about **{topic}** "
        "gathered via automated web search and content extraction.",
        "",
        "## Key Findings",
    ]

    if blocks:
        for i, b in enumerate(blocks, 1):
            snippet = _truncate_text(b["snippet"], 200)
            lines.append(f"{i}. **{b['title']}** — {snippet}")
            if b["url"]:
                lines.append(f"   - Source: {b['url']}")
    elif scraped:
        lines.append(f"- {_truncate_text(scraped, 300)}")
    else:
        lines.append("- Limited source data was available for this topic.")

    lines += [
        "",
        "## Conclusion",
        f"Based on the collected sources, {topic} remains an active area of interest. "
        "Review the linked sources below for full details.",
        "",
        "## Sources",
    ]
    for b in blocks:
        if b["url"]:
            lines.append(f"- [{b['title']}]({b['url']})")
    if scraped and not blocks:
        lines.append("- Scraped web content (see raw reader output)")

    return "\n".join(lines)


def build_search_agent():
    return lambda query: web_search.invoke(query)


def build_reader_agent():
    return lambda url: scrape_url.invoke(url)


def generate_report(topic: str, research: str, force_refresh: bool = False) -> str:
    """Generate report with one Gemini call; falls back to search-based report on quota errors."""
    research = _prepare_research(research)
    key = f"report:{topic}:{_stable_hash(research)}"

    if not force_refresh:
        cached = _get_cached(key)
        if cached and _is_valid_report(cached["value"]):
            return cached["value"]

    prompt = REPORT_PROMPT.format(topic=topic, research=research)

    try:
        content = _call_gemini_once(prompt)
        if not _is_valid_report(content):
            logger.warning(
                "Gemini returned truncated report (%d chars), using fallback",
                len(content or ""),
            )
            fallback = build_fallback_report(topic, research)
            _set_cache(key, fallback)
            return fallback
        _set_cache(key, content)
        return content
    except Exception as e:
        logger.warning("Gemini call failed, using fallback report: %s", e)
        cached = _get_cached(key)
        if cached and _is_valid_report(cached["value"]):
            return cached["value"]
        fallback = build_fallback_report(topic, research)
        _set_cache(key, fallback)
        return fallback


# Legacy aliases — critic removed to save quota
def generate_report_and_critic(topic: str, research: str, force_refresh: bool = False):
    return generate_report(topic, research, force_refresh), ""


def generate_critic(report: str, force_refresh: bool = False) -> str:
    return ""
