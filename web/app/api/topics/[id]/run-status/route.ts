import { NextRequest, NextResponse } from "next/server"

export async function GET(_: NextRequest, { params }: { params: { id: string } }) {
  const token = process.env.GH_TOKEN
  const owner = process.env.GH_OWNER
  const repo  = process.env.GH_REPO || "YTGEN"

  if (!token || !owner) {
    return NextResponse.json({ error: "GH_TOKEN 없음" }, { status: 500 })
  }

  const res = await fetch(
    `https://api.github.com/repos/${owner}/${repo}/actions/workflows/ytgen.yml/runs?per_page=5`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      cache: "no-store",
    }
  )

  if (!res.ok) {
    return NextResponse.json({ error: "GitHub API 오류" }, { status: 500 })
  }

  const data = await res.json()
  const runs = data.workflow_runs || []

  // topic_id가 inputs에 포함된 run 또는 가장 최근 run
  const topicRun = runs.find((r: { display_title: string }) =>
    r.display_title?.includes(params.id)
  ) || runs[0]

  if (!topicRun) {
    return NextResponse.json({ status: "none" })
  }

  return NextResponse.json({
    status: topicRun.status,           // queued | in_progress | completed
    conclusion: topicRun.conclusion,   // success | failure | cancelled | null
    html_url: topicRun.html_url,
    run_number: topicRun.run_number,
    created_at: topicRun.created_at,
  })
}
