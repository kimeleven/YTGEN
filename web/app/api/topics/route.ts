import { NextRequest, NextResponse } from "next/server"
import { createServiceClient } from "@/lib/supabase"

export async function GET() {
  const sb = createServiceClient()
  const { data, error } = await sb.from("topics").select("*").order("created_at")
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  const { name, description, keywords } = body

  if (!name?.trim()) {
    return NextResponse.json({ error: "name은 필수입니다." }, { status: 400 })
  }

  const sb = createServiceClient()
  const { data, error } = await sb
    .from("topics")
    .insert({ name: name.trim(), description: description?.trim() || null, keywords: keywords || [] })
    .select()
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data, { status: 201 })
}
