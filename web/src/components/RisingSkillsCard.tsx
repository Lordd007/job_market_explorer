"use client";
import React, { useEffect, useState } from "react";
import { fetchJSON } from "@/lib/api";

type RisingRow = {
  skill: string;
  recent_cnt: number;
  base_cnt: number;
  pct_delta: number | null;
};

export default function RisingSkillsCard({ city }: { city?: string }) {
  const [rows, setRows] = useState<RisingRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    fetchJSON<RisingRow[]>("/api/skills/rising", {
      city: city || undefined,
      weeks: 8,
      baseline_weeks: 8,
      min_support: 20,
    })
      .then(d => mounted && setRows(d))
      .catch(e => mounted && setError(String(e)))
      .finally(() => mounted && setLoading(false));
    return () => { mounted = false; };
  }, [city]);

  return (
    <div className="rounded-2xl border border-teal-200/60 bg-white shadow-sm p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-wide text-teal-700/80">Rising skills</div>
          <div className="text-xs text-gray-500">last 8 weeks vs prior 8</div>
        </div>
        {city && <div className="text-xs rounded-full bg-teal-50 px-2 py-0.5 border border-teal-200">{city}</div>}
      </div>

      {error && <div className="text-red-500 text-sm mt-2">Error: {error}</div>}
      {loading && <div className="text-gray-500 text-sm mt-2">Loading…</div>}

      {!loading && !error && (
        <table className="w-full text-sm mt-3">
          <thead>
            <tr className="text-left text-gray-500 border-b">
              <th className="py-1">Skill</th>
              <th className="py-1">Recent</th>
              <th className="py-1">Δ%</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 8).map(r => (
              <tr key={r.skill} className="border-b last:border-0">
                <td className="py-1 font-medium">{r.skill}</td>
                <td className="py-1">{r.recent_cnt}</td>
                <td className="py-1">
                  {r.pct_delta === null ? "—" : (
                    <span className={r.pct_delta >= 0 ? "text-green-600" : "text-red-600"}>
                      {r.pct_delta >= 0 ? "+" : ""}{r.pct_delta}%
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td className="py-2 text-gray-500" colSpan={3}>No data</td></tr>}
          </tbody>
        </table>
      )}
    </div>
  );
}
