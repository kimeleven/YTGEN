import { NextRequest, NextResponse } from "next/server"
import { sql } from "@/lib/db"

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const body = await req.json()
  const { token_json, client_secret_json, channel_name } = body

  if (!token_json?.trim() || !client_secret_json?.trim()) {
    return NextResponse.json({ error: "token_json, client_secret_json 필수" }, { status: 400 })
  }

  try {
    JSON.parse(token_json)
    JSON.parse(client_secret_json)
  } catch {
    return NextResponse.json({ error: "유효한 JSON 형식이 아닙니다." }, { status: 400 })
  }

  try {
    const db = sql()
    await db`
      INSERT INTO youtube_accounts (topic_id, channel_name, token_json, client_secret_json, updated_at)
      VALUES (${params.id}, ${channel_name || null}, ${token_json.trim()}, ${client_secret_json.trim()}, now())
      ON CONFLICT (topic_id) DO UPDATE
        SET channel_name       = EXCLUDED.channel_name,
            token_json         = EXCLUDED.token_json,
            client_secret_json = EXCLUDED.client_secret_json,
            updated_at         = EXCLUDED.updated_at
    `
    return NextResponse.json({ ok: true })
  } catch (e: unknown) {
    return NextResponse.json({ error: (e as Error).message }, { status: 500 })
  }
}
