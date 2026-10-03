import { NextResponse, type NextRequest } from "next/server";

import { TOKEN_COOKIE } from "@/lib/constants";

export function proxy(request: NextRequest) {
  if (!request.cookies.get(TOKEN_COOKIE)) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!login|api|_next|favicon.ico).*)"],
};