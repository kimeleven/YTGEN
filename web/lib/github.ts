/**
 * GitHub Actions workflow_dispatch 트리거
 */
export async function triggerWorkflow(topicId?: string): Promise<{ ok: boolean; message: string }> {
  const token = process.env.GH_TOKEN
  const owner = process.env.GH_OWNER
  const repo  = process.env.GH_REPO || "YTGEN"

  if (!token || !owner) {
    return { ok: false, message: "GH_TOKEN 또는 GH_OWNER 환경변수 없음" }
  }

  const res = await fetch(
    `https://api.github.com/repos/${owner}/${repo}/actions/workflows/ytgen.yml/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ref: "web-publish",
        inputs: topicId ? { topic_id: topicId } : {},
      }),
    }
  )

  if (res.status === 204) {
    return { ok: true, message: "GitHub Actions 실행 요청 완료" }
  }
  const text = await res.text()
  return { ok: false, message: `GitHub API 오류 (${res.status}): ${text}` }
}
