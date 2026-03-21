"""
YouTube Data API v3로 Shorts 영상을 업로드한다.
첫 실행 시 브라우저 OAuth 인증 → token.json 저장 → 이후 자동 갱신.

upload_all()로 활성화된 모든 SNS 플랫폼에 일괄 업로드 가능.
"""
import os
import json

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CLIENT_SECRET = "client_secret.json"
TOKEN_FILE    = "data/token.json"
SCOPES        = ["https://www.googleapis.com/auth/youtube"]


def _get_credentials() -> Credentials:
    """OAuth2 인증 정보를 반환한다. 없으면 브라우저 인증 실행."""
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    creds = None

    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"[uploader] 기존 token.json 로드 실패: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("[uploader] 토큰 갱신 완료")
            except Exception as e:
                print(f"[uploader] 토큰 갱신 실패: {e}")
                creds = None

        if not creds:
            print("[uploader] 브라우저에서 Google 계정 인증을 진행합니다...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
            print("[uploader] 인증 완료")

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return creds


def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    default_language: str = "ko",
    region_codes: list[str] | None = None,
) -> str:
    """
    YouTube Shorts에 영상을 업로드한다.

    Args:
        default_language: 영상 언어 코드 ("ko", "en", "ja", "zh" 등)
        region_codes: 노출 허용 국가 코드 리스트 (None이면 전 세계)

    Returns:
        업로드된 영상의 YouTube URL
    """
    if not os.path.exists(CLIENT_SECRET):
        print("[uploader] client_secret.json 없음 — 업로드 건너뜀")
        return f"local://{os.path.abspath(video_path)}"

    print(f"[uploader] 업로드 시작: {os.path.basename(video_path)}")
    if region_codes:
        print(f"[uploader] 지역 제한: {', '.join(region_codes)}")

    try:
        creds = _get_credentials()
        youtube = build("youtube", "v3", credentials=creds)

        shorts_description = f"{description}\n\n#Shorts #AI"
        body = {
            "snippet": {
                "title": title[:100],
                "description": shorts_description[:5000],
                "tags": tags,
                "categoryId": "28",
                "defaultLanguage": default_language,
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
                "containsSyntheticMedia": True,
            },
        }

        # 지역 제한 설정
        if region_codes:
            body["contentDetails"] = {
                "regionRestriction": {
                    "allowed": region_codes,
                }
            }

        parts = "snippet,status,contentDetails" if region_codes else "snippet,status"

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=5 * 1024 * 1024,
        )

        request = youtube.videos().insert(
            part=parts,
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"[uploader] 업로드 중... {pct}%")

        video_id = response.get("id")
        if not video_id:
            raise RuntimeError("YouTube 업로드 응답에 video id가 없습니다.")

        video_url = f"https://www.youtube.com/shorts/{video_id}"
        print(f"[uploader] 업로드 완료!")
        print(f"[uploader] URL: {video_url}")
        print(f"[uploader] 제목: {title}")
        print(f"[uploader] 태그: {', '.join(tags)}")
        return video_url

    except Exception as e:
        print(f"[uploader] 업로드 실패: {e}")
        print("[uploader] 로컬 저장 URL로 대체합니다.")
        return f"local://{os.path.abspath(video_path)}"


def upload_all(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    cfg: dict,
    lang_cfg: dict | None = None,
) -> dict:
    """
    활성화된 모든 SNS 플랫폼에 영상을 업로드한다.

    Args:
        video_path: 업로드할 MP4 파일 경로
        title: 영상 제목
        description: 영상 설명
        tags: 해시태그 리스트
        cfg: config.yaml 전체 dict
        lang_cfg: languages 항목 1개 (언어 코드·지역 코드 포함)

    Returns:
        {"youtube": url, "instagram": url, ...} 형태의 결과 dict
        각 플랫폼 실패 시 해당 값은 "failed: {error}" 문자열
    """
    results = {}
    sns_cfg = cfg.get("sns", {})
    lang_code = (lang_cfg or {}).get("code", "ko")
    region_codes = (lang_cfg or {}).get("youtube_regions")
    # 언어별 업로드 대상 플랫폼 (없으면 전체)
    allowed = set((lang_cfg or {}).get("platforms", ["youtube", "instagram", "facebook", "threads", "tiktok"]))
    caption = f"{title}\n\n{' '.join('#' + t for t in tags)}\n#AI #Shorts"

    # YouTube (platforms에 포함된 경우)
    if "youtube" in allowed:
        print("\n[upload_all] YouTube 업로드 중...")
        results["youtube"] = upload_to_youtube(
            video_path, title, description, tags,
            default_language=lang_code,
            region_codes=region_codes,
        )

    # Instagram Reels
    if "instagram" in allowed and sns_cfg.get("instagram", {}).get("enabled"):
        print("\n[upload_all] Instagram 업로드 중...")
        from src.instagram_uploader import upload_to_instagram
        results["instagram"] = upload_to_instagram(video_path, caption)

    # Facebook
    if "facebook" in allowed and sns_cfg.get("facebook", {}).get("enabled"):
        print("\n[upload_all] Facebook 업로드 중...")
        from src.facebook_uploader import upload_to_facebook
        results["facebook"] = upload_to_facebook(video_path, title, description)

    # Threads
    if "threads" in allowed and sns_cfg.get("threads", {}).get("enabled"):
        print("\n[upload_all] Threads 업로드 중...")
        from src.threads_uploader import upload_to_threads
        results["threads"] = upload_to_threads(video_path, caption)

    # TikTok
    if "tiktok" in allowed and sns_cfg.get("tiktok", {}).get("enabled"):
        print("\n[upload_all] TikTok 업로드 중...")
        from src.tiktok_uploader import upload_to_tiktok
        results["tiktok"] = upload_to_tiktok(video_path, title)

    # 결과 요약 출력
    print("\n" + "=" * 50)
    print("[upload_all] 업로드 결과 요약")
    print("=" * 50)
    for platform, result in results.items():
        status = "✓" if result.startswith("http") or result.startswith("published") else "✗"
        print(f"  {status} {platform}: {result}")
    print("=" * 50)

    return results
