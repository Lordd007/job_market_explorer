export function saveToken(t: string) {
  try { localStorage.setItem("jme_token", t); } catch {}
}
export function getToken(): string | null {
  try { return localStorage.getItem("jme_token"); } catch { return null; }
}
export function clearToken() {
  try { localStorage.removeItem("jme_token"); } catch {}
}
export function isAuthed(): boolean {
  return !!getToken();
}
