import { NextResponse } from "next/server";

import { BACKEND_URL } from "@/lib/api";

function parseCredentials(value: unknown): { email: string; password: string } | null {
  if (typeof value !== "object" || value === null) return null;
  const { email, password } = value as Record<string, unknown>;
  if (typeof email !== "string" || typeof password !== "string") return null;
  return { email, password };
}

export async function POST(request: Request) {
  const credentials = parseCredentials(await request.json().catch(() => null));
  if (!credentials) {
    return NextResponse.json({ detail: "Invalid request" }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "Cannot reach the AgentShield API" }, { status: 502 });
  }

  if (upstream.status === 409) {
    return NextResponse.json({ detail: "That email is already registered" }, { status: 409 });
  }
  if (upstream.status === 422) {
    return NextResponse.json(
      { detail: "Enter a valid email and a password of 12 to 128 characters" },
      { status: 400 },
    );
  }
  if (!upstream.ok) {
    return NextResponse.json({ detail: "Registration failed" }, { status: 502 });
  }
  return NextResponse.json({ ok: true }, { status: 201 });
}