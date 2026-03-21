"""
TikTok Content Posting API로 영상을 업로드한다.

필요 환경변수:
    TIKTOK_CLIENT_KEY       - TikTok 앱 Client Key
    TIKTOK_CLIENT_SECRET    - TikTok 앱 Client Secret
    TIKTOK_ACCESS_TOKEN     - OAuth Access Token (24시간 유효)
    TIKTOK_REFRESH_TOKEN    - OAuth Refresh Token (토큰 갱신용)

업로드 흐름:
    1. Access Token 유효성 확인 → 만료 시 자동 갱신
    2. 업로드 초기화 (initialize)
    3. 영상 청크 전송 (upload)
    4. 업로드 완료 처리 (publish)
    5. 처리 완료 대기 (polling)
"""
import json
import os
import time

import requests

TIKTOK_API = "https://open.tiktokapis.com/v2"
TOKEN_FILE  = "data/tiktok_token.json"
CHUNK_SIZE  = 10 * 1024 * 1024  # 10MB


def upload_to_tiktok(video_path: str, title: str) -> str:
    """
    TikTok에 영상을 업로드한다.

    Args:
        video_path: 업로드할 MP4 파일 경로
        title: 영상 제목 (설명란에 사용)

    Returns:
        업로드 성공 메시지 또는 "failed: {error}"
    """
    client_key    = os.getenv("TIKTOK_CLIENT_KEY")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET")

    if not client_key or not client_secret:
        print("[tiktok] TIKTOK_CLIENT_KEY 또는 TIKTOK_CLIENT_SECRET 없음 — 건너뜀")
        return "skipped: 환경변수 미설정"

    if not os.path.exists(video_path):
        return f"failed: 파일 없음 {video_path}"

    print(f"[tiktok] 업로드 시작: {os.path.basename(video_path)}")

    try:
        token = _get_valid_token(client_key, client_secret)
        file_size = os.path.getsize(video_path)

        # 1단계: 업로드 초기화
        upload_url, publish_id = _initialize_upload(token, file_size, title)
        print(f"[tiktok] 업로드 초기화 완료 (publish_id: {publish_id})")

        # 2단계: 청크 전송
        _upload_chunks(upload_url, video_path, file_size)

        # 3단계: 처리 완료 대기
        _wait_for_publish(token, publish_id)

        url = "https://www.tiktok.com"  # TikTok API는 업로드 후 URL을 바로 제공하지 않음
        print(f"[tiktok] 업로드 완료! TikTok 앱에서 확인하세요.")
        return f"published (publish_id: {publish_id})"

    except Exception as e:
        print(f"[tiktok] 업로드 실패: {e}")
        return f"failed: {e}"


def _get_valid_token(client_key: str, client_secret: str) -> str:
    """유효한 Access Token을 반환한다. 만료 시 자동 갱신."""
    # 1. 환경변수에서 토큰 확인
    token = os.getenv("TIKTOK_ACCESS_TOKEN")
    refresh_token = os.getenv("TIKTOK_REFRESH_TOKEN")

    # 2. 저장된 토큰 파일 확인 (갱신된 토큰)
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if saved.get("expires_at", 0) > time.time() + 60:
                return saved["access_token"]
            # 만료됐으면 저장된 refresh_token 사용
            refresh_token = saved.get("refresh_token", refresh_token)
        except Exception:
            pass

    # 3. 현재 토큰 유효성 확인
    if token:
        if _is_token_valid(token):
            return token

    # 4. Refresh Token으로 갱신
    if refresh_token:
        return _refresh_access_token(client_key, client_secret, refresh_token)

    if not token:
        raise RuntimeError(
            "TIKTOK_ACCESS_TOKEN 없음. TikTok 개발자 콘솔에서 OAuth 인증 후 토큰을 .env에 저장하세요."
        )

    return token


def _is_token_valid(token: str) -> bool:
    """토큰으로 간단한 API 호출을 해서 유효한지 확인한다."""
    try:
        resp = requests.get(
            f"{TIKTOK_API}/user/info/",
            headers={"Authorization": f"Bearer {token}"},
            params={"fields": "open_id"},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


def _refresh_access_token(client_key: str, client_secret: str, refresh_token: str) -> str:
    """Refresh Token으로 새 Access Token을 발급받는다."""
    print("[tiktok] 액세스 토큰 갱신 중...")
    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    data = resp.json()

    new_token = data.get("access_token")
    new_refresh = data.get("refresh_token", refresh_token)
    expires_in = data.get("expires_in", 86400)

    if not new_token:
        raise RuntimeError(f"토큰 갱신 실패: {data}")

    # 갱신된 토큰 저장
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "access_token": new_token,
            "refresh_token": new_refresh,
            "expires_at": time.time() + expires_in,
        }, f)

    print("[tiktok] 토큰 갱신 완료")
    return new_token


def _initialize_upload(token: str, file_size: int, title: str) -> tuple[str, str]:
    """업로드를 초기화하고 (upload_url, publish_id)를 반환한다."""
    chunk_count = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE

    resp = requests.post(
        f"{TIKTOK_API}/post/publish/video/init/",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={
            "post_info": {
                "title": title[:150],
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": CHUNK_SIZE,
                "total_chunk_count": chunk_count,
            },
        },
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("error", {}).get("code") != "ok":
        raise RuntimeError(f"업로드 초기화 실패: {data}")

    upload_url = data["data"]["upload_url"]
    publish_id = data["data"]["publish_id"]
    return upload_url, publish_id


def _upload_chunks(upload_url: str, video_path: str, file_size: int):
    """영상 파일을 청크 단위로 전송한다."""
    offset = 0
    chunk_index = 0

    with open(video_path, "rb") as f:
        while offset < file_size:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break

            end_offset = offset + len(chunk) - 1
            resp = requests.put(
                upload_url,
                headers={
                    "Content-Range": f"bytes {offset}-{end_offset}/{file_size}",
                    "Content-Type": "video/mp4",
                },
                data=chunk,
                timeout=300,
            )
            resp.raise_for_status()

            offset += len(chunk)
            chunk_index += 1
            pct = int(offset / file_size * 100)
            print(f"[tiktok] 업로드 중... {pct}% (청크 {chunk_index})")


def _wait_for_publish(token: str, publish_id: str, timeout: int = 300):
    """영상 처리 완료까지 polling한다."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.post(
            f"{TIKTOK_API}/post/publish/status/fetch/",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            json={"publish_id": publish_id},
        )
        resp.raise_for_status()
        data = resp.json()

        status = data.get("data", {}).get("status", "")

        if status == "PUBLISH_COMPLETE":
            print("[tiktok] 게시 완료")
            return
        if status in ("FAILED", "PUBLISH_FAILED"):
            fail_reason = data.get("data", {}).get("fail_reason", "알 수 없음")
            raise RuntimeError(f"TikTok 게시 실패: {fail_reason}")

        print(f"[tiktok] 처리 중... ({status})")
        time.sleep(10)

    raise TimeoutError("TikTok 게시 처리 시간 초과 (5분)")
