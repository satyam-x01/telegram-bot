import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger("WhatsAppBot.Searcher")

class LiveWebSearcher:
    """Live web searcher powered by DuckDuckGo (ddgs) to fetch fresh, real-time information."""

    def __init__(self):
        pass

    def search(self, query: str, max_results: int = 6) -> List[Dict[str, str]]:
        """Perform a live web search and return clean, ad-free search results."""
        from modules.url_sanitizer import sanitize_url, is_ad_or_tracking_url, unwrap_redirect
        results = []
        raw_items = []
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                raw_items = list(ddgs.text(query, max_results=max_results + 4))
        except Exception as e:
            try:
                from duckduckgo_search import DDGS as FallbackDDGS
                with FallbackDDGS() as ddgs:
                    raw_items = list(ddgs.text(query, max_results=max_results + 4))
            except Exception as e2:
                logger.error(f"Search failed for '{query}': {e2}")

        for r in raw_items:
            href = r.get("href", "") or ""
            unwrapped = unwrap_redirect(href)
            clean_link = sanitize_url(unwrapped)
            if not clean_link or is_ad_or_tracking_url(unwrapped) or is_ad_or_tracking_url(href):
                continue
            title = r.get("title", "").strip()
            snippet = r.get("body", "").strip()
            if title and clean_link:
                results.append({
                    "title": title,
                    "link": clean_link,
                    "snippet": snippet
                })
            if len(results) >= max_results:
                break

        return results

    def search_trending_category(self, category_name: str, topic: str) -> List[Dict[str, str]]:
        """Search for trending, new, or interesting items for a given category topic."""
        # Query attempts from specific to broad
        queries = [
            f"{topic} trending github",
            f"best new {topic}",
            topic
        ]
        for q in queries:
            logger.info(f"Performing live web search for: '{q}'")
            res = self.search(q, max_results=5)
            if res:
                return res
        return []

live_searcher = LiveWebSearcher()
