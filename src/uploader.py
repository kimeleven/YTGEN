"""
YouTube Data API v3로 Shorts 영상을 업로드한다.
첫 실행 시 브라우저 OAuth 인증 → token.json 저장 → 이후 자동 갱신.
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
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("[uploader] 토큰 갱신 완료")
        else:
            print("[uploader] 브라우저에서 Google 계정 인증을 진행합니다...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
            print("[uploader] 인증 완료")

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
) -> str:
    """
    YouTube Shorts에 영상을 업로드한다.

    Returns:
        업로드된 영상의 YouTube URL
    """
    if not os.path.exists(CLIENT_SECRET):
        print("[uploader] client_secret.json 없음 — 업로드 건너뜀")
        return f"local://{os.path.abspath(video_path)}"

    print(f"[uploader] 업로드 시작: {os.path.basename(video_path)}")

    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    # Shorts용 설명에 #Shorts 태그 추가
    shorts_description = f"{description}\n\n#Shorts #AI #인공지능"

    body = {
        "snippet": {
            "title": title[:100],           # YouTube 제목 최대 100자
            "description": shorts_description[:5000],
            "tags": tags,
            "categoryId": "28",             # 28 = Science & Technology
            "defaultLanguage": "ko",
        },
        "status": {
            "privacyStatus": "public",      # public / private / unlisted
            "selfDeclaredMadeForKids": False,
            # AI 생성 콘텐츠 라벨 (YouTube 정책 준수)
            "containsSyntheticMedia": True,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024,  # 5MB 청크
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"[uploader] 업로드 중... {pct}%")

    video_id  = response["id"]
    video_url = f"https://www.youtube.com/shorts/{video_id}"

    print(f"[uploader] 업로드 완료!")
    print(f"[uploader] URL: {video_url}")
    print(f"[uploader] 제목: {title}")
    print(f"[uploader] 태그: {', '.join(tags)}")

    return video_url
