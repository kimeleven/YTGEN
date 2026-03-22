import { NextRequest, NextResponse } from "next/server"
import { triggerWorkflow } from "@/lib/github"

export async function POST(_: NextRequest, { params }: { params: { id: string } }) {
  const result = await triggerWorkflow(params.id)

  if (result.ok) {
    return NextResponse.json({ ok: true })
  }

  return NextResponse.json({ error: result.message }, { status: 500 })
}
