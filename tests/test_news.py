import pytest
from unittest.mock import patch, MagicMock
from world_predictor.data.news import (
    NewsProcessor, NewsSource, NewsItem, NewsClassifier,
    VALID_CATEGORIES, SOURCE_PROFILES, _source_profile, RSS_FEEDS,
)


class TestNewsSource:
    def test_create_source(self):
        s = NewsSource("Reuters", 0.0, 0.92)
        assert s.name == "Reuters"
        assert s.politics == 0.0
        assert s.credibility == 0.92


class TestNewsItem:
    def test_create_item(self):
        source = NewsSource("BBC", -0.1, 0.88)
        item = NewsItem(
            title="Test headline",
            source=source,
            category="POLITICAL",
            content="Some content",
            url="https://example.com",
            region="US",
            impact=0.7,
        )
        assert item.title == "Test headline"
        assert item.category == "POLITICAL"
        assert item.impact == 0.7
        assert item.timestamp is not None

    def test_invalid_category_defaults_to_general(self):
        source = NewsSource("Test", 0.0, 0.5)
        item = NewsItem("Title", source, "INVALID_CAT", "", "", "Global", 0.5)
        assert item.category == "GENERAL"

    def test_impact_clamped(self):
        source = NewsSource("Test", 0.0, 0.5)
        item_high = NewsItem("Title", source, "GENERAL", "", "", "Global", 1.5)
        item_low = NewsItem("Title", source, "GENERAL", "", "", "Global", -0.5)
        assert item_high.impact == 1.0
        assert item_low.impact == 0.0


class TestSourceProfiles:
    def test_known_sources_have_profiles(self):
        assert "reuters" in SOURCE_PROFILES
        assert "bbc news" in SOURCE_PROFILES
        assert "fox news" in SOURCE_PROFILES

    def test_source_profile_lookup(self):
        profile = _source_profile("Reuters")
        assert profile["credibility"] == 0.92
        assert profile["politics"] == 0.0

    def test_unknown_source_returns_default(self):
        profile = _source_profile("Unknown Newspaper XYZ")
        assert profile["credibility"] == 0.5
        assert profile["politics"] == 0.0

    def test_case_insensitive(self):
        p1 = _source_profile("BBC News")
        p2 = _source_profile("bbc news")
        assert p1 == p2


class TestNewsProcessorDedup:
    def test_dedup_removes_duplicates(self):
        proc = NewsProcessor(newsapi_key="", anthropic_key="")
        items = [
            {"title": "Same headline", "snippet": "content a"},
            {"title": "Same headline", "snippet": "content b"},
            {"title": "Different headline", "snippet": "content c"},
        ]
        result = proc._dedup(items)
        assert len(result) == 2

    def test_dedup_removes_empty_titles(self):
        proc = NewsProcessor(newsapi_key="", anthropic_key="")
        items = [
            {"title": "", "snippet": "no title"},
            {"title": "[Removed]", "snippet": "removed article"},
            {"title": "Valid title", "snippet": "good"},
        ]
        result = proc._dedup(items)
        assert len(result) == 1
        assert result[0]["title"] == "Valid title"

    def test_dedup_case_insensitive(self):
        proc = NewsProcessor(newsapi_key="", anthropic_key="")
        items = [
            {"title": "Breaking News Today", "snippet": "a"},
            {"title": "breaking news today", "snippet": "b"},
        ]
        result = proc._dedup(items)
        assert len(result) == 1


class TestNewsClassifier:
    def test_not_available_without_key(self):
        c = NewsClassifier(api_key="")
        assert not c.available

    def test_available_with_key(self):
        c = NewsClassifier(api_key="test-key")
        assert c.available

    def test_classify_batch_fallback_on_error(self):
        """When Claude API fails, should return GENERAL for all items."""
        c = NewsClassifier(api_key="invalid-key")
        items = [{"title": "Test", "snippet": "content"}]
        # Mock the internal _client to raise
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API error")
        c._client = mock_client
        results = c.classify_batch(items)
        assert len(results) == 1
        assert results[0]["category"] == "GENERAL"

    def test_classify_empty_list(self):
        c = NewsClassifier(api_key="")
        assert c.classify_batch([]) == []


class TestNewsProcessorClassifyAndBuild:
    def test_build_without_api_key(self):
        """Without Anthropic key, all items should be GENERAL."""
        proc = NewsProcessor(newsapi_key="", anthropic_key="")
        raw = [
            {"title": "Headline 1", "snippet": "Content", "content": "Full", "url": "http://a.com", "source_name": "Reuters"},
            {"title": "Headline 2", "snippet": "Content", "content": "Full", "url": "http://b.com", "source_name": "BBC News"},
        ]
        items = proc._classify_and_build(raw)
        assert len(items) == 2
        assert all(item.category == "GENERAL" for item in items)
        # Source profiles should be applied
        assert items[0].source.credibility == 0.92  # Reuters
        assert items[1].source.credibility == 0.88  # BBC


class TestRSSFeedConfig:
    def test_rss_feeds_have_required_fields(self):
        for feed in RSS_FEEDS:
            assert "url" in feed
            assert "name" in feed
            assert feed["url"].startswith("http")


class TestValidCategories:
    def test_all_categories_present(self):
        expected = {"ECONOMIC_POLICY", "POLITICAL", "SOCIAL", "MILITARY",
                    "TECHNOLOGY", "ENVIRONMENTAL", "HEALTH", "TRADE", "GENERAL"}
        assert set(VALID_CATEGORIES) == expected
