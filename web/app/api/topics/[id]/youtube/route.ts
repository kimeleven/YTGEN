import { NextRequest, NextResponse } from "next/server"
import { createServiceClient } from "@/lib/supabase"

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const body = await req.json()
  const { token_json, client_secret_json, channel_name } = body

  if (!token_json?.trim() || !client_secret_json?.trim()) {
    return NextResponse.json({ error: "token_json, client_secret_json 필수" }, { status: 400 })
  }

  // JSON 유효성 검사
  try {
    JSON.parse(token_json)
    JSON.parse(client_secret_json)
  } catch {
    return NextResponse.json({ error: "유효한 JSON 형식이 아닙니다." }, { status: 400 })
  }

  const sb = createServiceClient()
  const { error } = await sb.from("youtube_accounts").upsert(
    {
      topic_id: params.id,
      channel_name: channel_name || null,
      token_json: token_json.trim(),
      client_secret_json: client_secret_json.trim(),
      updated_at: new Date().toISOString(),
    },
    { onConflict: "topic_id" }
  )

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ ok: true })
}
