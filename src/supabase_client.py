"""
Supabase 클라이언트 — 주제/YouTube 계정/영상 이력/중복 방지 관리.

환경변수:
    SUPABASE_URL         - Supabase 프로젝트 URL
    SUPABASE_SERVICE_KEY - 서비스 롤 키 (GitHub Actions, API 서버에서 사용)
"""
import os
from datetime import datetime, timezone
from typing import Optional

from supabase import create_client, Client

_client: Optional[Client] = None


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL, SUPABASE_SERVICE_KEY 환경변수가 필요합니다."
            )
        _client = create_client(url, key)
    return _client


# ── 주제 (Topic) ──────────────────────────────────────────────────────────────

def get_next_topic(topic_id: Optional[str] = None) -> Optional[dict]:
    """
    다음 실행할 주제를 반환한다.

    topic_id 지정 시 해당 주제를 반환.
    없으면 active=true 중 last_run_at이 가장 오래된(NULL 포함) 주제 1개.
    """
    sb = _get_client()

    if topic_id:
        resp = sb.table("topics").select("*").eq("id", topic_id).single().execute()
        return resp.data

    resp = (
        sb.table("topics")
        .select("*")
        .eq("active", True)
        .order("last_run_at", desc=False, nullsfirst=True)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def update_last_run(topic_id: str) -> None:
    """주제의 last_run_at을 현재 시각으로 업데이트한다."""
    sb = _get_client()
    sb.table("topics").update(
        {"last_run_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", topic_id).execute()


def list_topics() -> list[dict]:
    """모든 주제 목록을 반환한다."""
    sb = _get_client()
    resp = sb.table("topics").select("*").order("created_at").execute()
    return resp.data or []


def create_topic(name: str, description: str = "", keywords: list[str] = None, config: dict = None) -> dict:
    """주제를 생성하고 반환한다."""
    sb = _get_client()
    resp = sb.table("topics").insert({
        "name": name,
        "description": description,
        "keywords": keywords or [],
        "config": config or {},
    }).execute()
    return resp.data[0]


def update_topic(topic_id: str, **kwargs) -> dict:
    """주제를 업데이트하고 반환한다."""
    sb = _get_client()
    resp = sb.table("topics").update(kwargs).eq("id", topic_id).execute()
    return resp.data[0]


def delete_topic(topic_id: str) -> None:
    """주제를 삭제한다."""
    sb = _get_client()
    sb.table("topics").delete().eq("id", topic_id).execute()


# ── YouTube 계정 ──────────────────────────────────────────────────────────────

def get_topic_youtube_token(topic_id: str) -> Optional[tuple[str, str]]:
    """
    주제의 YouTube OAuth 토큰을 반환한다.

    Returns:
        (token_json, client_secret_json) 튜플, 없으면 None
    """
    sb = _get_client()
    resp = (
        sb.table("youtube_accounts")
        .select("token_json, client_secret_json")
        .eq("topic_id", topic_id)
        .single()
        .execute()
    )
    if not resp.data:
        return None
    return resp.data["token_json"], resp.data["client_secret_json"]


def save_youtube_token(topic_id: str, channel_name: str, token_json: str, client_secret_json: str) -> None:
    """YouTube 토큰을 저장하거나 업데이트한다."""
    sb = _get_client()
    sb.table("youtube_accounts").upsert(
        {
            "topic_id": topic_id,
            "channel_name": channel_name,
            "token_json": token_json,
            "client_secret_json": client_secret_json,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="topic_id",
    ).execute()


# ── 영상 이력 ─────────────────────────────────────────────────────────────────

def save_video_result(
    topic_id: str,
    news_url: str,
    news_title: str,
    language: str,
    title: str,
    youtube_url: str,
) -> None:
    """영상 생성 결과를 저장한다."""
    sb = _get_client()
    sb.table("videos").insert({
        "topic_id": topic_id,
        "news_url": news_url,
        "news_title": news_title,
        "language": language,
        "title": title,
        "youtube_url": youtube_url,
    }).execute()


def list_videos(topic_id: str, limit: int = 20) -> list[dict]:
    """주제의 최근 영상 목록을 반환한다."""
    sb = _get_client()
    resp = (
        sb.table("videos")
        .select("*")
        .eq("topic_id", topic_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []


# ── 중복 뉴스 방지 ────────────────────────────────────────────────────────────

def is_news_posted(topic_id: str, news_url: str) -> bool:
    """해당 주제에서 이미 처리된 뉴스 URL인지 확인한다."""
    sb = _get_client()
    resp = (
        sb.table("posted_news")
        .select("id")
        .eq("topic_id", topic_id)
        .eq("news_url", news_url)
        .limit(1)
        .execute()
    )
    return bool(resp.data)


def mark_news_posted(topic_id: str, news_url: str) -> None:
    """뉴스 URL을 처리 완료로 표시한다."""
    sb = _get_client()
    try:
        sb.table("posted_news").insert({
            "topic_id": topic_id,
            "news_url": news_url,
        }).execute()
    except Exception:
        pass  # UNIQUE 제약 위반 시 무시


def get_posted_urls(topic_id: str) -> set[str]:
    """주제에서 처리된 모든 뉴스 URL 집합을 반환한다."""
    sb = _get_client()
    resp = (
        sb.table("posted_news")
        .select("news_url")
        .eq("topic_id", topic_id)
        .execute()
    )
    return {row["news_url"] for row in (resp.data or [])}
