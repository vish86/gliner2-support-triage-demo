import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body = await req.json();

  const pyUrl = process.env.PY_URL || "http://127.0.0.1:8000";
  const resp = await fetch(`${pyUrl}/draft`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await resp.json();
  return NextResponse.json(data, { status: resp.status });
}
