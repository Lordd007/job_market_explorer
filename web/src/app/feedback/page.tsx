"use client";
import React, { useState } from "react";
import { API_BASE } from "@/lib/config";

type Form = { name: string; email: string; subject: string; category?: string; message: string };

export default function FeedbackPage() {
  const [form, setForm] = useState<Form>({ name: "", email: "", subject: "", message: "" });
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setErr(null);
    try {
      const url = `${API_BASE.replace(/\/$/, "")}/api/feedback`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type":"application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setDone(true);
      setForm({ name: "", email: "", subject: "", message: "" });
    } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setErr(msg);
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="space-y-6">
      <h1 className="text-2xl font-bold">Feedback</h1>

      {done && (
        <div className="rounded-md border border-teal-300 bg-teal-50 px-3 py-2 text-teal-800">
          Thank you for your feedback! Our team will look into the issue.
        </div>
      )}
      {err && <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-red-700">Error: {err}</div>}

      <form onSubmit={onSubmit} className="rounded-xl border border-teal-200 bg-white p-4 space-y-3 max-w-2xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="text-sm text-gray-600">Name</label>
            <input
              required
              className="w-full rounded border border-gray-300 px-3 py-2"
              value={form.name}
              onChange={(e)=>setForm(f => ({...f, name: e.target.value}))}
            />
          </div>
          <div>
            <label className="text-sm text-gray-600">Email</label>
            <input
              required
              type="email"
              className="w-full rounded border border-gray-300 px-3 py-2"
              value={form.email}
              onChange={(e)=>setForm(f => ({...f, email: e.target.value}))}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="text-sm text-gray-600">Subject</label>
            <input
              required
              className="w-full rounded border border-gray-300 px-3 py-2"
              value={form.subject}
              onChange={(e)=>setForm(f => ({...f, subject: e.target.value}))}
            />
          </div>
          <div>
            <label className="text-sm text-gray-600">Category (optional)</label>
            <input
              className="w-full rounded border border-gray-300 px-3 py-2"
              placeholder="bug, idea, data-issue…"
              value={form.category || ""}
              onChange={(e)=>setForm(f => ({...f, category: e.target.value}))}
            />
          </div>
        </div>

        <div>
          <label className="text-sm text-gray-600">Message</label>
          <textarea
            required
            className="w-full rounded border border-gray-300 px-3 py-2 h-40"
            value={form.message}
            onChange={(e)=>setForm(f => ({...f, message: e.target.value}))}
          />
        </div>

        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 rounded bg-teal-600 text-white disabled:opacity-60"
        >
          {saving ? "Sending…" : "Submit feedback"}
        </button>
      </form>
    </main>
  );
}
