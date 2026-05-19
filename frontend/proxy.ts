import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED = ["/applications", "/cv", "/search"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = PROTECTED.some((p) => pathname.startsWith(p));
  if (!isProtected) return NextResponse.next();

  const authed = request.cookies.get("sw_authed")?.value === "1";
  if (!authed) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/applications/:path*", "/cv/:path*", "/search/:path*"],
};
