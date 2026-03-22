"use client"

import { useState, useEffect, useRef } from "react"

type RunStatus = "idle" | "triggering" | "queued" | "in_progress" | "success" | "failure" | "cancelled"

export default function RunButton({ topicId }: { topicId: string }) {
  const [status, setStatus] = useState<RunStatus>("idle")
  const [runUrl, setRunUrl] = useState<string | null>(null)
  const [error, setError] = useState("")
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  function stopPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  async function pollStatus() {
    try {
      const res = await fetch(`/api/topics/${topicId}/run-status`)
      const data = await res.json()

      if (data.status === "completed") {
        setStatus(data.conclusion === "success" ? "success" : data.conclusion === "failure" ? "failure" : "cancelled")
        if (data.html_url) setRunUrl(data.html_url)
        stopPolling()
      } else if (data.status === "in_progress") {
        setStatus("in_progress")
        if (data.html_url) setRunUrl(data.html_url)
      } else if (data.status === "queued") {
        setStatus("queued")
        if (data.html_url) setRunUrl(data.html_url)
      }
    } catch {
      // 폴링 중 일시적 오류는 무시
    }
  }

  async function handleRun() {
    setStatus("triggering")
    setError("")
    setRunUrl(null)

    try {
      const res = await fetch(`/api/topics/${topicId}/run`, { method: "POST" })
      const data = await res.json()

      if (!res.ok) {
        setError(data.error || "실행 요청 실패")
        setStatus("idle")
        return
      }

      setStatus("queued")
      // 5초 후 폴링 시작 (Actions가 등록되는 시간 여유)
      setTimeout(() => {
        pollRef.current = setInterval(pollStatus, 8000)
      }, 5000)
    } catch {
      setError("네트워크 오류")
      setStatus("idle")
    }
  }

  useEffect(() => () => stopPolling(), [])

  const statusConfig = {
    idle:       { label: "▶ 지금 실행", bg: "bg-blue-600 hover:bg-blue-700", disabled: false },
    triggering: { label: "요청 중...",   bg: "bg-blue-400",                    disabled: true  },
    queued:     { label: "⏳ 대기 중...", bg: "bg-yellow-500",                  disabled: true  },
    in_progress:{ label: "⚙️ 실행 중...", bg: "bg-orange-500",                  disabled: true  },
    success:    { label: "✅ 완료",       bg: "bg-green-600 hover:bg-green-700", disabled: false },
    failure:    { label: "❌ 실패",       bg: "bg-red-600 hover:bg-red-700",     disabled: false },
    cancelled:  { label: "⚠️ 취소됨",    bg: "bg-gray-500 hover:bg-gray-600",   disabled: false },
  }[status]

  return (
    <div className="flex flex-col items-end gap-2">
      <button
        onClick={status === "idle" || status === "success" || status === "failure" || status === "cancelled" ? handleRun : undefined}
        disabled={statusConfig.disabled}
        className={`text-sm text-white rounded-md px-4 py-1.5 transition-colors ${statusConfig.bg} disabled:cursor-not-allowed`}
      >
        {statusConfig.label}
      </button>

      {error && (
        <p className="text-xs text-red-500">{error}</p>
      )}

      {runUrl && (
        <a
          href={runUrl}
          target="_blank"
          className="text-xs text-blue-600 hover:underline"
        >
          GitHub Actions 로그 보기 →
        </a>
      )}

      {(status === "queued" || status === "in_progress") && (
        <p className="text-xs text-gray-400">영상 생성에 약 10~20분 소요됩니다.</p>
      )}
    </div>
  )
}
