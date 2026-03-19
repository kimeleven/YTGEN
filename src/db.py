"""
SQLite DB로 업로드된 뉴스를 관리한다.
중복 뉴스 방지 및 통계 조회에 사용.
DB 파일: data/ytgen.db
"""
import os
import sqlite3
from datetime import datetime

DB_PATH = "data/ytgen.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS posted_videos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    url        TEXT UNIQUE NOT NULL,
    title      TEXT,
    source     TEXT,
    video_path TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);
"""


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """DB와 테이블을 초기화한다. 앱 시작 시 1회 호출."""
    with _connect() as conn:
        conn.execute(_CREATE_TABLE)
        conn.commit()
    print(f"[db] 초기화 완료: {DB_PATH}")


def is_posted(url: str) -> bool:
    """해당 URL의 뉴스가 이미 처리됐는지 확인한다."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM posted_videos WHERE url = ?", (url,)
        ).fetchone()
    return row is not None


def save_posted(news_item: dict, video_path: str):
    """영상 생성 완료된 뉴스를 DB에 저장한다."""
    url   = news_item.get("url", "")
    title = news_item.get("title", "")
    source = news_item.get("source", "")

    if not url:
        return

    with _connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO posted_videos (url, title, source, video_path)
            VALUES (?, ?, ?, ?)
            """,
            (url, title, source, video_path),
        )
        conn.commit()
    print(f"[db] 저장 완료: [{source}] {title[:40]}")


def get_posted_urls() -> set:
    """처리된 모든 URL을 set으로 반환한다."""
    with _connect() as conn:
        rows = conn.execute("SELECT url FROM posted_videos").fetchall()
    return {row[0] for row in rows}


def get_stats() -> dict:
    """오늘/전체 업로드 통계를 반환한다."""
    today = datetime.now().strftime("%Y-%m-%d")
    with _connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM posted_videos"
        ).fetchone()[0]
        today_count = conn.execute(
            "SELECT COUNT(*) FROM posted_videos WHERE created_at LIKE ?",
            (f"{today}%",),
        ).fetchone()[0]
        recent = conn.execute(
            "SELECT title, source, created_at FROM posted_videos ORDER BY id DESC LIMIT 5"
        ).fetchall()

    return {
        "total": total,
        "today": today_count,
        "recent": [{"title": r[0], "source": r[1], "created_at": r[2]} for r in recent],
    }
