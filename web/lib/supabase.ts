import { createClient } from "@supabase/supabase-js"

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// 서버 전용 (API routes): service key 사용
export function createServiceClient() {
  return createClient(supabaseUrl, process.env.SUPABASE_SERVICE_KEY!)
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

export type YoutubeAccount = {
  id: string
  topic_id: string
  channel_name: string | null
  updated_at: string
}
