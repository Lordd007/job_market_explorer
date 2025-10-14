"use client";
import React, { useEffect, useState } from "react";
import { fetchJSON } from "@/lib/api";

export default function CitySelect({ value, onChange }: { value?: string; onChange: (v?: string)=>void }) {
  const [cities, setCities] = useState<{city:string; n:number}[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let m = true;
    fetchJSON<{city:string; n:number}[]>("/api/cities", { min_support: 50 })
      .then(d => m && setCities(d))
      .catch(e => m && setErr(String(e)));
    return () => { m = false; };
  }, []);

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-gray-600">City:</span>
      <select
        value={value || ""}
        onChange={(e) => onChange(e.target.value || undefined)}
        className="rounded-md border px-2 py-1"
      >
        <option value="">All</option>
        {cities.map(c => (
          <option key={c.city} value={c.city}>{c.city} ({c.n})</option>
        ))}
      </select>
      {err && <span className="text-xs text-red-500">{err}</span>}
    </div>
  );
}
