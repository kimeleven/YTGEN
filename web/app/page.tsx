import { sql, Topic, Video } from "@/lib/db"

async function getTopicsWithAccounts() {
  const db = sql()
  const topics = await db`SELECT * FROM topics ORDER BY created_at` as Topic[]
  const accounts = await db`SELECT topic_id FROM youtube_accounts` as { topic_id: string }[]
  const connectedIds = new Set(accounts.map((a) => a.topic_id))

  const today = new Date().toISOString().slice(0, 10)
  const todayVideos = await db`SELECT topic_id FROM videos WHERE created_at >= ${today}` as Video[]
  const countMap: Record<string, number> = {}
  for (const v of todayVideos) {
    countMap[v.topic_id] = (countMap[v.topic_id] || 0) + 1
  }

  return topics.map((t) => ({
    ...t,
    youtube_connected: connectedIds.has(t.id),
    today_count: countMap[t.id] || 0,
  }))
}

export default async function Dashboard() {
  const topics = await getTopicsWithAccounts()

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">대시보드</h1>
      {topics.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <p className="text-lg mb-4">등록된 주제가 없습니다.</p>
          <a href="/topics/new" className="bg-blue-600 text-white px-5 py-2 rounded-md hover:bg-blue-700">
            첫 번째 주제 만들기
          </a>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {topics.map((topic) => (
            <TopicCard key={topic.id} topic={topic} />
          ))}
        </div>
      )}
    </div>
  )
}

function TopicCard({ topic }: { topic: Topic & { youtube_connected: boolean; today_count: number } }) {
  const lastRun = topic.last_run_at
    ? new Date(topic.last_run_at).toLocaleString("ko-KR")
    : "아직 실행 안 됨"

  return (
    <div className="bg-white rounded-xl border p-5 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-semibold text-base">{topic.name}</h2>
          {topic.description && <p className="text-gray-500 text-sm mt-0.5">{topic.description}</p>}
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full ${topic.active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
          {topic.active ? "활성" : "비활성"}
        </span>
      </div>
      <div className="text-sm text-gray-500 space-y-1">
        <div>{topic.youtube_connected ? "✅" : "❌"} YouTube {topic.youtube_connected ? "연결됨" : "미연결"}</div>
        <div>🕐 마지막 실행: {lastRun}</div>
        <div>📹 오늘 생성: {topic.today_count}개</div>
        {topic.keywords && topic.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1">
            {topic.keywords.map((kw) => (
              <span key={kw} className="bg-blue-50 text-blue-600 text-xs px-2 py-0.5 rounded-full">{kw}</span>
            ))}
          </div>
        )}
      </div>
      <div className="flex gap-2 pt-1">
        <a href={`/topics/${topic.id}`} className="flex-1 text-center text-sm border rounded-md py-1.5 hover:bg-gray-50">
          상세 보기
        </a>
        {!topic.youtube_connected && (
          <a href={`/topics/${topic.id}/connect-youtube`} className="flex-1 text-center text-sm bg-red-50 text-red-600 border border-red-200 rounded-md py-1.5 hover:bg-red-100">
            YouTube 연결
          </a>
        )}
        <form action={`/api/topics/${topic.id}/run`} method="POST">
          <button type="submit" className="text-sm bg-blue-600 text-white rounded-md px-3 py-1.5 hover:bg-blue-700">
            ▶ 실행
          </button>
        </form>
      </div>
    </div>
  )
}
