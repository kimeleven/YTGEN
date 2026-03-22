-- YTGen Web Publish — Supabase 스키마
-- Supabase SQL Editor에서 실행하세요

-- ── 주제 테이블 ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS topics (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  description TEXT,
  keywords    TEXT[],             -- 뉴스 RSS 검색 키워드 (없으면 기본 AI 뉴스)
  config      JSONB DEFAULT '{}', -- languages, schedule 등 오버라이드 설정
  active      BOOLEAN DEFAULT true,
  created_at  TIMESTAMPTZ DEFAULT now(),
  last_run_at TIMESTAMPTZ
);

-- ── YouTube 계정 테이블 (주제별) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS youtube_accounts (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id           UUID REFERENCES topics(id) ON DELETE CASCADE,
  channel_name       TEXT,
  token_json         TEXT NOT NULL,        -- YouTube OAuth 토큰 JSON (암호화 권장)
  client_secret_json TEXT NOT NULL,        -- Google OAuth 앱 자격증명 JSON
  updated_at         TIMESTAMPTZ DEFAULT now(),
  UNIQUE (topic_id)
);

-- ── 생성된 영상 이력 ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS videos (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id    UUID REFERENCES topics(id) ON DELETE CASCADE,
  news_url    TEXT,
  news_title  TEXT,
  language    TEXT,
  title       TEXT,
  youtube_url TEXT,
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- ── 처리된 뉴스 URL (주제별 중복 방지) ───────────────────────────────
CREATE TABLE IF NOT EXISTS posted_news (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id   UUID REFERENCES topics(id) ON DELETE CASCADE,
  news_url   TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (topic_id, news_url)
);

-- ── 인덱스 ──────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_topics_active ON topics(active, last_run_at);
CREATE INDEX IF NOT EXISTS idx_videos_topic ON videos(topic_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posted_news_topic ON posted_news(topic_id, news_url);

-- ── RLS (Row Level Security) — 서비스 키로만 접근 ────────────────────
ALTER TABLE topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE youtube_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE posted_news ENABLE ROW LEVEL SECURITY;

-- 서비스 롤은 모든 작업 허용 (GitHub Actions, 웹 API에서 service_key 사용)
CREATE POLICY "service_all" ON topics FOR ALL USING (true);
CREATE POLICY "service_all" ON youtube_accounts FOR ALL USING (true);
CREATE POLICY "service_all" ON videos FOR ALL USING (true);
CREATE POLICY "service_all" ON posted_news FOR ALL USING (true);
