-- YTGen Web Publish — Neon PostgreSQL 스키마
-- Neon Console SQL Editor에서 실행하세요

CREATE TABLE IF NOT EXISTS topics (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  description TEXT,
  keywords    TEXT[],
  config      JSONB DEFAULT '{}',
  active      BOOLEAN DEFAULT true,
  created_at  TIMESTAMPTZ DEFAULT now(),
  last_run_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS youtube_accounts (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id           UUID REFERENCES topics(id) ON DELETE CASCADE,
  channel_name       TEXT,
  token_json         TEXT NOT NULL,
  client_secret_json TEXT NOT NULL,
  updated_at         TIMESTAMPTZ DEFAULT now(),
  UNIQUE (topic_id)
);

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

CREATE TABLE IF NOT EXISTS posted_news (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id   UUID REFERENCES topics(id) ON DELETE CASCADE,
  news_url   TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (topic_id, news_url)
);

CREATE INDEX IF NOT EXISTS idx_topics_active ON topics(active, last_run_at);
CREATE INDEX IF NOT EXISTS idx_videos_topic  ON videos(topic_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posted_news   ON posted_news(topic_id, news_url);
