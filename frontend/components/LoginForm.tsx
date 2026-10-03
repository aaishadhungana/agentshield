"use client";

import { Loader2, Shield } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

type Mode = "login" | "register";

async function postJson(
  url: string,
  body: unknown,
): Promise<{ ok: boolean; detail?: string }> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (response.ok) {
    return { ok: true };
  }
  const data = (await response.json().catch(() => ({}))) as { detail?: string };
  return { ok: false, detail: data.detail ?? "Something went wrong" };
}

export default function LoginForm({ sessionExpired }: { sessionExpired: boolean }) {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const credentials = { email, password };
      if (mode === "register") {
        const registered = await postJson("/api/auth/register", credentials);
        if (!registered.ok) {
          setError(registered.detail ?? "Registration failed");
          return;
        }
      }
      const result = await postJson("/api/auth/login", credentials);
      if (!result.ok) {
        setError(result.detail ?? "Sign in failed");
        return;
      }
      router.push("/");
      router.refresh();
    } catch {
      setError("Cannot reach the server");
    } finally {
      setLoading(false);
    }
  }

  const isRegister = mode === "register";

  return (
    <div className="w-full max-w-sm rounded-xl border border-slate-800 bg-slate-900 p-8 shadow-xl">
      <div className="mb-6 flex items-center gap-2 text-white">
        <Shield className="h-6 w-6 text-emerald-400" />
        <span className="text-lg font-semibold">AgentShield</span>
      </div>
      <h1 className="text-xl font-semibold text-white">
        {isRegister ? "Create an account" : "Sign in"}
      </h1>
      <p className="mt-1 text-sm text-slate-400">
        Runtime security for AI agents
      </p>

      {sessionExpired && !error && (
        <p className="mt-4 rounded-md bg-amber-500/10 px-3 py-2 text-sm text-amber-300">
          Your session expired. Please sign in again.
        </p>
      )}
      {error && (
        <p className="mt-4 rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</p>
      )}

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label htmlFor="email" className="mb-1 block text-sm text-slate-300">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500"
          />
        </div>
        <div>
          <label htmlFor="password" className="mb-1 block text-sm text-slate-300">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            minLength={isRegister ? 12 : 1}
            maxLength={128}
            autoComplete={isRegister ? "new-password" : "current-password"}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500"
          />
          {isRegister && (
            <p className="mt-1 text-xs text-slate-500">Use at least 12 characters.</p>
          )}
        </div>
        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-slate-950 hover:bg-emerald-400 disabled:opacity-60"
        >
          {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          {isRegister ? "Create account" : "Sign in"}
        </button>
      </form>

      <button
        type="button"
        onClick={() => {
          setMode(isRegister ? "login" : "register");
          setError(null);
        }}
        className="mt-4 text-sm text-slate-400 hover:text-white"
      >
        {isRegister ? "Already have an account? Sign in" : "New here? Create an account"}
      </button>
    </div>
  );
}