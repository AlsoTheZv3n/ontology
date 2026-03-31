"""Map raw HN RSS entries to ArticleObject."""

from __future__ import annotations

import hashlib

from schemas.objects import ArticleObject


class ArticleMapper:
    def from_hn(self, raw: dict) -> ArticleObject:
        url = raw.get("url", "")
        key = hashlib.md5(url.encode()).hexdigest()[:12]
        return ArticleObject(
            key=key,
            properties={
                "title": raw.get("title"),
                "url": url,
                "published": raw.get("published"),
                "hn_score": raw.get("score", 0),
                "hn_comments": raw.get("comments", 0),
                "source": "hackernews",
            },
            sources={"hn_rss": raw},
        )
