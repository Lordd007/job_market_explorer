"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchJSON } from "@/lib/api";
import { API_BASE } from "@/lib/config";

type Skill = { skill: string; cnt: number };

export default function DashboardPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    setLoading(true);
    setErr(null);
    fetchJSON<Skill[]>("/api/skills/top", { limit: 10, days: 90 })
      .then(setSkills)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="p-6 space-y-4">
      <div className="flex items-end justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold">Top Skills (last 90 days)</h1>
          <p className="text-sm opacity-70">Live from {API_BASE}</p>
        </div>

        {/* Navigate to Job Search */}
        <Link
          href="/jobs"
          className="inline-flex items-center rounded border px-3 py-2 hover:bg-neutral-900"
          title="Go to Job Search"
        >
          🔎 Browse Jobs
        </Link>
      </div>

      {err && <div className="text-red-400">Error: {err}</div>}
      {loading && <div className="opacity-70">Loading…</div>}

      {!loading && !err && (
        <table className="min-w-full border border-neutral-700">
          <thead className="bg-neutral-900/50">
            <tr>
              <th className="px-4 py-2 text-left border border-neutral-800">Skill</th>
              <th className="px-4 py-2 text-left border border-neutral-800">Count</th>
            </tr>
          </thead>
          <tbody>
            {skills.map((s) => (
              <tr key={s.skill} className="hover:bg-neutral-900/40">
                <td className="px-4 py-2 border border-neutral-800">{s.skill}</td>
                <td className="px-4 py-2 border border-neutral-800">{s.cnt}</td>
              </tr>
            ))}
            {skills.length === 0 && (
              <tr>
                <td className="px-4 py-3 opacity-70" colSpan={2}>
                  No data yet. Try running the nightly ingest.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </main>
  );
}
