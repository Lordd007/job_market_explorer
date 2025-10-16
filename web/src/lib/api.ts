import { API_BASE } from "./config";

/** Build a full API URL with query params */
export function apiUrl(
  path: string,
  params: Record<string, string | number | undefined | null> = {}
): URL {
  const base = API_BASE.endsWith("/") ? API_BASE : `${API_BASE}/`;
  const url = new URL(path.replace(/^\//, ""), base);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && String(v).length) {
      url.searchParams.set(k, String(v));
    }
  }
  return url;
}

/** Fetch JSON with optional opts (method, headers, Authorization, json body, cache) */
export async function fetchJSON<T>(
  path: string,
  params?: Record<string, string | number | undefined | null>,
  opts?: {
    method?: string;
    headers?: Record<string, string>;
    authorization?: string;
    json?: unknown;
    cache?: RequestCache;
  }
): Promise<T> {
  const url = apiUrl(path, params).toString();

  const headers: Record<string, string> = { ...(opts?.headers || {}) };
  if (opts?.authorization) headers["Authorization"] = opts.authorization;
  if (opts?.json !== undefined && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(url, {
    method: opts?.method || (opts?.json !== undefined ? "POST" : "GET"),
    headers,
    body: opts?.json !== undefined ? JSON.stringify(opts.json) : undefined,
    cache: opts?.cache || "no-store",
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}
