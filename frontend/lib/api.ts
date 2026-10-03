import "server-only";

import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { TOKEN_COOKIE } from "@/lib/constants";

export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

async function request(path: string): Promise<Response> {
  const token = (await cookies()).get(TOKEN_COOKIE)?.value;
  if (!token) {
    redirect("/login");
  }

  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}${path}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
  } catch {
    throw new Error("Cannot reach the AgentShield API");
  }

  if (response.status === 401) {
    redirect("/login?expired=1");
  }
  return response;
}

export async function apiFetch<T>(path: string): Promise<T> {
  const response = await request(path);
  if (response.status === 404) {
    notFound();
  }
  if (!response.ok) {
    throw new Error(`The API returned an error (${response.status})`);
  }
  return (await response.json()) as T;
}

export async function apiFetchOrNull<T>(path: string): Promise<T | null> {
  const response = await request(path);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`The API returned an error (${response.status})`);
  }
  return (await response.json()) as T;
}