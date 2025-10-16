"use client";
import { useEffect, useState } from "react";
import { fetchJSON } from "@/lib/api";

type Rising = { skill: string; current: number; baseline: number; delta: number; support: number };

export default function RisingSkillsCard({ weeks=8, baselineWeeks=8, minSupport=20 }:
  { weeks?: number; baselineWeeks?: number; minSupport?: number; }) {

  const [data, setData] = useState<Rising[]>([]);
  const [err, setErr] = useState<string|null>(null);

  useEffect(() => {
    setErr(null);
    fetchJSON<Rising[]>("/api/skills/rising", { weeks, baseline_weeks: baselineWeeks, min_support: minSupport })
      .then(setData)
      .catch(e => setErr(String(e)));
  }, [weeks, baselineWeeks, minSupport]);

  if (err) return <div className="text-red-500">Error: {err}</div>;
  if (!data.length) return <div className="opacity-60">No rising skills yet</div>;

  return (
    <ul className="text-sm">
      {data.slice(0,8).map((r) => (
        <li key={r.skill} className="flex justify-between">
          <span>{r.skill}</span>
          <span className="tabular-nums">
            {r.delta >= 50 ? "↑ huge" : `${Math.round(r.delta * 100)}%`}
          </span>
        </li>
      ))}
    </ul>
  );
}