import { NextResponse } from "next/server"

export async function POST() {
  const res = NextResponse.redirect(
    new URL("/login", process.env.NEXTAUTH_URL || "http://localhost:3000")
  )
  res.cookies.set("auth_token", "", { maxAge: 0, path: "/" })
  return res
}
