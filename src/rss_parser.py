import feedparser
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class RSSParser:
    def __init__(self, rss_url: str):
        self.rss_url = rss_url

    def parse_feed(self) -> List[Dict]:
        """解析RSS源，返回最新条目"""
        try:
            feed = feedparser.parse(self.rss_url)

            if hasattr(feed, 'bozo_exception'):
                logger.error(f"RSS解析错误: {feed.bozo_exception}")
                return []

            if not feed.entries:
                logger.warning(f"RSS源 {self.rss_url} 没有任何条目")
                return []

            parsed_entries = []
            for entry in feed.entries:
                try:

                    title = entry.get('title', '无标题')
                    summary = entry.get('summary', '无摘要')

                    parsed_entry = {
                        'title': title,
                        'link': entry.get('link', ''),
                        'summary': summary,
                        'published': entry.get('published', '')
                    }
                    parsed_entries.append(parsed_entry)
                except Exception as e:
                    logger.error(f"解析单个条目失败: {e}")
                    continue

            return parsed_entries

        except Exception as e:
            logger.error(f"RSS解析失败: {e}")
            return []