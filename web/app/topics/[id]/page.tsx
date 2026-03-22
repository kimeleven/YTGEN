import { sql, Topic, Video } from "@/lib/db"
import { notFound } from "next/navigation"

async function getData(id: string) {
  const db = sql()
  const topicRows = await db`SELECT * FROM topics WHERE id = ${id}` as Topic[]
  if (topicRows.length === 0) return null
  const topic = topicRows[0]

  const videos = await db`
    SELECT * FROM videos WHERE topic_id = ${id} ORDER BY created_at DESC LIMIT 30
  ` as Video[]

  const accountRows = await db`
    SELECT channel_name, updated_at FROM youtube_accounts WHERE topic_id = ${id}
  `
  const account = accountRows[0] || null

  return { topic, videos, account }
}

export default async function TopicDetailPage({ params }: { params: { id: string } }) {
  const data = await getData(params.id)
  if (!data) notFound()
  const { topic, videos, account } = data

  const langCounts: Record<string, number> = {}
  for (const v of videos) {
    if (v.language) langCounts[v.language] = (langCounts[v.language] || 0) + 1
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{topic.name}</h1>
          {topic.description && <p className="text-gray-500 mt-1">{topic.description}</p>}
        </div>
        <div className="flex gap-2">
          <a href={`/topics/${topic.id}/connect-youtube`} className="text-sm border rounded-md px-3 py-1.5 hover:bg-gray-50">
            YouTube {account ? "재연결" : "연결"}
          </a>
          <RunNowButton topicId={topic.id} />
        </div>
      </div>

      {/* YouTube 상태 */}
      <div className="bg-white rounded-xl border p-4">
        <h2 className="font-semibold mb-2">YouTube 계정</h2>
        {account ? (
          <div className="text-sm text-gray-600 space-y-1">
            <div>✅ 채널: {account.channel_name || "연결됨"}</div>
            <div>🕐 마지막 업데이트: {new Date(account.updated_at).toLocaleString("ko-KR")}</div>
          </div>
        ) : (
          <div className="text-sm text-gray-400">❌ YouTube 계정이 연결되지 않았습니다.</div>
        )}
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

function RunNowButton({ topicId }: { topicId: string }) {
  return (
    <form action={`/api/topics/${topicId}/run`} method="POST">
      <button type="submit" className="text-sm bg-blue-600 text-white rounded-md px-3 py-1.5 hover:bg-blue-700">
        ▶ 지금 실행
      </button>
    </form>
  )
}
