from __future__ import annotations

import requests


class SerpApiClient:
    def __init__(self, api_key: str, engine: str, gl: str, hl: str):
        self.api_key = api_key
        self.engine = engine
        self.gl = gl
        self.hl = hl

    def search_top_urls(self, query: str, top_n: int) -> list[str]:
        # SerpAPI endpoint
        url = "https://serpapi.com/search.json"
        params = {
            "api_key": self.api_key,
            "engine": self.engine,
            "q": query,
            "gl": self.gl,
            "hl": self.hl,
            "num": top_n,
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        urls: list[str] = []
        for item in data.get("organic_results", []) or []:
            link = item.get("link")
            if link and isinstance(link, str):
                urls.append(link)
            if len(urls) >= top_n:
                break

        # fallbacks (rare but safe)
        if len(urls) < top_n:
            for item in data.get("news_results", []) or []:
                link = item.get("link")
                if link and isinstance(link, str):
                    urls.append(link)
                if len(urls) >= top_n:
                    break

        # preserve order, de-dupe
        seen = set()
        deduped = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                deduped.append(u)

        return deduped[:top_n]
