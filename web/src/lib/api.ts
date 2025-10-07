import { API_BASE } from "./config";

/**
 * Constructs a full API URL with query parameters.
 */
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

/**
 * Fetches JSON data from an API endpoint.
 */
export async function fetchJSON<T>(
  path: string,
  params: Record<string, string | number | undefined | null> = {}
): Promise<T> {
  const url = apiUrl(path, params); // URL object

  // Use url.toString() to get string for fetch()
  const res = await fetch(url.toString(), { cache: "no-store" });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}
