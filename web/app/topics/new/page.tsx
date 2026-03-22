"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

export default function NewTopicPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [keywords, setKeywords] = useState("")
  const [contentMode, setContentMode] = useState<"news" | "ai_prompt">("news")
  const [aiPrompt, setAiPrompt] = useState("")
  const [error, setError] = useState("")

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) { setError("주제 이름을 입력하세요."); return }
    if (contentMode === "ai_prompt" && !aiPrompt.trim()) { setError("AI 프롬프트를 입력하세요."); return }
    setLoading(true)
    setError("")

    const res = await fetch("/api/topics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name.trim(),
        description: description.trim(),
        keywords: contentMode === "news" ? keywords.split(",").map((k) => k.trim()).filter(Boolean) : [],
        config: {
          content_mode: contentMode,
          ...(contentMode === "ai_prompt" ? { ai_prompt: aiPrompt.trim() } : {}),
        },
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

      <form onSubmit={handleSubmit} className="space-y-5">
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
            placeholder="예: AI 최신 뉴스를 자동 업로드"
            className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* 콘텐츠 생성 모드 */}
        <div>
          <label className="block text-sm font-medium mb-2">콘텐츠 생성 방식 *</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setContentMode("news")}
              className={`border rounded-lg p-3 text-left transition-colors ${
                contentMode === "news"
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-gray-200 hover:bg-gray-50"
              }`}
            >
              <div className="font-medium text-sm">📰 뉴스 기반</div>
              <div className="text-xs text-gray-500 mt-1">RSS 뉴스를 가져와 영상 제작</div>
            </button>
            <button
              type="button"
              onClick={() => setContentMode("ai_prompt")}
              className={`border rounded-lg p-3 text-left transition-colors ${
                contentMode === "ai_prompt"
                  ? "border-purple-500 bg-purple-50 text-purple-700"
                  : "border-gray-200 hover:bg-gray-50"
              }`}
            >
              <div className="font-medium text-sm">✨ AI 생성</div>
              <div className="text-xs text-gray-500 mt-1">프롬프트로 주제를 AI가 선정</div>
            </button>
          </div>
        </div>

        {/* 뉴스 모드: 키워드 */}
        {contentMode === "news" && (
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
        )}

        {/* AI 모드: 프롬프트 */}
        {contentMode === "ai_prompt" && (
          <div>
            <label className="block text-sm font-medium mb-1">AI 프롬프트 *</label>
            <textarea
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              rows={4}
              placeholder={`예: 시니어를 위한 건강 정보 콘텐츠. 혈압, 당뇨, 관절 건강 등 60대 이상이 알아야 할 실용적인 건강 팁을 다룬다.`}
              className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            />
            <p className="text-xs text-gray-400 mt-1">
              실행할 때마다 Gemini가 이 방향에 맞는 새로운 주제를 선정하여 중복 없이 영상을 제작합니다.
            </p>
          </div>
        )}

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
