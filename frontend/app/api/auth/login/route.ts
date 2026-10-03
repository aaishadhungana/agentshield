import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { BACKEND_URL } from "@/lib/api";
import { TOKEN_COOKIE } from "@/lib/constants";

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
    upstream = await fetch(`${BACKEND_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "Cannot reach the AgentShield API" }, { status: 502 });
  }

  if (upstream.status === 401) {
    return NextResponse.json({ detail: "Invalid email or password" }, { status: 401 });
  }
  if (upstream.status === 422) {
    return NextResponse.json({ detail: "Enter a valid email address" }, { status: 400 });
  }
  if (!upstream.ok) {
    return NextResponse.json({ detail: "Sign in failed" }, { status: 502 });
  }

  const data = (await upstream.json()) as { access_token: string; expires_in: number };
  (await cookies()).set(TOKEN_COOKIE, data.access_token, {
    httpOnly: true,
    sameSite: "strict",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: data.expires_in,
  });
  return NextResponse.json({ ok: true });
}