"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Suspense } from "react"

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const from = searchParams.get("from") || "/"

  const [user, setUser] = useState("")
  const [pass, setPass] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)

    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: user, password: pass }),
    })

    setLoading(false)

    if (res.ok) {
      router.push(from)
      router.refresh()
    } else {
      const data = await res.json()
      setError(data.error || "로그인 실패")
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl border shadow-sm p-8 w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold">YTGen</h1>
          <p className="text-gray-500 text-sm mt-1">관리자 로그인</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">아이디</label>
            <input
              type="text"
              value={user}
              onChange={(e) => setUser(e.target.value)}
              required
              autoFocus
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
            <input
              type="password"
              value={pass}
              onChange={(e) => setPass(e.target.value)}
              required
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {error && (
            <p className="text-red-500 text-sm">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "로그인 중..." : "로그인"}
          </button>
        </form>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  )
}
