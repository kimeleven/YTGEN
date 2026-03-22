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
  const [guideOpen, setGuideOpen] = useState(false)

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
                <li>YTGen 프로젝트 로컬 실행 환경 (Python)</li>
              </ul>
            </div>

            <div>
              <p className="font-semibold text-gray-900 mb-2">① Google Cloud Console에서 OAuth 앱 설정</p>
              <ol className="list-decimal list-inside space-y-2 text-gray-600">
                <li><span className="font-medium text-gray-800">console.cloud.google.com</span> 접속 → 프로젝트 생성 (또는 기존 프로젝트 선택)</li>
                <li><span className="font-medium text-gray-800">API 및 서비스 → 라이브러리</span>에서 <span className="bg-gray-100 px-1 rounded">YouTube Data API v3</span> 검색 후 사용 설정</li>
                <li><span className="font-medium text-gray-800">API 및 서비스 → OAuth 동의 화면</span> 설정
                  <ul className="list-disc list-inside ml-4 mt-1 space-y-1 text-xs text-gray-500">
                    <li>User Type: 외부 선택</li>
                    <li>앱 이름, 지원 이메일 입력 후 저장</li>
                    <li>스코프에서 <code className="bg-gray-100 px-1 rounded">.../auth/youtube.upload</code> 추가</li>
                    <li>테스트 사용자에 업로드할 Google 계정 이메일 추가</li>
                  </ul>
                </li>
                <li><span className="font-medium text-gray-800">API 및 서비스 → 사용자 인증 정보</span> → <span className="bg-blue-50 text-blue-700 px-1 rounded">+ 사용자 인증 정보 만들기</span> → OAuth 클라이언트 ID
                  <ul className="list-disc list-inside ml-4 mt-1 space-y-1 text-xs text-gray-500">
                    <li>애플리케이션 유형: <span className="font-medium">데스크톱 앱</span></li>
                    <li>생성 후 <span className="font-medium">JSON 다운로드</span> → 이게 <code className="bg-gray-100 px-1 rounded">client_secret.json</code></li>
                  </ul>
                </li>
              </ol>
            </div>

            <div>
              <p className="font-semibold text-gray-900 mb-2">② 로컬에서 token.json 발급</p>
              <ol className="list-decimal list-inside space-y-2 text-gray-600">
                <li>다운로드한 <code className="bg-gray-100 px-1 rounded">client_secret.json</code>을 YTGen 프로젝트 폴더에 저장</li>
                <li>터미널에서 실행:
                  <div className="mt-1 bg-gray-900 text-green-400 rounded px-3 py-2 font-mono text-xs">
                    python main.py once
                  </div>
                </li>
                <li>브라우저가 열리며 Google 로그인 화면 표시 → <span className="font-medium">업로드할 YouTube 채널의 계정으로 로그인</span></li>
                <li>권한 허용 후 터미널로 돌아오면 <code className="bg-gray-100 px-1 rounded">data/token.json</code> 생성됨</li>
              </ol>
            </div>

            <div>
              <p className="font-semibold text-gray-900 mb-2">③ JSON 내용 붙여넣기</p>
              <ol className="list-decimal list-inside space-y-1 text-gray-600">
                <li><code className="bg-gray-100 px-1 rounded">client_secret.json</code> 파일을 텍스트 편집기로 열어 전체 내용 복사 → 아래 첫 번째 칸에 붙여넣기</li>
                <li><code className="bg-gray-100 px-1 rounded">data/token.json</code> 파일을 텍스트 편집기로 열어 전체 내용 복사 → 아래 두 번째 칸에 붙여넣기</li>
              </ol>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2 text-xs text-yellow-800">
              ⚠️ token.json은 YouTube 채널 접근 권한을 가진 민감한 정보입니다. 이 페이지는 HTTPS로 암호화 전송되며, 데이터베이스에 저장됩니다.
            </div>
          </div>
        )}
      </div>

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
            <span className="font-normal text-gray-400 ml-1">(Google Cloud Console에서 다운로드한 파일)</span>
          </label>
          <textarea
            value={clientSecretJson}
            onChange={(e) => setClientSecretJson(e.target.value)}
            placeholder='{"installed":{"client_id":"...","client_secret":"..."}}'
            rows={4}
            className="w-full border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            token.json 내용 *
            <span className="font-normal text-gray-400 ml-1">(python main.py once 실행 후 data/token.json)</span>
          </label>
          <textarea
            value={tokenJson}
            onChange={(e) => setTokenJson(e.target.value)}
            placeholder='{"token":"ya29...","refresh_token":"1//...","token_uri":"..."}'
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
