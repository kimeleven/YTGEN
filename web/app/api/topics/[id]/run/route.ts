import { NextRequest, NextResponse } from "next/server"
import { triggerWorkflow } from "@/lib/github"

export async function POST(_: NextRequest, { params }: { params: { id: string } }) {
  const result = await triggerWorkflow(params.id)

  if (result.ok) {
    // 웹 폼에서 POST하면 대시보드로 리다이렉트
    return NextResponse.redirect(new URL("/", process.env.NEXTAUTH_URL || "http://localhost:3000"), 303)
  }

  return NextResponse.json({ error: result.message }, { status: 500 })
}
