import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { TOKEN_COOKIE } from "@/lib/constants";

export async function POST() {
  (await cookies()).delete(TOKEN_COOKIE);
  return NextResponse.json({ ok: true });
}