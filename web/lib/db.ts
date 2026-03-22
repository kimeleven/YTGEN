import { neon } from "@neondatabase/serverless"

export function sql() {
  const url = process.env.DATABASE_URL
  if (!url) throw new Error("DATABASE_URL 환경변수를 설정하세요.")
  return neon(url)
}

export type Topic = {
  id: string
  name: string
  description: string | null
  keywords: string[] | null
  config: Record<string, unknown>
  active: boolean
  created_at: string
  last_run_at: string | null
}

export type Video = {
  id: string
  topic_id: string
  news_url: string | null
  news_title: string | null
  language: string | null
  title: string | null
  youtube_url: string | null
  created_at: string
}
