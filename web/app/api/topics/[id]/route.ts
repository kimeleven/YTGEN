import { NextRequest, NextResponse } from "next/server"
import { createServiceClient } from "@/lib/supabase"

export async function GET(_: NextRequest, { params }: { params: { id: string } }) {
  const sb = createServiceClient()
  const { data, error } = await sb.from("topics").select("*").eq("id", params.id).single()
  if (error) return NextResponse.json({ error: error.message }, { status: 404 })
  return NextResponse.json(data)
}

export async function PUT(req: NextRequest, { params }: { params: { id: string } }) {
  const body = await req.json()
  const sb = createServiceClient()
  const { data, error } = await sb.from("topics").update(body).eq("id", params.id).select().single()
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}

export async function DELETE(_: NextRequest, { params }: { params: { id: string } }) {
  const sb = createServiceClient()
  const { error } = await sb.from("topics").delete().eq("id", params.id)
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return new NextResponse(null, { status: 204 })
}
