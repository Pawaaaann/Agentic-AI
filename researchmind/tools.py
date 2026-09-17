"""External research tools using Tavily API and concurrent web scraping."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()


def web_search(query: str, max_results: int | None = None) -> list[dict[str, str]]:
    """Execute search using Tavily API. Strictly requires TAVILY_API_KEY."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError(
            "TAVILY_API_KEY is not configured. Tavily API key is strictly required for research extraction."
        )

    limit = max_results if max_results is not None else int(os.getenv("TAVILY_MAX_RESULTS", "4"))
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=limit)
        results = response.get("results", [])
    except Exception as error:
        raise RuntimeError(f"Tavily search API request failed: {error}") from error

    processed = []
    snippet_limit = int(os.getenv("SNIPPET_MAX_CHARS", "400"))
    for item in results:
        processed.append(
            {
                "title": item.get("title", "Untitled Source"),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:snippet_limit],
            }
        )

    if not processed:
        raise RuntimeError(f"Tavily API search returned 0 results for query: '{query}'")

    return processed


def scrape_url(url: str, max_chars: int | None = None) -> dict[str, Any]:
    """Fetch a public HTTP(S) page and return cleaned main text and title."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {
            "url": url,
            "title": "Invalid URL",
            "content": "",
            "status": "error",
            "error": "Absolute HTTP(S) URL is required.",
        }

    char_limit = max_chars if max_chars is not None else int(os.getenv("MAX_SCRAPE_CHARS", "4000"))
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title_tag = soup.find("title")
        page_title = title_tag.get_text(strip=True) if title_tag else parsed.netloc

        # Remove irrelevant tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe", "svg"]):
            tag.decompose()

        main_text = soup.get_text(separator=" ", strip=True)
        # Normalize whitespace
        cleaned_text = " ".join(main_text.split())[:char_limit]

        return {
            "url": url,
            "title": page_title,
            "content": cleaned_text,
            "status": "success",
            "error": None,
        }
    except requests.RequestException as error:
        return {
            "url": url,
            "title": parsed.netloc,
            "content": "",
            "status": "error",
            "error": str(error),
        }


def scrape_urls_concurrent(urls: list[str], max_workers: int = 4) -> list[dict[str, Any]]:
    """Concurrently scrape multiple URLs using ThreadPoolExecutor."""
    if not urls:
        return []

    unique_urls = list(dict.fromkeys(urls))
    scraped_results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=min(len(unique_urls), max_workers)) as executor:
        future_to_url = {executor.submit(scrape_url, url): url for url in unique_urls}
        for future in as_completed(future_to_url):
            try:
                res = future.result()
                scraped_results.append(res)
            except Exception as exc:
                url = future_to_url[future]
                scraped_results.append(
                    {
                        "url": url,
                        "title": urlparse(url).netloc,
                        "content": "",
                        "status": "error",
                        "error": str(exc),
                    }
                )

    return scraped_results

