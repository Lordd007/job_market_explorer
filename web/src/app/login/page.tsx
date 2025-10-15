// web/src/app/login/page.tsx
"use client";
import React, { useState } from "react";
import { API_BASE } from "@/lib/config";
import { saveToken } from "@/lib/auth";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [code, setCode] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [token, setToken] = useState<string | null>(null);

  async function requestCode(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setStatus(null);
    try {
      const url = `${API_BASE.replace(/\/$/, "")}/api/auth/request_code`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSent(true);
      setStatus("We emailed you a 6-digit code. It expires in 10 minutes.");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setStatus(`Error: ${msg}`);
    } finally {
      setBusy(false);
    }
  }

  async function verify(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setStatus(null);
    try {
      const url = `${API_BASE.replace(/\/$/, "")}/api/auth/verify_code`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      saveToken(data.access_token);
      setToken(data.access_token);
      setStatus("Logged in! You can now set Preferences or browse Jobs.");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setStatus(`Error: ${msg}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="max-w-md mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Log in</h1>

      {!sent ? (
        <form
          onSubmit={requestCode}
          className="rounded-xl border border-teal-200 bg-white p-4 space-y-3"
        >
          <div>
            <label className="text-sm text-gray-600">Email</label>
            <input
              type="email"
              required
              className="w-full rounded border border-gray-300 px-3 py-2"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>
          <button
            disabled={busy}
            className="px-4 py-2 rounded bg-teal-600 text-white disabled:opacity-60"
          >
            {busy ? "Sending…" : "Send code"}
          </button>
          {status && <div className="text-sm text-gray-600">{status}</div>}
        </form>
      ) : (
        <form
          onSubmit={verify}
          className="rounded-xl border border-teal-200 bg-white p-4 space-y-3"
        >
          <div>
            <div className="text-sm text-gray-600">
              Code sent to <b>{email}</b>
            </div>
            <label className="text-sm text-gray-600">6-digit code</label>
            <input
              required
              minLength={6}
              maxLength={6}
              className="w-full rounded border border-gray-300 px-3 py-2"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="••••••"
            />
          </div>
          <button
            disabled={busy}
            className="px-4 py-2 rounded bg-teal-600 text-white disabled:opacity-60"
          >
            {busy ? "Verifying…" : "Verify & Log in"}
          </button>
          {status && <div className="text-sm text-gray-600">{status}</div>}

          {token && (
            <div className="mt-3 text-sm">
              <Link href="/preferences" className="underline text-teal-700">
                Set your preferences
              </Link>{" "}
              or{" "}
              <Link href="/jobs" className="underline text-teal-700">
                browse jobs
              </Link>
              .
            </div>
          )}
        </form>
      )}
    </main>
  );
}
