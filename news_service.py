from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import requests


NEWS_SOURCES = [
    {
        "name": "CNBC Top News",
        "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    },
    {
        "name": "CNBC World News",
        "url": "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    },
    {
        "name": "Morgan Stanley Insights",
        "url": "https://www.morganstanley.com/ideas/rss",
    },
    {
        "name": "Investing.com Stock News",
        "url": "https://www.investing.com/rss/news_25.rss",
    },
]


def _score_sentiment(text: str) -> str:
    lower = text.lower()
    positive = ["增长", "盈利", "突破", "合作", "上涨", "创新高", "获批", "positive", "beat"]
    negative = ["下滑", "亏损", "裁员", "下跌", "风险", "诉讼", "处罚", "negative", "miss"]

    pos = sum(1 for word in positive if word in lower)
    neg = sum(1 for word in negative if word in lower)
    if pos > neg:
        return "利好"
    if neg > pos:
        return "利空"
    return "中性"


def _fetch_rss_items(rss_url: str, source_name: str, timeout: int = 15) -> list[dict]:
    resp = requests.get(rss_url, timeout=timeout)
    resp.raise_for_status()
    root = ElementTree.fromstring(resp.content)
    items = root.findall("./channel/item")

    result = []
    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date_raw = (item.findtext("pubDate") or "").strip()
        source = source_name
        source_node = item.find("source")
        if source_node is not None and source_node.text:
            source = source_node.text.strip()

        published_at = pub_date_raw
        if pub_date_raw:
            try:
                dt = parsedate_to_datetime(pub_date_raw).astimezone()
                published_at = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                published_at = pub_date_raw

        sentiment = _score_sentiment(title)
        result.append(
            {
                "title": title,
                "url": link,
                "source": source,
                "published_at": published_at,
                "sentiment": sentiment,
                "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return result


def fetch_news(query: str, limit: int = 12) -> list[dict]:
    keywords = [k.strip().lower() for k in query.replace("OR", ",").split(",") if k.strip()]
    aggregated: list[dict] = []

    # Curated sources only: CNBC + Morgan Stanley + Investing.com.
    for source in NEWS_SOURCES:
        try:
            aggregated.extend(_fetch_rss_items(source["url"], source["name"]))
        except Exception:
            continue

    # Deduplicate by URL then title.
    dedup = {}
    for item in aggregated:
        key = item["url"] or item["title"]
        if key and key not in dedup:
            dedup[key] = item

    dedup_list = list(dedup.values())

    # Keyword focus to keep results relevant.
    if keywords:
        filtered = [
            item
            for item in dedup_list
            if any(k in (item["title"] + " " + item.get("source", "")).lower() for k in keywords)
        ]
        if filtered:
            dedup_list = filtered

    # Sort by published time (best effort).
    def _sort_key(item: dict) -> str:
        return item.get("published_at", "")

    dedup_list.sort(key=_sort_key, reverse=True)
    result = dedup_list[:limit]
    return result
