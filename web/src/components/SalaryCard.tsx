"use client";
import React, { useEffect, useState } from "react";
import StatCard from "./StatCard";
import { fetchJSON } from "@/lib/api";

type SalaryRow = { p25: number | null; median: number | null; p75: number | null; n: number };

export default function SalaryCard({ skill, city }: { skill: string; city?: string }) {
  const [data, setData] = useState<SalaryRow | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    if (!skill) { setData(null); return; }

    fetchJSON<SalaryRow>("/api/metrics/salary_by_skill", {  params: { skill, city: city || undefined }})
      .then(d => mounted && setData(d))
      .catch(e => mounted && setErr(String(e)));
    return () => { mounted = false; };
  }, [skill, city]);

  const fmt = (n: number | null) => (n == null ? "—" : `$${(n/1000).toFixed(0)}k`);

  return (
    <div className="rounded-2xl border border-teal-200/60 bg-white shadow-sm p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-wide text-teal-700/80">Salary (USD)</div>
          <div className="text-xs text-gray-500">for {skill} {city ? `in ${city}` : ""}</div>
        </div>
      </div>
      {err && <div className="text-red-500 text-sm mt-2">Error: {err}</div>}
      <div className="grid grid-cols-3 gap-3 mt-3">
        <StatCard title="p25"   value={fmt(data?.p25 ?? null)} />
        <StatCard title="median" value={fmt(data?.median ?? null)} />
        <StatCard title="p75"   value={fmt(data?.p75 ?? null)} subtitle={`${data?.n ?? 0} samples`} />
      </div>
    </div>
  );
}
