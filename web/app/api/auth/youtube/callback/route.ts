import { NextRequest, NextResponse } from "next/server"
import { sql } from "@/lib/db"

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl
  const code = searchParams.get("code")
  const topicId = searchParams.get("state")
  const error = searchParams.get("error")

  const baseUrl = new URL(req.url).origin

  if (error || !code || !topicId) {
    return NextResponse.redirect(new URL(`/?auth_error=${error || "missing_code"}`, baseUrl))
  }

  // DB에서 client_secret 조회
  const db = sql()
  const rows = await db`
    SELECT client_secret_json FROM youtube_accounts WHERE topic_id = ${topicId}
  `
  if (rows.length === 0) {
    return NextResponse.redirect(new URL(`/topics/${topicId}/connect-youtube?error=no_secret`, baseUrl))
  }

  let creds: Record<string, string>
  try {
    const parsed = JSON.parse(rows[0].client_secret_json)
    creds = (parsed.web || parsed.installed) as Record<string, string>
  } catch {
    return NextResponse.redirect(new URL(`/topics/${topicId}/connect-youtube?error=parse_error`, baseUrl))
  }

  const redirectUri = `${baseUrl}/api/auth/youtube/callback`
  console.log("[youtube/callback] baseUrl:", baseUrl, "redirectUri:", redirectUri)

  // 인증 코드 → 토큰 교환
  const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id: creds.client_id,
      client_secret: creds.client_secret,
      redirect_uri: redirectUri,
      grant_type: "authorization_code",
    }),
  })

  if (!tokenRes.ok) {
    const err = await tokenRes.text()
    console.error("Token exchange failed:", err)
    return NextResponse.redirect(new URL(`/topics/${topicId}/connect-youtube?error=token_exchange`, baseUrl))
  }

  const tokenData = await tokenRes.json()
  const tokenJson = JSON.stringify(tokenData)

  // DB에 token 저장
  await db`
    UPDATE youtube_accounts
    SET token_json = ${tokenJson}, updated_at = now()
    WHERE topic_id = ${topicId}
  `

  return NextResponse.redirect(new URL(`/topics/${topicId}?connected=1`, baseUrl))
}
