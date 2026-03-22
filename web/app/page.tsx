import { sql, Topic, Video } from "@/lib/db"

async function getTopicsWithAccounts() {
  const db = sql()
  const topics = await db`SELECT * FROM topics ORDER BY created_at` as Topic[]
  const accounts = await db`SELECT topic_id, token_json, channel_name FROM youtube_accounts` as { topic_id: string; token_json: string; channel_name: string | null }[]

  const accountMap: Record<string, { token_json: string; channel_name: string | null }> = {}
  for (const a of accounts) {
    accountMap[a.topic_id] = { token_json: a.token_json, channel_name: a.channel_name }
  }

  const today = new Date().toISOString().slice(0, 10)
  const todayVideos = await db`SELECT topic_id FROM videos WHERE created_at >= ${today}` as Video[]
  const countMap: Record<string, number> = {}
  for (const v of todayVideos) {
    countMap[v.topic_id] = (countMap[v.topic_id] || 0) + 1
  }

  return topics.map((t) => {
    const acc = accountMap[t.id]
    const isConnected = acc && acc.token_json && acc.token_json !== "pending"
    const isPending = acc && acc.token_json === "pending"
    const cfg = (t.config as Record<string, string>) || {}
    return {
      ...t,
      youtube_status: isConnected ? "connected" : isPending ? "pending" : "none",
      channel_name: acc?.channel_name || null,
      today_count: countMap[t.id] || 0,
      content_mode: cfg.content_mode === "ai_prompt" ? "ai_prompt" : "news",
    }
  })
}

type TopicWithStatus = Topic & {
  youtube_status: "connected" | "pending" | "none"
  channel_name: string | null
  today_count: number
  content_mode: "news" | "ai_prompt"
}

export default async function Dashboard() {
  const topics = await getTopicsWithAccounts() as TopicWithStatus[]

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

function TopicCard({ topic }: { topic: TopicWithStatus }) {
  const lastRun = topic.last_run_at
    ? new Date(topic.last_run_at).toLocaleString("ko-KR")
    : "아직 실행 안 됨"

  const ytStatus = {
    connected: { icon: "✅", label: `연결됨${topic.channel_name ? ` — ${topic.channel_name}` : ""}`, color: "text-green-600" },
    pending:   { icon: "⏳", label: "인증 미완료",  color: "text-yellow-600" },
    none:      { icon: "❌", label: "미연결",        color: "text-red-500" },
  }[topic.youtube_status]

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

      <div className="text-sm space-y-1">
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            topic.content_mode === "ai_prompt"
              ? "bg-purple-100 text-purple-700"
              : "bg-blue-100 text-blue-700"
          }`}>
            {topic.content_mode === "ai_prompt" ? "✨ AI 생성" : "📰 뉴스 기반"}
          </span>
          <span className="text-xs text-gray-400">6시간마다 자동 실행</span>
        </div>
        <div className={`flex items-center gap-1 ${ytStatus.color}`}>
          <span>{ytStatus.icon}</span>
          <span>YouTube {ytStatus.label}</span>
        </div>
        <div className="text-gray-500">🕐 마지막 실행: {lastRun}</div>
        <div className="text-gray-500">📹 오늘 생성: {topic.today_count}개</div>
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
        <a href={`/topics/${topic.id}/edit`} className="text-center text-sm border rounded-md px-3 py-1.5 hover:bg-gray-50 text-gray-600">
          편집
        </a>
        {topic.youtube_status !== "connected" && (
          <a
            href={`/topics/${topic.id}/connect-youtube`}
            className={`flex-1 text-center text-sm rounded-md py-1.5 border ${
              topic.youtube_status === "pending"
                ? "bg-yellow-50 text-yellow-700 border-yellow-200 hover:bg-yellow-100"
                : "bg-red-50 text-red-600 border-red-200 hover:bg-red-100"
            }`}
          >
            {topic.youtube_status === "pending" ? "인증 완료하기" : "YouTube 연결"}
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
