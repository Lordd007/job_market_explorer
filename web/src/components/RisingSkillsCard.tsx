"use client";
import React, { useEffect, useState } from "react";
import { fetchJSON } from "@/lib/api";

type RisingRow = {
  skill: string;
  current: number;
  baseline: number;
  delta: number;   // fraction (e.g., 0.42 = +42%)
  support: number; // current + baseline
};

type Props = {
  city?: string;         // <-- make city optional
  weeks?: number;        // default 8
  baselineWeeks?: number;// default 8
  minSupport?: number;   // default 20
};

export default function RisingSkillsCard({
  city,
  weeks = 2,
  baselineWeeks = 2,
  minSupport = 20,
}: Props) {
  const [rows, setRows] = useState<RisingRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    const params: Record<string, string | number> = {
      weeks,
      baseline_weeks: baselineWeeks,
      min_support: minSupport,
    };
    if (city) params.city = city;

    fetchJSON<RisingRow[]>("/api/skills/rising", params)
      .then((d) => mounted && setRows(d))
      .catch((e) => mounted && setError(String(e)))
      .finally(() => mounted && setLoading(false));

    return () => {
      mounted = false;
    };
  }, [city, weeks, baselineWeeks, minSupport]);

  return (
    <div className="rounded-2xl border border-teal-200/60 bg-white shadow-sm p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-wide text-teal-700/80">Rising skills</div>
          <div className="text-xs text-gray-500">
            last {weeks} weeks vs prior {baselineWeeks}
          </div>
        </div>
        {city && (
          <div className="text-xs rounded-full bg-teal-50 px-2 py-0.5 border border-teal-200">
            {city}
          </div>
        )}
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
            {rows.slice(0, 8).map((r) => (
              <tr key={r.skill} className="border-b last:border-0">
                <td className="py-1 font-medium">{r.skill}</td>
                <td className="py-1">{r.current}</td>
                <td className="py-1">
                  {Number.isFinite(r.delta)
                    ? `${Math.round(r.delta * 100)}%`
                    : "—"}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td className="py-2 text-gray-500" colSpan={3}>
                  No data
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
