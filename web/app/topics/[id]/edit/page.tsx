"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"

export default function EditTopicPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)
  const [error, setError] = useState("")

  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [keywords, setKeywords] = useState("")
  const [contentMode, setContentMode] = useState<"news" | "ai_prompt">("news")
  const [aiPrompt, setAiPrompt] = useState("")
  const [active, setActive] = useState(true)

  useEffect(() => {
    fetch(`/api/topics/${params.id}`)
      .then((r) => r.json())
      .then((topic) => {
        setName(topic.name || "")
        setDescription(topic.description || "")
        setKeywords((topic.keywords || []).join(", "))
        setActive(topic.active ?? true)
        const cfg = topic.config || {}
        setContentMode(cfg.content_mode === "ai_prompt" ? "ai_prompt" : "news")
        setAiPrompt(cfg.ai_prompt || "")
        setFetching(false)
      })
      .catch(() => { setError("주제 정보를 불러오지 못했습니다."); setFetching(false) })
  }, [params.id])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) { setError("주제 이름을 입력하세요."); return }
    if (contentMode === "ai_prompt" && !aiPrompt.trim()) { setError("AI 프롬프트를 입력하세요."); return }
    setLoading(true)
    setError("")

    const res = await fetch(`/api/topics/${params.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name.trim(),
        description: description.trim() || null,
        keywords: contentMode === "news" ? keywords.split(",").map((k) => k.trim()).filter(Boolean) : [],
        active,
        config: {
          content_mode: contentMode,
          ...(contentMode === "ai_prompt" ? { ai_prompt: aiPrompt.trim() } : {}),
        },
      }),
    })

    if (res.ok) {
      router.push(`/topics/${params.id}`)
    } else {
      const data = await res.json()
      setError(data.error || "저장 실패")
      setLoading(false)
    }
  }

  async function handleDelete() {
    if (!confirm(`"${name}" 주제를 삭제할까요? 영상 이력도 모두 삭제됩니다.`)) return
    await fetch(`/api/topics/${params.id}`, { method: "DELETE" })
    router.push("/")
  }

  if (fetching) return <div className="text-gray-400 py-20 text-center">불러오는 중...</div>

  return (
    <div className="max-w-lg">
      <a href={`/topics/${params.id}`} className="text-sm text-gray-400 hover:text-gray-600">← 돌아가기</a>
      <h1 className="text-2xl font-bold mt-4 mb-6">주제 편집</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* 활성 토글 */}
        <div className="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-3">
          <div>
            <p className="text-sm font-medium">자동 실행</p>
            <p className="text-xs text-gray-400 mt-0.5">비활성화하면 스케줄 자동 실행에서 제외됩니다.</p>
          </div>
          <button
            type="button"
            onClick={() => setActive(!active)}
            className={`relative w-11 h-6 rounded-full transition-colors ${active ? "bg-blue-600" : "bg-gray-300"}`}
          >
            <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${active ? "translate-x-5" : ""}`} />
          </button>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">주제 이름 *</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">설명</label>
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* 콘텐츠 모드 */}
        <div>
          <label className="block text-sm font-medium mb-2">콘텐츠 생성 방식</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setContentMode("news")}
              className={`border rounded-lg p-3 text-left transition-colors ${contentMode === "news" ? "border-blue-500 bg-blue-50 text-blue-700" : "border-gray-200 hover:bg-gray-50"}`}
            >
              <div className="font-medium text-sm">📰 뉴스 기반</div>
              <div className="text-xs text-gray-500 mt-1">RSS 뉴스로 영상 제작</div>
            </button>
            <button
              type="button"
              onClick={() => setContentMode("ai_prompt")}
              className={`border rounded-lg p-3 text-left transition-colors ${contentMode === "ai_prompt" ? "border-purple-500 bg-purple-50 text-purple-700" : "border-gray-200 hover:bg-gray-50"}`}
            >
              <div className="font-medium text-sm">✨ AI 생성</div>
              <div className="text-xs text-gray-500 mt-1">프롬프트로 주제 선정</div>
            </button>
          </div>
        </div>

        {contentMode === "news" && (
          <div>
            <label className="block text-sm font-medium mb-1">뉴스 키워드</label>
            <input
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="예: 인공지능, ChatGPT (쉼표로 구분)"
              className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-400 mt-1">비우면 기본 AI 뉴스 RSS 사용</p>
          </div>
        )}

        {contentMode === "ai_prompt" && (
          <div>
            <label className="block text-sm font-medium mb-1">AI 프롬프트 *</label>
            <textarea
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              rows={4}
              className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            />
            <p className="text-xs text-gray-400 mt-1">실행마다 이 방향으로 새로운 주제를 선정합니다.</p>
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
            {loading ? "저장 중..." : "저장"}
          </button>
        </div>
      </form>

      {/* 삭제 */}
      <div className="mt-10 pt-6 border-t">
        <button
          type="button"
          onClick={handleDelete}
          className="text-sm text-red-500 hover:text-red-700"
        >
          이 주제 삭제
        </button>
      </div>
    </div>
  )
}
