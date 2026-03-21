"""
Threads API로 영상을 업로드한다.

필요 환경변수:
    META_ACCESS_TOKEN   - Meta 장기 액세스 토큰 (60일)
    THREADS_USER_ID     - Threads 사용자 ID

필요 API 권한:
    threads_basic, threads_content_publish

업로드 흐름:
    1. 미디어 컨테이너 생성 (VIDEO 타입)
    2. 처리 완료까지 polling (최대 5분)
    3. 컨테이너 publish
"""
import os
import time

import requests

THREADS_URL = "https://graph.threads.net/v1.0"


def upload_to_threads(video_path: str, caption: str) -> str:
    """
    Threads에 영상을 업로드한다.

    Args:
        video_path: 업로드할 MP4 파일 경로
        caption: 게시물 캡션 (#해시태그 포함)

    Returns:
        업로드된 게시물 URL (실패 시 "failed: {error}")
    """
    token = os.getenv("META_ACCESS_TOKEN")
    user_id = os.getenv("THREADS_USER_ID")

    if not token or not user_id:
        print("[threads] META_ACCESS_TOKEN 또는 THREADS_USER_ID 없음 — 건너뜀")
        return "skipped: 환경변수 미설정"

    if not os.path.exists(video_path):
        return f"failed: 파일 없음 {video_path}"

    print(f"[threads] 업로드 시작: {os.path.basename(video_path)}")

    try:
        # 1단계: 미디어 컨테이너 생성
        container_id = _create_container(token, user_id, video_path, caption)
        print(f"[threads] 컨테이너 생성 완료: {container_id}")

        # 2단계: 처리 완료 대기
        _wait_for_ready(token, container_id)

        # 3단계: publish
        media_id = _publish(token, user_id, container_id)
        url = f"https://www.threads.net/t/{media_id}"
        print(f"[threads] 업로드 완료: {url}")
        return url

    except Exception as e:
        print(f"[threads] 업로드 실패: {e}")
        return f"failed: {e}"


def _create_container(token: str, user_id: str, video_path: str, caption: str) -> str:
    """VIDEO 미디어 컨테이너를 생성하고 container_id를 반환한다."""
    file_size = os.path.getsize(video_path)

    resp = requests.post(
        f"{THREADS_URL}/{user_id}/threads",
        params={"access_token": token},
        data={
            "media_type": "VIDEO",
            "upload_type": "resumable",
            "text": caption,
        },
    )
    resp.raise_for_status()
    data = resp.json()

    container_id = data.get("id")
    upload_url = data.get("upload_url")

    if not container_id:
        raise RuntimeError(f"컨테이너 생성 실패: {data}")

    if not upload_url:
        # upload_url 별도 조회
        upload_url = _get_upload_url(token, container_id)

    # 영상 바이트 전송
    _upload_video_bytes(upload_url, token, video_path, file_size)

    return container_id


def _get_upload_url(token: str, container_id: str) -> str:
    """컨테이너의 업로드 URL을 조회한다."""
    resp = requests.get(
        f"{THREADS_URL}/{container_id}",
        params={"fields": "upload_url", "access_token": token},
    )
    resp.raise_for_status()
    data = resp.json()
    upload_url = data.get("upload_url")
    if not upload_url:
        raise RuntimeError(f"upload_url 조회 실패: {data}")
    return upload_url


def _upload_video_bytes(upload_url: str, token: str, video_path: str, file_size: int):
    """영상 바이트를 resumable 업로드 엔드포인트에 전송한다."""
    with open(video_path, "rb") as f:
        video_bytes = f.read()

    resp = requests.post(
        upload_url,
        headers={
            "Authorization": f"OAuth {token}",
            "offset": "0",
            "file_size": str(file_size),
        },
        data=video_bytes,
        timeout=300,
    )
    resp.raise_for_status()
    print(f"[threads] 영상 전송 완료 ({file_size / 1024 / 1024:.1f} MB)")


def _wait_for_ready(token: str, container_id: str, timeout: int = 300):
    """컨테이너 처리가 완료될 때까지 polling한다."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(
            f"{THREADS_URL}/{container_id}",
            params={"fields": "status", "access_token": token},
        )
        resp.raise_for_status()
        status = resp.json().get("status", "")

        if status == "FINISHED":
            print("[threads] 처리 완료")
            return
        if status == "ERROR":
            raise RuntimeError("Threads 미디어 처리 중 오류 발생")

        print(f"[threads] 처리 중... ({status})")
        time.sleep(10)

    raise TimeoutError("Threads 미디어 처리 시간 초과 (5분)")


def _publish(token: str, user_id: str, container_id: str) -> str:
    """컨테이너를 publish하고 media_id를 반환한다."""
    resp = requests.post(
        f"{THREADS_URL}/{user_id}/threads_publish",
        params={
            "creation_id": container_id,
            "access_token": token,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    media_id = data.get("id")
    if not media_id:
        raise RuntimeError(f"publish 실패: {data}")
    return media_id
