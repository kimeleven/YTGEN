import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "YTGen 관리자",
  description: "YouTube Shorts 자동 생성 관리 대시보드",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <nav className="bg-white border-b px-6 py-3 flex items-center justify-between">
          <a href="/" className="font-bold text-lg">🎬 YTGen</a>
          <div className="flex items-center gap-3">
            <a href="/topics/new" className="bg-blue-600 text-white px-4 py-1.5 rounded-md text-sm hover:bg-blue-700">
              + 주제 추가
            </a>
            <form action="/api/auth/logout" method="POST">
              <button type="submit" className="text-sm text-gray-500 hover:text-gray-800">
                로그아웃
              </button>
            </form>
          </div>
        </nav>
        <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  )
}
