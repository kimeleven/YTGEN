"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

export default function ConnectYoutubePage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const [tokenJson, setTokenJson] = useState("")
  const [clientSecretJson, setClientSecretJson] = useState("")
  const [channelName, setChannelName] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!tokenJson.trim() || !clientSecretJson.trim()) {
      setError("token.json과 client_secret.json 내용을 모두 입력하세요.")
      return
    }
    setLoading(true)
    setError("")

    const res = await fetch(`/api/topics/${params.id}/youtube`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token_json: tokenJson.trim(),
        client_secret_json: clientSecretJson.trim(),
        channel_name: channelName.trim(),
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

  return (
    <div className="max-w-lg">
      <a href={`/topics/${params.id}`} className="text-sm text-gray-400 hover:text-gray-600">← 돌아가기</a>
      <h1 className="text-2xl font-bold mt-4 mb-2">YouTube 계정 연결</h1>
      <p className="text-sm text-gray-500 mb-6">
        이 주제 전용 YouTube 채널의 OAuth 토큰을 입력합니다.
        로컬에서 <code className="bg-gray-100 px-1 rounded">python main.py once</code>를 한 번 실행하면
        <code className="bg-gray-100 px-1 rounded">data/token.json</code>이 생성됩니다.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">채널 이름 (선택)</label>
          <input
            value={channelName}
            onChange={(e) => setChannelName(e.target.value)}
            placeholder="예: AI뉴스 채널"
            className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            client_secret.json 내용 *
            <span className="font-normal text-gray-400 ml-1">(Google Cloud Console에서 다운로드)</span>
          </label>
          <textarea
            value={clientSecretJson}
            onChange={(e) => setClientSecretJson(e.target.value)}
            placeholder='{"installed":{"client_id":"..."}}'
            rows={4}
            className="w-full border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            token.json 내용 *
            <span className="font-normal text-gray-400 ml-1">(data/token.json 파일 내용)</span>
          </label>
          <textarea
            value={tokenJson}
            onChange={(e) => setTokenJson(e.target.value)}
            placeholder='{"token":"ya29...","refresh_token":"1//...","...":""}'
            rows={4}
            className="w-full border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
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
            {loading ? "저장 중..." : "저장"}
          </button>
        </div>
      </form>
    </div>
  )
}
