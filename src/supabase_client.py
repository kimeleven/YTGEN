"""
Neon PostgreSQL 클라이언트 — 주제/YouTube 계정/영상 이력/중복 방지 관리.

환경변수:
    DATABASE_URL - Neon PostgreSQL 연결 문자열
                   예: postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
"""
import os
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

import psycopg2
import psycopg2.extras


def _get_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL 환경변수가 필요합니다.")
    return url


@contextmanager
def _conn():
    """PostgreSQL 연결 컨텍스트 매니저."""
    conn = psycopg2.connect(_get_url(), cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── 주제 (Topic) ──────────────────────────────────────────────────────────────

def get_next_topic(topic_id: Optional[str] = None) -> Optional[dict]:
    """
    다음 실행할 주제를 반환한다.

    topic_id 지정 시 해당 주제 반환.
    없으면 active=true 중 last_run_at이 가장 오래된(NULL 포함) 주제 1개.
    """
    with _conn() as conn:
        with conn.cursor() as cur:
            if topic_id:
                cur.execute("SELECT * FROM topics WHERE id = %s", (topic_id,))
            else:
                cur.execute("""
                    SELECT * FROM topics
                    WHERE active = true
                    ORDER BY last_run_at ASC NULLS FIRST
                    LIMIT 1
                """)
            row = cur.fetchone()
            return dict(row) if row else None


def update_last_run(topic_id: str) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE topics SET last_run_at = %s WHERE id = %s",
                (datetime.now(timezone.utc), topic_id),
            )


def list_topics() -> list[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM topics ORDER BY created_at")
            return [dict(r) for r in cur.fetchall()]


def create_topic(name: str, description: str = "", keywords: list = None, config: dict = None) -> dict:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO topics (name, description, keywords, config)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (name, description, keywords or [], json.dumps(config or {})),
            )
            return dict(cur.fetchone())


def update_topic(topic_id: str, **kwargs) -> dict:
    fields = ", ".join(f"{k} = %s" for k in kwargs)
    values = list(kwargs.values()) + [topic_id]
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE topics SET {fields} WHERE id = %s RETURNING *", values)
            return dict(cur.fetchone())


def delete_topic(topic_id: str) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM topics WHERE id = %s", (topic_id,))


# ── YouTube 계정 ──────────────────────────────────────────────────────────────

def get_topic_youtube_token(topic_id: str) -> Optional[tuple[str, str]]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT token_json, client_secret_json FROM youtube_accounts WHERE topic_id = %s",
                (topic_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return row["token_json"], row["client_secret_json"]


def save_youtube_token(topic_id: str, channel_name: str, token_json: str, client_secret_json: str) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO youtube_accounts (topic_id, channel_name, token_json, client_secret_json, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (topic_id) DO UPDATE
                  SET channel_name = EXCLUDED.channel_name,
                      token_json = EXCLUDED.token_json,
                      client_secret_json = EXCLUDED.client_secret_json,
                      updated_at = EXCLUDED.updated_at
                """,
                (topic_id, channel_name, token_json, client_secret_json, datetime.now(timezone.utc)),
            )


# ── 영상 이력 ─────────────────────────────────────────────────────────────────

def save_video_result(topic_id: str, news_url: str, news_title: str,
                      language: str, title: str, youtube_url: str) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO videos (topic_id, news_url, news_title, language, title, youtube_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (topic_id, news_url, news_title, language, title, youtube_url),
            )


def list_videos(topic_id: str, limit: int = 20) -> list[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM videos WHERE topic_id = %s ORDER BY created_at DESC LIMIT %s",
                (topic_id, limit),
            )
            return [dict(r) for r in cur.fetchall()]


# ── 중복 뉴스 방지 ────────────────────────────────────────────────────────────

def is_news_posted(topic_id: str, news_url: str) -> bool:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM posted_news WHERE topic_id = %s AND news_url = %s LIMIT 1",
                (topic_id, news_url),
            )
            return cur.fetchone() is not None


def mark_news_posted(topic_id: str, news_url: str) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO posted_news (topic_id, news_url) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (topic_id, news_url),
                )
            except Exception:
                pass


def get_posted_urls(topic_id: str) -> set[str]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT news_url FROM posted_news WHERE topic_id = %s",
                (topic_id,),
            )
            return {row["news_url"] for row in cur.fetchall()}
