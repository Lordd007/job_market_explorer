"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchJSON } from "@/lib/api";
import { API_BASE } from "@/lib/config";
import CitySelect from "@/components/CitySelect";
import RisingSkillsCard from "@/components/RisingSkillsCard";
import SalaryCard from "@/components/SalaryCard";

type Skill = { skill: string; cnt: number };

export default function DashboardPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // tiles
  const [city, setCity] = useState<string | undefined>(undefined);
  const [skillQuery, setSkillQuery] = useState<string>("python");

  useEffect(() => {
    setLoading(true);
    setErr(null);
    fetchJSON<Skill[]>("/api/skills/top", { limit: 10, days: 90 })
      .then(setSkills)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="p-6 space-y-6">
      <div className="flex items-end justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold">Insights</h1>
          <p className="text-sm opacity-70">Live from {API_BASE}</p>
        </div>

        <div className="flex items-center gap-4">
          <CitySelect value={city} onChange={setCity} />
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Skill:</span>
            <input
              value={skillQuery}
              onChange={(e) => setSkillQuery(e.target.value)}
              className="rounded-md border border-neutral-700 bg-neutral-900/40 px-2 py-1"
              placeholder="python"
            />
          </div>
          <Link
            href="/jobs"
            className="inline-flex items-center rounded border border-neutral-700 px-3 py-2 hover:bg-neutral-900"
            title="Go to Job Search"
          >
            🔎 Browse Jobs
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RisingSkillsCard city={city} />
        <SalaryCard skill={skillQuery} city={city} />
      </div>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Top Skills (last 90 days)</h2>

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
      </section>
    </main>
  );
}
