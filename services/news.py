from services.cache import ttl_cache
import feedparser

FEEDS = [
    "https://www.interfax.ru/rss.asp",  # Интерфакс
    "https://tass.ru/rss/v2.xml",       # ТАСС
]

@ttl_cache(600)
def get_headlines(limit=10):
    items = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries[: limit // len(FEEDS) + 2]:
            items.append({
                "title": e.get("title"),
                "link": e.get("link"),
                "published": e.get("published"),
                "source": feed.feed.get("title", "RSS"),
            })
    # обрежем общий список

    return items[:limit]
