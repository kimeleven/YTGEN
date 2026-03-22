import { NextRequest, NextResponse } from "next/server"

export function middleware(req: NextRequest) {
  const token = req.cookies.get("auth_token")?.value
  const secret = process.env.AUTH_SECRET

  if (!secret) return NextResponse.next() // 환경변수 미설정 시 패스

  const isLoginPage = req.nextUrl.pathname === "/login"
  const isApiAuth = req.nextUrl.pathname.startsWith("/api/auth")

  if (isLoginPage || isApiAuth) return NextResponse.next()

  if (token !== secret) {
    const loginUrl = new URL("/login", req.url)
    loginUrl.searchParams.set("from", req.nextUrl.pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
}
