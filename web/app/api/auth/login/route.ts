import { NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  const { username, password } = await req.json()

  const adminUser = process.env.ADMIN_USER
  const adminPass = process.env.ADMIN_PASSWORD
  const secret = process.env.AUTH_SECRET

  if (!adminUser || !adminPass || !secret) {
    return NextResponse.json({ error: "서버 환경변수 미설정" }, { status: 500 })
  }

  if (username !== adminUser || password !== adminPass) {
    return NextResponse.json({ error: "아이디 또는 비밀번호가 틀렸습니다." }, { status: 401 })
  }

  const res = NextResponse.json({ ok: true })
  res.cookies.set("auth_token", secret, {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 30, // 30일
    path: "/",
  })
  return res
}
