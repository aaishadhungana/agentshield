import { Shield } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import LogoutButton from "@/components/LogoutButton";

export default function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 bg-slate-900/60">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2 font-semibold text-white">
              <Shield className="h-5 w-5 text-emerald-400" />
              AgentShield
            </Link>
            <nav className="flex items-center gap-5 text-sm text-slate-400">
              <Link href="/" className="hover:text-white">
                Dashboard
              </Link>
              <Link href="/events" className="hover:text-white">
                Events
              </Link>
            </nav>
          </div>
          <LogoutButton />
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}