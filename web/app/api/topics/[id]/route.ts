import { NextRequest, NextResponse } from "next/server"
import { sql } from "@/lib/db"

export async function GET(_: NextRequest, { params }: { params: { id: string } }) {
  try {
    const db = sql()
    const rows = await db`SELECT * FROM topics WHERE id = ${params.id}`
    if (rows.length === 0) return NextResponse.json({ error: "Not found" }, { status: 404 })
    return NextResponse.json(rows[0])
  } catch (e: unknown) {
    return NextResponse.json({ error: (e as Error).message }, { status: 500 })
  }
}

export async function PUT(req: NextRequest, { params }: { params: { id: string } }) {
  const body = await req.json()
  const { name, description, keywords, active } = body

  try {
    const db = sql()
    const rows = await db`
      UPDATE topics
      SET
        name        = COALESCE(${name ?? null}, name),
        description = COALESCE(${description ?? null}, description),
        keywords    = COALESCE(${keywords ?? null}, keywords),
        active      = COALESCE(${active ?? null}, active)
      WHERE id = ${params.id}
      RETURNING *
    `
    if (rows.length === 0) return NextResponse.json({ error: "Not found" }, { status: 404 })
    return NextResponse.json(rows[0])
  } catch (e: unknown) {
    return NextResponse.json({ error: (e as Error).message }, { status: 500 })
  }
}

export async function DELETE(_: NextRequest, { params }: { params: { id: string } }) {
  try {
    const db = sql()
    await db`DELETE FROM topics WHERE id = ${params.id}`
    return new NextResponse(null, { status: 204 })
  } catch (e: unknown) {
    return NextResponse.json({ error: (e as Error).message }, { status: 500 })
  }
}
