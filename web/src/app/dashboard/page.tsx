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
    // NEW: params go under { params: {...} }
    fetchJSON<Skill[]>("/api/skills/top", { params: { limit: 10, days: 90 } })
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
          {/* City – dynamic (from /api/cities) */}
          <div className="flex flex-col">
            <label className="text-sm opacity-70">City</label>
            <CitySelect value={city} onChange={setCity} />
          </div>

          {/* Skill input for salary tile */}
          <div className="flex items-center gap-2">
            <span className="text-sm opacity-70">Skill:</span>
            <input
              value={skillQuery}
              onChange={(e) => setSkillQuery(e.target.value)}
              className="rounded border border-teal-200 bg-white px-3 py-2 text-slate-900"
              placeholder="python"
            />
          </div>

          <Link
            href="/jobs"
            className="inline-flex items-center rounded border border-teal-300 px-3 py-2 hover:bg-teal-50"
            title="Go to Job Search"
          >
            🔎 Browse Jobs
          </Link>
        </div>
      </div>

      {/* Tiles */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Rising skills can now (optionally) take a city; it's OK to pass undefined */}
        <RisingSkillsCard city={city} />
        {/* Salary card accepts { skill, city? } */}
        <SalaryCard skill={skillQuery} city={city} />
      </div>

      {/* Table: Top skills (90 days) */}
      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Top Skills (last 90 days)</h2>

        {err && <div className="text-red-500">Error: {err}</div>}
        {loading && <div className="opacity-70">Loading…</div>}

        {!loading && !err && (
          <table className="min-w-full border border-teal-200 bg-white">
            <thead className="bg-teal-50">
              <tr>
                <th className="px-4 py-2 text-left border border-teal-200">
                  Skill
                </th>
                <th className="px-4 py-2 text-left border border-teal-200">
                  Count
                </th>
              </tr>
            </thead>
            <tbody>
              {skills.map((s) => (
                <tr key={s.skill} className="hover:bg-teal-50">
                  <td className="px-4 py-2 border border-teal-200">
                    {s.skill}
                  </td>
                  <td className="px-4 py-2 border border-teal-200">
                    {s.cnt}
                  </td>
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
