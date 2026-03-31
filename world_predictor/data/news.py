import os
import json
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Optional

import requests
import feedparser
import anthropic

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

VALID_CATEGORIES = [
    "ECONOMIC_POLICY", "POLITICAL", "SOCIAL", "MILITARY",
    "TECHNOLOGY", "ENVIRONMENTAL", "HEALTH", "TRADE", "GENERAL",
]


class NewsSource:
    def __init__(self, name: str, politics: float, credibility: float):
        self.name = name
        self.politics = politics   # -1 (left) to 1 (right)
        self.credibility = credibility  # 0 to 1


class NewsItem:
    def __init__(self, title: str, source: NewsSource, category: str,
                 content: str, url: str, region: str, impact: float):
        self.title = title
        self.source = source
        self.category = category if category in VALID_CATEGORIES else "GENERAL"
        self.content = content
        self.url = url
        self.region = region
        self.impact = max(0.0, min(1.0, impact))
        self.timestamp = datetime.now()


# ---------------------------------------------------------------------------
# Known source metadata (politics bias + credibility)
# ---------------------------------------------------------------------------

SOURCE_PROFILES: Dict[str, Dict] = {
    # Neutral / wire services
    "reuters":      {"politics": 0.0,  "credibility": 0.92},
    "associated press": {"politics": 0.0, "credibility": 0.90},
    # Slight left
    "bbc news":     {"politics": -0.1, "credibility": 0.88},
    "bbc":          {"politics": -0.1, "credibility": 0.88},
    "the guardian":  {"politics": -0.3, "credibility": 0.82},
    "cnn":          {"politics": -0.25, "credibility": 0.78},
    "al jazeera":   {"politics": -0.15, "credibility": 0.80},
    "nbc news":     {"politics": -0.2, "credibility": 0.78},
    # Slight right
    "cnbc":         {"politics": 0.1,  "credibility": 0.84},
    "the wall street journal": {"politics": 0.15, "credibility": 0.88},
    "fox news":     {"politics": 0.55, "credibility": 0.65},
    # International
    "dw news":      {"politics": 0.0,  "credibility": 0.85},
    "france 24":    {"politics": -0.05, "credibility": 0.83},
    "nhk world":    {"politics": 0.0,  "credibility": 0.85},
}

_DEFAULT_PROFILE = {"politics": 0.0, "credibility": 0.5}


def _source_profile(name: str) -> Dict:
    """Look up source bias/credibility, case-insensitive."""
    return SOURCE_PROFILES.get(name.lower().strip(), _DEFAULT_PROFILE)


# ---------------------------------------------------------------------------
# RSS feed URLs (fallback)
# ---------------------------------------------------------------------------

RSS_FEEDS = [
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "name": "BBC News"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "name": "Al Jazeera"},
    {"url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "name": "CNBC"},
    {"url": "https://rss.dw.com/rdf/rss-en-world", "name": "DW News"},
    {"url": "https://www3.nhk.or.jp/rss/news/cat0.xml", "name": "NHK World"},
]


# ---------------------------------------------------------------------------
# Claude News Classifier
# ---------------------------------------------------------------------------

_CLASSIFY_PROMPT = """You are a news classification engine for a geopolitical simulation.

For each news headline + snippet below, return a JSON array where each element has:
- "category": one of {categories}
- "impact": float 0.0-1.0 (how significant is this for global/regional stability)
- "region": ISO 3166-1 alpha-2 country code most affected, or "Global"

Rules:
- ECONOMIC_POLICY: fiscal, monetary, GDP, employment, inflation, central bank
- POLITICAL: elections, legislation, diplomacy, sanctions, government changes
- SOCIAL: protests, demographics, migration, culture, inequality, education
- MILITARY: armed conflict, defense, arms deals, NATO, military exercises
- TECHNOLOGY: AI, cyber, space, semiconductors, tech regulation
- ENVIRONMENTAL: climate, disasters, energy transition, pollution
- HEALTH: pandemics, healthcare policy, drug approvals, WHO
- TRADE: tariffs, trade deals, supply chain, imports/exports
- GENERAL: anything else

Respond with ONLY the JSON array, no markdown fences or extra text.

News items:
{items_json}"""


class NewsClassifier:
    """Classify news items using Claude API."""

    def __init__(self, api_key: Optional[str] = None, batch_size: int = 10):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.batch_size = batch_size
        self._client: Optional[anthropic.Anthropic] = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def classify_batch(self, items: List[Dict[str, str]]) -> List[Dict]:
        """Classify a batch of {"title": ..., "snippet": ...} dicts.

        Returns list of {"category", "impact", "region"} in same order.
        """
        if not items:
            return []

        items_json = json.dumps(
            [{"index": i, "title": it["title"], "snippet": it.get("snippet", "")[:300]}
             for i, it in enumerate(items)],
            ensure_ascii=False,
        )

        prompt = _CLASSIFY_PROMPT.format(
            categories=", ".join(VALID_CATEGORIES),
            items_json=items_json,
        )

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            results = json.loads(raw)
            if isinstance(results, list) and len(results) == len(items):
                return results
        except Exception as e:
            logger.warning("Claude classification failed: %s", e)

        # Fallback: return GENERAL for everything
        return [{"category": "GENERAL", "impact": 0.3, "region": "Global"}] * len(items)

    def classify_items(self, items: List[Dict[str, str]]) -> List[Dict]:
        """Classify items in batches."""
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i : i + self.batch_size]
            results.extend(self.classify_batch(batch))
        return results


# ---------------------------------------------------------------------------
# NewsProcessor — main orchestrator
# ---------------------------------------------------------------------------

class NewsProcessor:
    def __init__(self, newsapi_key: Optional[str] = None, anthropic_key: Optional[str] = None):
        self.newsapi_key = newsapi_key or os.environ.get("NEWSAPI_KEY", "")
        self.classifier = NewsClassifier(api_key=anthropic_key)
        self.processed_news: List[NewsItem] = []
        self._seen_hashes: set = set()  # dedup by title hash

    # ---- Public API ----

    def fetch_daily_news(self) -> List[NewsItem]:
        """Fetch news from NewsAPI (primary) + RSS (fallback), classify via Claude."""
        raw_items: List[Dict] = []

        # 1) Try NewsAPI
        if self.newsapi_key:
            try:
                raw_items = self._fetch_newsapi()
                logger.info("NewsAPI returned %d items", len(raw_items))
            except Exception as e:
                logger.warning("NewsAPI failed, falling back to RSS: %s", e)

        # 2) Always supplement with RSS
        try:
            rss_items = self._fetch_rss()
            logger.info("RSS returned %d items", len(rss_items))
            raw_items.extend(rss_items)
        except Exception as e:
            logger.warning("RSS fetch failed: %s", e)

        # 3) Dedup
        raw_items = self._dedup(raw_items)
        if not raw_items:
            logger.warning("No news items fetched")
            return []

        # 4) Classify
        news_items = self._classify_and_build(raw_items)
        self.processed_news.extend(news_items)
        return news_items

    def categorize_news(self, news_items: List[NewsItem]) -> Dict[str, List[NewsItem]]:
        """Group news items by category."""
        categories: Dict[str, List[NewsItem]] = {}
        for news in news_items:
            categories.setdefault(news.category, []).append(news)
        return categories

    # ---- NewsAPI ----

    def _fetch_newsapi(self) -> List[Dict]:
        """Fetch from NewsAPI.org top-headlines endpoint."""
        url = "https://newsapi.org/v2/top-headlines"
        items = []

        for category in ["business", "technology", "science", "health", "general"]:
            resp = requests.get(url, params={
                "apiKey": self.newsapi_key,
                "language": "en",
                "category": category,
                "pageSize": 20,
            }, timeout=15)

            if resp.status_code == 426 or resp.status_code == 429:
                logger.warning("NewsAPI rate limited (status %d)", resp.status_code)
                break

            resp.raise_for_status()
            data = resp.json()

            for article in data.get("articles", []):
                source_name = (article.get("source") or {}).get("name", "Unknown")
                items.append({
                    "title": article.get("title", ""),
                    "snippet": article.get("description", "") or "",
                    "content": article.get("content", "") or "",
                    "url": article.get("url", ""),
                    "source_name": source_name,
                    "published_at": article.get("publishedAt", ""),
                })

        return items

    # ---- RSS ----

    def _fetch_rss(self) -> List[Dict]:
        """Fetch from RSS feeds."""
        items = []
        for feed_info in RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_info["url"])
                for entry in feed.entries[:15]:
                    items.append({
                        "title": entry.get("title", ""),
                        "snippet": entry.get("summary", "")[:500],
                        "content": entry.get("summary", ""),
                        "url": entry.get("link", ""),
                        "source_name": feed_info["name"],
                        "published_at": entry.get("published", ""),
                    })
            except Exception as e:
                logger.warning("RSS feed %s failed: %s", feed_info["name"], e)
        return items

    # ---- Dedup ----

    def _dedup(self, items: List[Dict]) -> List[Dict]:
        """Remove duplicates by title hash."""
        unique = []
        for item in items:
            title = (item.get("title") or "").strip()
            if not title or title == "[Removed]":
                continue
            h = hashlib.md5(title.lower().encode()).hexdigest()
            if h not in self._seen_hashes:
                self._seen_hashes.add(h)
                unique.append(item)
        return unique

    # ---- Classification + build ----

    def _classify_and_build(self, raw_items: List[Dict]) -> List[NewsItem]:
        """Classify raw items via Claude and build NewsItem objects."""
        # Prepare for classification
        to_classify = [{"title": it["title"], "snippet": it.get("snippet", "")} for it in raw_items]

        if self.classifier.available:
            classifications = self.classifier.classify_items(to_classify)
        else:
            logger.info("No ANTHROPIC_API_KEY — skipping classification, using GENERAL")
            classifications = [{"category": "GENERAL", "impact": 0.3, "region": "Global"}] * len(raw_items)

        # Build NewsItem objects
        news_items = []
        for raw, cls in zip(raw_items, classifications):
            profile = _source_profile(raw.get("source_name", ""))
            source = NewsSource(
                name=raw.get("source_name", "Unknown"),
                politics=profile["politics"],
                credibility=profile["credibility"],
            )
            item = NewsItem(
                title=raw["title"],
                source=source,
                category=cls.get("category", "GENERAL"),
                content=raw.get("content", "") or raw.get("snippet", ""),
                url=raw.get("url", ""),
                region=cls.get("region", "Global"),
                impact=float(cls.get("impact", 0.3)),
            )
            news_items.append(item)

        return news_items
