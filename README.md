# YTGen — YouTube Shorts 자동 생성기

AI 뉴스를 수집해 자동으로 YouTube Shorts 영상을 만들고 업로드하는 파이프라인입니다.

---

## 동작 흐름

```
Google News RSS → 대본 생성 (Gemini) → 이미지 생성 → TTS 음성 합성 → 영상 인코딩 → YouTube 업로드
```

1. **뉴스 수집** — Google News RSS에서 AI 관련 최신 뉴스(OpenAI, Claude, Gemini, Grok 등)를 수집
2. **대본 생성** — Gemini API로 Shorts용 나레이션 스크립트 자동 작성
3. **이미지 생성** — Gemini 2.5 Flash Image → Imagen 4 순서로 시도, 모두 실패 시 그라디언트 배경 fallback
4. **TTS** — Microsoft Edge TTS(`ko-KR-SunHiNeural`)로 음성 파일 생성
5. **영상 조합** — MoviePy로 이미지+음성 클립 합성, 자막·워터마크·BGM 삽입 후 1080×1920 MP4 인코딩
6. **업로드** — YouTube Data API v3로 Shorts 업로드 (실패 시 로컬 저장)

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
GEMINI_API_KEY=your_gemini_api_key
```

YouTube 업로드를 위해 Google Cloud Console에서 OAuth 2.0 클라이언트 자격증명(`client_secret.json`)을 받아 루트에 배치하세요.
첫 실행 시 브라우저 인증이 진행되며 `token.json`이 자동 생성됩니다.

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
```

---

## 프로젝트 구조

```
YTGen/
├── main.py               # 진입점 (once / schedule / list)
├── config.yaml           # 전체 설정
├── requirements.txt
├── src/
│   ├── news_fetcher.py   # Google News RSS 수집
│   ├── script_gen.py     # Gemini로 대본 생성
│   ├── image_gen.py      # Imagen 이미지 생성
│   ├── tts_gen.py        # Edge TTS 음성 생성
│   ├── video_maker.py    # MoviePy 영상 합성
│   ├── uploader.py       # YouTube Data API 업로드
│   ├── scheduler.py      # APScheduler 스케줄 관리
│   └── db.py             # SQLite 중복 방지 DB
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
