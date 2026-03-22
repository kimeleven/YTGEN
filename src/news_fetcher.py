"""
Google News RSS로 AI 최신 뉴스를 수집한다.
처리된 뉴스는 SQLite DB(src/db.py)로 관리해 중복을 방지한다.
"""
import re
import xml.etree.ElementTree as ET

import requests

# ── RSS 소스 (AI 주요 키워드별) ────────────────────────────────────────────────
_RSS_SOURCES = [
    ("OpenAI",  "https://news.google.com/rss/search?q=OpenAI+ChatGPT&hl=ko&gl=KR&ceid=KR:ko"),
    ("Claude",  "https://news.google.com/rss/search?q=Anthropic+Claude+AI&hl=ko&gl=KR&ceid=KR:ko"),
    ("Gemini",  "https://news.google.com/rss/search?q=Google+Gemini+AI&hl=ko&gl=KR&ceid=KR:ko"),
    ("Grok",    "https://news.google.com/rss/search?q=xAI+Grok+Elon&hl=ko&gl=KR&ceid=KR:ko"),
    ("AI뉴스",  "https://news.google.com/rss/search?q=인공지능+AI+뉴스&hl=ko&gl=KR&ceid=KR:ko"),
    ("LLM",     "https://news.google.com/rss/search?q=LLM+대형언어모델&hl=ko&gl=KR&ceid=KR:ko"),
]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _parse_feed(source_name: str, rss_url: str) -> list[dict]:
    """RSS 피드를 파싱해 뉴스 목록을 반환한다."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; YTGen/1.0)"}
        resp = requests.get(rss_url, headers=headers, timeout=10)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        items = []
        for item in list(root.iter("item"))[:5]:
            title   = _strip_html(item.findtext("title", ""))
            link    = item.findtext("link", "").strip()
            desc    = _strip_html(item.findtext("description", ""))
            pubdate = item.findtext("pubDate", "")

            if not link:
                guid = item.findtext("guid", "")
                if guid.startswith("http"):
                    link = guid

            items.append({
                "source":    source_name,
                "title":     title,
                "summary":   desc[:500],
                "url":       link,
                "published": pubdate,
            })
        return items

    except Exception as e:
        print(f"[news_fetcher] {source_name} RSS 파싱 실패: {e}")
        return []


def _build_rss_sources(keywords: list[str] = None) -> list[tuple[str, str]]:
    """키워드 목록으로 RSS 소스를 생성한다. 없으면 기본 AI 뉴스 소스 반환."""
    if not keywords:
        return _RSS_SOURCES
    sources = []
    for kw in keywords:
        import urllib.parse
        encoded = urllib.parse.quote(kw)
        sources.append((kw, f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"))
    return sources


def fetch_news(
    max_count: int = 1,
    skip_processed: bool = True,
    exclude_urls: set = None,
    keywords: list[str] = None,
) -> list[dict]:
    """
    최신 뉴스를 수집해 반환한다.

    Args:
        max_count: 최대 반환 뉴스 수
        skip_processed: SQLite DB에 기록된 뉴스 제외 (once/schedule 모드용)
        exclude_urls: 제외할 URL 집합 (web 모드에서 Supabase posted_news 전달)
        keywords: 검색 키워드 목록 (None이면 기본 AI 뉴스 RSS 사용)

    Returns:
        [{"source", "title", "summary", "url", "published"}, ...]
    """
    posted = set()
    if skip_processed:
        from src.db import get_posted_urls
        posted = get_posted_urls()
    if exclude_urls:
        posted = posted | exclude_urls

    all_news = []
    seen_titles = set()
    sources = _build_rss_sources(keywords)

    for source_name, rss_url in sources:
        items = _parse_feed(source_name, rss_url)
        for item in items:
            if not item["title"] or not item["url"]:
                continue
            if item["url"] in posted:
                continue
            title_key = item["title"][:20]
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            all_news.append(item)

        if len(all_news) >= max_count:
            break

    result = all_news[:max_count]
    print(f"[news_fetcher] {len(result)}개 뉴스 수집 (기등록 {len(posted)}개 제외)")
    return result
