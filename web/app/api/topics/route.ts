import { NextRequest, NextResponse } from "next/server"
import { sql } from "@/lib/db"

export async function GET() {
  try {
    const db = sql()
    const topics = await db`SELECT * FROM topics ORDER BY created_at`
    return NextResponse.json(topics)
  } catch (e: unknown) {
    return NextResponse.json({ error: (e as Error).message }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  const { name, description, keywords, config } = body

  if (!name?.trim()) {
    return NextResponse.json({ error: "name은 필수입니다." }, { status: 400 })
  }

  try {
    const db = sql()
    const rows = await db`
      INSERT INTO topics (name, description, keywords, config)
      VALUES (${name.trim()}, ${description?.trim() || null}, ${keywords || []}, ${JSON.stringify(config || {})})
      RETURNING *
    `
    return NextResponse.json(rows[0], { status: 201 })
  } catch (e: unknown) {
    return NextResponse.json({ error: (e as Error).message }, { status: 500 })
  }
}
