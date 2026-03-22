import { sql, Topic, Video } from "@/lib/db"
import { notFound } from "next/navigation"
import RunButton from "./RunButton"

export const dynamic = "force-dynamic"
export const revalidate = 0

async function getData(id: string) {
  const db = sql()
  const topicRows = await db`SELECT * FROM topics WHERE id = ${id}` as Topic[]
  if (topicRows.length === 0) return null
  const topic = topicRows[0]

  const videos = await db`
    SELECT * FROM videos WHERE topic_id = ${id} ORDER BY created_at DESC LIMIT 30
  ` as Video[]

  const accountRows = await db`
    SELECT channel_name, updated_at, token_json FROM youtube_accounts WHERE topic_id = ${id}
  `
  const account = accountRows[0] || null

  return { topic, videos, account }
}

export default async function TopicDetailPage({
  params,
  searchParams,
}: {
  params: { id: string }
  searchParams: { connected?: string; error?: string }
}) {
  const data = await getData(params.id)
  if (!data) notFound()
  const { topic, videos, account } = data

  const isConnected = account && account.token_json && account.token_json !== "pending"
  const isPending = account && account.token_json === "pending"

  const langCounts: Record<string, number> = {}
  for (const v of videos) {
    if (v.language) langCounts[v.language] = (langCounts[v.language] || 0) + 1
  }

  const errorMessages: Record<string, string> = {
    token_exchange: "Google 인증 코드 교환에 실패했습니다. 다시 시도해 주세요.",
    no_secret: "client_secret이 저장되지 않았습니다. 다시 연결을 시도해 주세요.",
    parse_error: "저장된 client_secret 형식이 올바르지 않습니다.",
  }

  return (
    <div className="space-y-6">

      {/* 연결 성공 배너 */}
      {searchParams.connected === "1" && (
        <div className="bg-green-50 border border-green-300 rounded-xl px-4 py-3 flex items-center gap-3">
          <span className="text-2xl">✅</span>
          <div>
            <p className="font-semibold text-green-800">YouTube 계정 연결 완료!</p>
            <p className="text-sm text-green-600">이제 이 주제의 영상이 연결된 채널에 자동 업로드됩니다.</p>
          </div>
        </div>
      )}

      {/* 연결 실패 배너 */}
      {searchParams.error && (
        <div className="bg-red-50 border border-red-300 rounded-xl px-4 py-3 flex items-center gap-3">
          <span className="text-2xl">❌</span>
          <div>
            <p className="font-semibold text-red-800">YouTube 연결 실패</p>
            <p className="text-sm text-red-600">{errorMessages[searchParams.error] || "알 수 없는 오류가 발생했습니다."}</p>
          </div>
        </div>
      )}

      {/* 헤더 */}
      <div className="flex items-start justify-between">
        <div>
          <a href="/" className="text-sm text-gray-400 hover:text-gray-600">← 대시보드</a>
          <h1 className="text-2xl font-bold mt-1">{topic.name}</h1>
          {topic.description && <p className="text-gray-500 mt-1">{topic.description}</p>}
        </div>
        <div className="flex gap-2 items-start">
          <a href={`/topics/${topic.id}/edit`} className="text-sm border rounded-md px-3 py-1.5 hover:bg-gray-50">
            편집
          </a>
          <RunButton topicId={topic.id} />
        </div>
      </div>

      {/* YouTube 연결 상태 */}
      <div className={`rounded-xl border p-4 ${isConnected ? "bg-green-50 border-green-200" : isPending ? "bg-yellow-50 border-yellow-200" : "bg-red-50 border-red-200"}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">
              {isConnected ? "✅" : isPending ? "⏳" : "❌"}
            </span>
            <div>
              <p className={`font-semibold ${isConnected ? "text-green-800" : isPending ? "text-yellow-800" : "text-red-800"}`}>
                {isConnected
                  ? `YouTube 연결됨${account.channel_name ? ` — ${account.channel_name}` : ""}`
                  : isPending
                  ? "YouTube 연결 미완료 (인증이 필요합니다)"
                  : "YouTube 미연결"}
              </p>
              {isConnected && (
                <p className="text-xs text-green-600 mt-0.5">
                  마지막 업데이트: {new Date(account.updated_at).toLocaleString("ko-KR")}
                </p>
              )}
              {!isConnected && (
                <p className={`text-xs mt-0.5 ${isPending ? "text-yellow-600" : "text-red-600"}`}>
                  YouTube 채널을 연결해야 자동 업로드가 가능합니다.
                </p>
              )}
            </div>
          </div>
          <a
            href={`/topics/${topic.id}/connect-youtube`}
            className={`text-sm px-3 py-1.5 rounded-md border ${
              isConnected
                ? "border-green-300 text-green-700 hover:bg-green-100"
                : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
            }`}
          >
            {isConnected ? "재연결" : isPending ? "인증 완료하기" : "연결하기"}
          </a>
        </div>
      </div>

      {/* 통계 */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="총 영상" value={videos.length} />
        <StatCard label="마지막 실행" value={topic.last_run_at ? new Date(topic.last_run_at).toLocaleDateString("ko-KR") : "-"} />
        <StatCard label="언어" value={Object.keys(langCounts).join(", ") || "-"} />
      </div>

      {/* 키워드 */}
      {topic.keywords && topic.keywords.length > 0 && (
        <div className="bg-white rounded-xl border p-4">
          <h2 className="font-semibold mb-2">뉴스 키워드</h2>
          <div className="flex flex-wrap gap-2">
            {topic.keywords.map((kw) => (
              <span key={kw} className="bg-blue-50 text-blue-600 text-sm px-3 py-1 rounded-full">{kw}</span>
            ))}
          </div>
        </div>
      )}

      {/* 영상 이력 */}
      <div className="bg-white rounded-xl border">
        <div className="px-4 py-3 border-b font-semibold">영상 이력 ({videos.length}개)</div>
        {videos.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">아직 생성된 영상이 없습니다.</div>
        ) : (
          <div className="divide-y">
            {videos.map((v) => (
              <div key={v.id} className="px-4 py-3 flex items-center justify-between text-sm">
                <div className="min-w-0 flex-1">
                  <div className="font-medium truncate">{v.title || v.news_title || "-"}</div>
                  <div className="text-gray-400 text-xs mt-0.5">
                    [{v.language?.toUpperCase()}] {new Date(v.created_at).toLocaleString("ko-KR")}
                  </div>
                </div>
                {v.youtube_url && v.youtube_url.startsWith("http") && (
                  <a href={v.youtube_url} target="_blank" className="ml-3 text-blue-600 hover:underline text-xs shrink-0">
                    YouTube →
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white rounded-xl border p-4 text-center">
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  )
}

