"""
Meta Graph API로 Facebook 페이지에 영상을 업로드한다.

필요 환경변수:
    META_ACCESS_TOKEN   - Meta 장기 액세스 토큰 (60일)
    FACEBOOK_PAGE_ID    - Facebook 페이지 ID

업로드 흐름:
    1. 업로드 세션 초기화
    2. 영상 청크 전송 (5MB 단위)
    3. 업로드 완료 처리 → 게시물 발행
"""
import os
import time

import requests

GRAPH_URL = "https://graph.facebook.com/v19.0"
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB


def upload_to_facebook(video_path: str, title: str, description: str) -> str:
    """
    Facebook 페이지에 영상을 업로드한다.

    Args:
        video_path: 업로드할 MP4 파일 경로
        title: 영상 제목
        description: 게시물 설명

    Returns:
        업로드된 게시물 URL (실패 시 "failed: {error}")
    """
    token = os.getenv("META_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")

    if not token or not page_id:
        print("[facebook] META_ACCESS_TOKEN 또는 FACEBOOK_PAGE_ID 없음 — 건너뜀")
        return "skipped: 환경변수 미설정"

    if not os.path.exists(video_path):
        return f"failed: 파일 없음 {video_path}"

    print(f"[facebook] 업로드 시작: {os.path.basename(video_path)}")

    try:
        file_size = os.path.getsize(video_path)

        # 1단계: 업로드 세션 초기화
        upload_session_id, start_offset = _init_upload(token, page_id, file_size)
        print(f"[facebook] 업로드 세션 생성: {upload_session_id}")

        # 2단계: 청크 전송
        _upload_chunks(token, upload_session_id, video_path, file_size, start_offset)

        # 3단계: 업로드 완료 → 게시물 발행
        video_id = _finish_upload(token, page_id, upload_session_id, title, description)

        url = f"https://www.facebook.com/video/{video_id}"
        print(f"[facebook] 업로드 완료: {url}")
        return url

    except Exception as e:
        print(f"[facebook] 업로드 실패: {e}")
        return f"failed: {e}"


def _init_upload(token: str, page_id: str, file_size: int) -> tuple[str, int]:
    """청크 업로드 세션을 초기화하고 (session_id, start_offset)을 반환한다."""
    resp = requests.post(
        f"{GRAPH_URL}/{page_id}/videos",
        params={"access_token": token},
        data={
            "upload_phase": "start",
            "file_size": file_size,
        },
    )
    resp.raise_for_status()
    data = resp.json()

    session_id = data.get("upload_session_id")
    start_offset = int(data.get("start_offset", 0))

    if not session_id:
        raise RuntimeError(f"업로드 세션 초기화 실패: {data}")

    return session_id, start_offset


def _upload_chunks(
    token: str,
    session_id: str,
    video_path: str,
    file_size: int,
    start_offset: int,
):
    """영상 파일을 청크 단위로 전송한다."""
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    offset = start_offset

    with open(video_path, "rb") as f:
        f.seek(offset)
        while offset < file_size:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break

            end_offset = offset + len(chunk)
            resp = requests.post(
                f"{GRAPH_URL}/{page_id}/videos",
                params={"access_token": token},
                data={
                    "upload_phase": "transfer",
                    "upload_session_id": session_id,
                    "start_offset": offset,
                    "video_file_chunk": chunk,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            next_offset = int(data.get("start_offset", end_offset))
            pct = int(next_offset / file_size * 100)
            print(f"[facebook] 업로드 중... {pct}%")
            offset = next_offset


def _finish_upload(
    token: str,
    page_id: str,
    session_id: str,
    title: str,
    description: str,
) -> str:
    """업로드를 완료하고 video_id를 반환한다."""
    resp = requests.post(
        f"{GRAPH_URL}/{page_id}/videos",
        params={"access_token": token},
        data={
            "upload_phase": "finish",
            "upload_session_id": session_id,
            "title": title[:255],
            "description": description[:5000],
        },
    )
    resp.raise_for_status()
    data = resp.json()

    video_id = data.get("video_id") or data.get("id")
    if not video_id:
        raise RuntimeError(f"업로드 완료 실패: {data}")

    return video_id
