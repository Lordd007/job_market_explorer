// web/src/lib/api.ts
import { API_BASE } from "./config";

export type FetchJSONOpts = {
  /** ?q=…&page=…  — null/undefined are skipped, booleans are stringified  */
  params?: Record<string, string | number | boolean | null | undefined>;
  /** Extra headers, e.g. { authorization: `Bearer ${t}` } */
  headers?: Record<string, string>;
  /** HTTP method (kept flexible, same as fetch) */
  method?: RequestInit["method"];
  /** Body to be JSON.stringify'ed */
  json?: unknown;
  /** Optional fetch cache hint, default "no-store" for API calls */
  cache?: RequestCache;
};

export async function fetchJSON<T = unknown>(
  path: string,
  opts: FetchJSONOpts = {}
): Promise<T> {
  const base = API_BASE.endsWith("/") ? API_BASE : `${API_BASE}/`;
  const url = new URL(path.replace(/^\//, ""), base);

  // Build query string
  if (opts.params) {
    for (const [k, v] of Object.entries(opts.params)) {
      if (v === undefined || v === null) continue;
      url.searchParams.set(k, typeof v === "boolean" ? String(v) : String(v));
    }
  }

  const init: RequestInit = {
    method: opts.method ?? "GET",
    headers: { "Content-Type": "application/json", ...(opts.headers ?? {}) },
    // For API calls we don’t want Next/Fetch to cache unless you explicitly pass something else
    cache: opts.cache ?? "no-store",
  };

  if (opts.json !== undefined) {
    init.body = JSON.stringify(opts.json);
  }

  const res = await fetch(url.toString(), init);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json() as Promise<T>;
}
