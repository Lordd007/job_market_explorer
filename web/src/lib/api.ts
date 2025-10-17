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

export type FetchJSONOpts = {
  params?: Record<string, string | number | undefined | null>;
  method?: string;
  headers?: Record<string, string>;
  json?: unknown;
  cache?: RequestCache;
};

export async function fetchJSON<T>(path: string, opts: FetchJSONOpts = {}): Promise<T> {
  const { params = {}, method = "GET", headers = {}, json, cache = "no-store" } = opts;
  const url = apiUrl(path, params);
  const res = await fetch(url.toString(), {
    method,
    cache,
    headers: { ...(json ? { "Content-Type": "application/json" } : {}), ...headers },
    body: json ? JSON.stringify(json) : undefined,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return (await res.json()) as T;
}