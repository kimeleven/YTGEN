"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Suspense } from "react"

function ConnectYoutubeForm({ params }: { params: { id: string } }) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const urlError = searchParams.get("error")

  const errorMessages: Record<string, string> = {
    token_exchange: "Google 인증 코드 교환 실패. 다시 시도해 주세요.",
    no_secret: "저장된 client_secret이 없습니다. 다시 입력해 주세요.",
    parse_error: "client_secret 형식이 올바르지 않습니다.",
  }

  const [clientSecretJson, setClientSecretJson] = useState("")
  const [channelName, setChannelName] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(urlError ? (errorMessages[urlError] || "오류가 발생했습니다.") : "")
  const [guideOpen, setGuideOpen] = useState(false)

  async function handleConnect(e: React.FormEvent) {
    e.preventDefault()
    if (!clientSecretJson.trim()) {
      setError("client_secret.json 내용을 입력하세요.")
      return
    }
    setLoading(true)
    setError("")

    const res = await fetch(`/api/topics/${params.id}/youtube/auth-url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_secret_json: clientSecretJson.trim(),
        channel_name: channelName.trim(),
      }),
    })

    if (res.ok) {
      const { url } = await res.json()
      window.location.href = url  // Google OAuth 페이지로 이동
    } else {
      const data = await res.json()
      setError(data.error || "오류가 발생했습니다.")
      setLoading(false)
    }
  }

  return (
    <div className="max-w-lg">
      <a href={`/topics/${params.id}`} className="text-sm text-gray-400 hover:text-gray-600">← 돌아가기</a>
      <h1 className="text-2xl font-bold mt-4 mb-6">YouTube 계정 연결</h1>

      {/* 안내 가이드 */}
      <div className="border rounded-xl mb-6 overflow-hidden">
        <button
          type="button"
          onClick={() => setGuideOpen(!guideOpen)}
          className="w-full flex items-center justify-between px-4 py-3 bg-blue-50 text-blue-800 text-sm font-medium hover:bg-blue-100"
        >
          <span>📋 연결 방법 안내 (처음이라면 먼저 읽어주세요)</span>
          <span>{guideOpen ? "▲" : "▼"}</span>
        </button>

        {guideOpen && (
          <div className="px-4 py-4 text-sm space-y-5 text-gray-700 bg-white">
            <div>
              <p className="font-semibold text-gray-900 mb-2">📌 준비물</p>
              <ul className="list-disc list-inside space-y-1 text-gray-600">
                <li>Google 계정 (업로드할 YouTube 채널)</li>
                <li>Google Cloud Console 접근 권한</li>
              </ul>
            </div>

            <div>
              <p className="font-semibold text-gray-900 mb-2">① YouTube Data API 활성화</p>
              <ol className="list-decimal list-inside space-y-2 text-gray-600">
                <li><span className="font-medium">console.cloud.google.com</span> 접속 → 프로젝트 생성 (또는 기존 선택)</li>
                <li><span className="font-medium">API 및 서비스 → 라이브러리</span>에서 <code className="bg-gray-100 px-1 rounded">YouTube Data API v3</code> 검색 후 사용 설정</li>
              </ol>
            </div>

            <div>
              <p className="font-semibold text-gray-900 mb-2">② OAuth 동의 화면 설정</p>
              <ol className="list-decimal list-inside space-y-2 text-gray-600">
                <li><span className="font-medium">API 및 서비스 → OAuth 동의 화면</span> → User Type: <span className="font-medium">외부</span> 선택</li>
                <li>앱 이름, 지원 이메일 입력 후 저장</li>
                <li>스코프 추가: <code className="bg-gray-100 px-1 rounded">.../auth/youtube.upload</code></li>
                <li>테스트 사용자에 업로드할 Google 계정 이메일 추가</li>
              </ol>
            </div>

            <div>
              <p className="font-semibold text-gray-900 mb-2">③ OAuth 클라이언트 ID 생성</p>
              <ol className="list-decimal list-inside space-y-2 text-gray-600">
                <li><span className="font-medium">API 및 서비스 → 사용자 인증 정보</span> → <span className="text-blue-700">+ 사용자 인증 정보 만들기</span> → OAuth 클라이언트 ID</li>
                <li>애플리케이션 유형: <span className="font-medium text-red-600">웹 애플리케이션</span> 선택 (데스크톱 앱 아님)</li>
                <li>승인된 리디렉션 URI 추가:
                  <div className="mt-1 bg-gray-900 text-green-400 rounded px-3 py-2 font-mono text-xs break-all">
                    {typeof window !== "undefined" ? window.location.origin : "https://your-domain.vercel.app"}/api/auth/youtube/callback
                  </div>
                </li>
                <li>생성 후 <span className="font-medium">JSON 다운로드</span> → 이게 <code className="bg-gray-100 px-1 rounded">client_secret.json</code></li>
              </ol>
            </div>

            <div>
              <p className="font-semibold text-gray-900 mb-2">④ 아래 양식 작성 후 연결</p>
              <p className="text-gray-600">다운로드한 <code className="bg-gray-100 px-1 rounded">client_secret.json</code> 파일을 텍스트 편집기로 열어 전체 내용을 복사 후 붙여넣으세요.<br/>이후 "Google 계정으로 연결" 버튼을 클릭하면 구글 로그인 후 자동으로 완료됩니다.</p>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2 text-xs text-yellow-800">
              ⚠️ client_secret.json은 민감한 정보입니다. HTTPS로 암호화 전송되며, 데이터베이스에 저장됩니다.
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleConnect} className="space-y-4">
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
            <span className="font-normal text-gray-400 ml-1">(Google Cloud Console → 사용자 인증 정보 → JSON 다운로드)</span>
          </label>
          <textarea
            value={clientSecretJson}
            onChange={(e) => setClientSecretJson(e.target.value)}
            placeholder='{"web":{"client_id":"...","client_secret":"...","redirect_uris":["..."]}}'
            rows={5}
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
            className="flex-1 bg-red-600 text-white rounded-md py-2 text-sm hover:bg-red-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? "연결 중..." : "🔗 Google 계정으로 연결"}
          </button>
        </div>
      </form>
    </div>
  )
}

export default function ConnectYoutubePage({ params }: { params: { id: string } }) {
  return (
    <Suspense>
      <ConnectYoutubeForm params={params} />
    </Suspense>
  )
}
