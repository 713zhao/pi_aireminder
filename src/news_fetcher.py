"""
News Fetcher Module
Fetches and manages news from RSS feeds
"""
import feedparser
import logging
from typing import List, Dict
from datetime import datetime
from dataclasses import dataclass


@dataclass
class NewsItem:
    """Represents a news article"""
    title: str
    description: str
    link: str
    published: datetime
    source: str
    
    def __str__(self):
        return f"{self.source}: {self.title}"


class NewsFetcher:
    """Fetches news from RSS feeds"""
    
    # Default RSS feeds (fallback if not in config)
    DEFAULT_FEEDS = {
        "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
        "CNN": "http://rss.cnn.com/rss/edition.rss",
        "Reuters": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        "TechCrunch": "https://techcrunch.com/feed/",
        "The Guardian": "https://www.theguardian.com/world/rss",
    }
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(__name__)
        
        # Load feeds from config or use defaults
        if config and 'news' in config:
            news_config = config['news']
            self.feeds = news_config.get('feeds', self.DEFAULT_FEEDS)
            self.max_items_per_feed = news_config.get('max_items_per_feed', 5)
        else:
            self.feeds = self.DEFAULT_FEEDS
            self.max_items_per_feed = 5
        
        self.news_items: List[NewsItem] = []
        self.logger.info(f"Initialized NewsFetcher with {len(self.feeds)} feeds")
        
    def fetch_news(self, max_items_per_feed: int = None) -> List[NewsItem]:
        """Fetch news from all configured RSS feeds"""
        if max_items_per_feed is None:
            max_items_per_feed = self.max_items_per_feed
        
        self.news_items = []
        
        for source_name, feed_url in self.feeds.items():
            try:
                self.logger.info(f"Fetching news from {source_name}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:max_items_per_feed]:
                    try:
                        # Parse published date
                        published = datetime.now()
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published = datetime(*entry.published_parsed[:6])
                        
                        # Get description (summary or content)
                        description = ""
                        if hasattr(entry, 'summary'):
                            description = entry.summary
                        elif hasattr(entry, 'description'):
                            description = entry.description
                        
                        # Clean HTML tags from description
                        description = self._clean_html(description)
                        
                        news_item = NewsItem(
                            title=entry.title,
                            description=description,
                            link=entry.link,
                            published=published,
                            source=source_name
                        )
                        
                        self.news_items.append(news_item)
                        
                    except Exception as e:
                        self.logger.error(f"Error parsing entry from {source_name}: {e}")
                        continue
                
                self.logger.info(f"Fetched {len(self.news_items)} items from {source_name}")
                
            except Exception as e:
                self.logger.error(f"Error fetching from {source_name}: {e}")
                continue
        
        # Sort by published date (newest first)
        self.news_items.sort(key=lambda x: x.published, reverse=True)
        
        self.logger.info(f"Total news items fetched: {len(self.news_items)}")
        return self.news_items
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        import html
        text = html.unescape(text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def get_news_items(self) -> List[NewsItem]:
        """Get cached news items"""
        return self.news_items


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("RSS News Fetcher Test")
    print("="*60)
    
    fetcher = NewsFetcher()
    news = fetcher.fetch_news(max_items_per_feed=3)
    
    print(f"\nFetched {len(news)} news items:\n")
    
    for i, item in enumerate(news[:10], 1):
        print(f"{i}. [{item.source}] {item.title}")
        print(f"   {item.description[:100]}...")
        print(f"   Published: {item.published.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Link: {item.link}")
        print()
