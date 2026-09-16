"""Fetch fresh AI news from Tavily across several themed queries."""

import logging
from urllib.parse import urlparse

from tavily import TavilyClient

try:
    from . import config
except ImportError:  # pragma: no cover - supports the flat-file layout used here.
    import config

log = logging.getLogger(__name__)


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _normalize(result: dict, query: str) -> dict:
    return {
        "title": (result.get("title") or "").strip(),
        "url": (result.get("url") or "").strip(),
        "content": (result.get("content") or "").strip(),
        "published": result.get("published_date") or "",
        "score": float(result.get("score") or 0.0),
        "source": _domain(result.get("url") or ""),
        "query": query,
    }


def fetch_news() -> list[dict]:
    """Run every configured query and return a deduplicated, ranked story list."""
    client = TavilyClient(api_key=config.TAVILY_API_KEY)
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    stories: list[dict] = []

    for query in config.SEARCH_QUERIES:
        try:
            response = client.search(
                query=query,
                topic="news",
                days=config.LOOKBACK_DAYS,
                max_results=config.RESULTS_PER_QUERY,
                search_depth="advanced",
                include_answer=False,
            )
        except Exception as exc:
            log.warning("Tavily query failed (%s): %s", query, exc)
            continue

        for raw in response.get("results", []):
            story = _normalize(raw, query)

            if not story["title"] or not story["url"]:
                continue
            if story["source"] in config.BLOCKED_DOMAINS:
                continue
            if story["url"] in seen_urls:
                continue

            # Cheap near-duplicate check: same story, different outlet wording.
            title_key = "".join(c for c in story["title"].lower() if c.isalnum())[:60]
            if title_key in seen_titles:
                continue

            seen_urls.add(story["url"])
            seen_titles.add(title_key)
            stories.append(story)

        log.info("Query '%s' -> %d unique stories so far", query, len(stories))

    stories.sort(key=lambda s: s["score"], reverse=True)
    trimmed = stories[: config.MAX_STORIES_IN_EMAIL]
    log.info("Collected %d stories, keeping top %d", len(stories), len(trimmed))
    return trimmed
