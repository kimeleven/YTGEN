# YTGen — AI 뉴스 SNS 자동 업로드 봇

AI 뉴스를 수집해 자동으로 영상을 만들고 YouTube · Instagram · Facebook · Threads · TikTok에 동시 업로드하는 파이프라인입니다.

---

## 동작 흐름

```
Google News RSS → 대본 생성 (Gemini) → 이미지 생성 → TTS 음성 합성 → 영상 인코딩 → 멀티 SNS 업로드
```

1. **뉴스 수집** — Google News RSS에서 AI 관련 최신 뉴스(OpenAI, Claude, Gemini, Grok 등)를 수집
2. **대본 생성** — Gemini API로 Shorts용 나레이션 스크립트 자동 작성
3. **이미지 생성** — Gemini 2.5 Flash Image → Imagen 4 순서로 시도, 모두 실패 시 그라디언트 배경 fallback
4. **TTS** — Microsoft Edge TTS(`ko-KR-SunHiNeural`)로 음성 파일 생성
5. **영상 조합** — MoviePy로 이미지+음성 클립 합성, 자막·워터마크·BGM 삽입 후 1080×1920 MP4 인코딩
6. **멀티 SNS 업로드** — YouTube / Instagram Reels / Facebook / Threads / TikTok 동시 업로드

---

## 설치

```bash
pip install -r requirements.txt
```

> FFmpeg가 시스템에 설치되어 있어야 합니다.

---

## 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하세요.

```env
# ── 필수 ──────────────────────────────────
GEMINI_API_KEY=your_gemini_api_key

# ── YouTube ───────────────────────────────
# client_secret.json을 루트에 배치하면 자동으로 OAuth 인증 진행

# ── Instagram / Facebook / Threads (Meta 공통) ──
META_ACCESS_TOKEN=your_meta_long_lived_token   # 60일 유효
INSTAGRAM_USER_ID=your_instagram_user_id
FACEBOOK_PAGE_ID=your_facebook_page_id
THREADS_USER_ID=your_threads_user_id

# ── TikTok ────────────────────────────────
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token   # 24시간 유효, 자동 갱신
TIKTOK_REFRESH_TOKEN=your_tiktok_refresh_token
```

각 플랫폼 토큰 발급 방법은 아래 **SNS 설정 가이드** 참고.

`config.yaml`에서 사용하지 않을 플랫폼은 `enabled: false`로 끌 수 있습니다.

---

## 사용법

```bash
# 뉴스 1개로 즉시 영상 생성 (테스트용)
python main.py once

# 스케줄러 시작 (6시간 간격, 하루 최대 4개)
python main.py schedule

# 생성된 영상 목록 및 DB 통계 확인
python main.py list
```

---

## 스케줄 설정 (`config.yaml`)

```yaml
schedule:
  interval_hours: 6   # 실행 간격 (시간)
  daily_limit: 4      # 하루 최대 생성 개수
  start_time: "09:00" # 첫 실행 시각

sns:
  instagram:
    enabled: true     # false로 바꾸면 해당 플랫폼 건너뜀
  facebook:
    enabled: true
  threads:
    enabled: true
  tiktok:
    enabled: true
```

---

## SNS 설정 가이드

### Meta 계열 (Instagram + Facebook + Threads 공통)
> 하나의 Meta 앱으로 세 플랫폼을 모두 제어합니다.

1. [developers.facebook.com](https://developers.facebook.com) → **앱 생성**
2. 제품 추가: `Instagram Graph API` · `Facebook Login` · `Threads API`
3. Instagram 계정을 **비즈니스 또는 크리에이터** 계정으로 전환
4. Facebook **페이지** 생성 (없으면)
5. [Meta Graph Explorer](https://developers.facebook.com/tools/explorer/)에서 토큰 발급
   - 필요 권한: `instagram_basic` `instagram_content_publish` `pages_manage_posts` `threads_basic` `threads_content_publish`
6. 발급 토큰을 **장기 토큰(60일)** 으로 교환
7. `.env`에 `META_ACCESS_TOKEN`, `INSTAGRAM_USER_ID`, `FACEBOOK_PAGE_ID`, `THREADS_USER_ID` 저장

### TikTok
1. [developers.tiktok.com](https://developers.tiktok.com) → 개발자 계정 등록
2. 앱 생성 → **Content Posting API** 제품 선택
3. 앱 심사 신청 (수일~수주 소요)
4. 심사 통과 후 OAuth 로그인으로 Access Token + Refresh Token 발급
5. `.env`에 `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_ACCESS_TOKEN`, `TIKTOK_REFRESH_TOKEN` 저장
   - Access Token은 24시간마다 자동 갱신됩니다.

---

## 프로젝트 구조

```
YTGen/
├── main.py               # 진입점 (once / schedule / list)
├── config.yaml           # 전체 설정
├── requirements.txt
├── src/
│   ├── news_fetcher.py        # Google News RSS 수집
│   ├── script_gen.py          # Gemini로 대본 생성
│   ├── image_gen.py           # Imagen 이미지 생성
│   ├── tts_gen.py             # Edge TTS 음성 생성
│   ├── video_maker.py         # MoviePy 영상 합성
│   ├── uploader.py            # YouTube 업로드 + upload_all() 디스패처
│   ├── instagram_uploader.py  # Instagram Reels 업로드
│   ├── facebook_uploader.py   # Facebook 영상 업로드
│   ├── threads_uploader.py    # Threads 영상 업로드
│   ├── tiktok_uploader.py     # TikTok 영상 업로드
│   ├── scheduler.py           # APScheduler 스케줄 관리
│   └── db.py                  # SQLite 중복 방지 DB
├── output/               # 생성된 MP4 저장
├── temp/                 # 세그먼트 임시 파일
└── data/
    └── ytgen.db          # 업로드 기록 DB
```

---

## 주요 의존성

| 패키지 | 용도 |
|---|---|
| `google-genai` | Gemini 대본 생성, Gemini Flash Image / Imagen 4 이미지 생성 |
| `edge-tts` | Microsoft Edge TTS 한국어 음성 합성 |
| `moviepy` | 영상 합성·인코딩 |
| `Pillow` | 자막·워터마크 렌더링 |
| `APScheduler` | 주기적 실행 스케줄링 |
| `google-api-python-client` | YouTube 업로드 |
