import { NextRequest, NextResponse } from "next/server"
import { sql } from "@/lib/db"

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const { client_secret_json, channel_name } = await req.json()

  if (!client_secret_json?.trim()) {
    return NextResponse.json({ error: "client_secret_json 필수" }, { status: 400 })
  }

  let parsed: Record<string, unknown>
  try {
    parsed = JSON.parse(client_secret_json)
  } catch {
    return NextResponse.json({ error: "유효한 JSON 형식이 아닙니다." }, { status: 400 })
  }

  // "web" 또는 "installed" 키 지원
  const creds = (parsed.web || parsed.installed) as Record<string, string> | undefined
  if (!creds?.client_id || !creds?.client_secret) {
    return NextResponse.json({ error: "client_id 또는 client_secret을 찾을 수 없습니다." }, { status: 400 })
  }

  // DB에 client_secret 저장 (token은 OAuth 완료 후 채워짐)
  const db = sql()
  await db`
    INSERT INTO youtube_accounts (topic_id, channel_name, client_secret_json, token_json, updated_at)
    VALUES (${params.id}, ${channel_name || null}, ${client_secret_json.trim()}, ${"pending"}, now())
    ON CONFLICT (topic_id) DO UPDATE
      SET channel_name       = EXCLUDED.channel_name,
          client_secret_json = EXCLUDED.client_secret_json,
          token_json         = 'pending',
          updated_at         = EXCLUDED.updated_at
  `

  const baseUrl = process.env.NEXTAUTH_URL || "http://localhost:3000"
  const redirectUri = `${baseUrl}/api/auth/youtube/callback`

  const oauthUrl = new URL("https://accounts.google.com/o/oauth2/v2/auth")
  oauthUrl.searchParams.set("client_id", creds.client_id)
  oauthUrl.searchParams.set("redirect_uri", redirectUri)
  oauthUrl.searchParams.set("response_type", "code")
  oauthUrl.searchParams.set("scope", "https://www.googleapis.com/auth/youtube.upload")
  oauthUrl.searchParams.set("access_type", "offline")
  oauthUrl.searchParams.set("prompt", "consent")
  oauthUrl.searchParams.set("state", params.id)

  return NextResponse.json({ url: oauthUrl.toString() })
}
