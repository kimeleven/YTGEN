"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

export default function NewTopicPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [keywords, setKeywords] = useState("")
  const [error, setError] = useState("")

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) { setError("주제 이름을 입력하세요."); return }
    setLoading(true)
    setError("")

    const res = await fetch("/api/topics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name.trim(),
        description: description.trim(),
        keywords: keywords.split(",").map((k) => k.trim()).filter(Boolean),
      }),
    })

    if (res.ok) {
      const topic = await res.json()
      router.push(`/topics/${topic.id}/connect-youtube`)
    } else {
      const data = await res.json()
      setError(data.error || "생성 실패")
      setLoading(false)
    }
  }

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">새 주제 만들기</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">주제 이름 *</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="예: AI뉴스, 시니어콘텐츠"
            className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">설명</label>
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="예: AI 최신 뉴스를 한국어/영어로 자동 업로드"
            className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">뉴스 키워드</label>
          <input
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="예: 인공지능, ChatGPT, 딥러닝 (쉼표로 구분)"
            className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-400 mt-1">비우면 기본 AI 뉴스 RSS를 사용합니다.</p>
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <div className="flex gap-3 pt-2">
          <button
            type="button"
            onClick={() => router.back()}
            className="flex-1 border rounded-md py-2 text-sm hover:bg-gray-50"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-blue-600 text-white rounded-md py-2 text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "생성 중..." : "만들기 →"}
          </button>
        </div>
      </form>
    </div>
  )
}
