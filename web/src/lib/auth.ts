const TOKEN_KEY = "jme_token";

export function saveToken(t: string) {
  try { localStorage.setItem(TOKEN_KEY, t); } catch {}
}
export function getToken(): string | null {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}
export function clearToken() {
  try { localStorage.removeItem(TOKEN_KEY); } catch {}
}
export function isAuthed(): boolean {
  return !!getToken();
}
export function authHeaders() {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}
