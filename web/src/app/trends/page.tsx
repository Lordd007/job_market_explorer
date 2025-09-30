"use client";
import { useEffect, useMemo, useState } from "react";
import { API_BASE } from "@/lib/config";
import { ALL_CITIES } from "@/data/cities";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

type Row = { week: string; cnt: number };

const SKILLS = [
  "python", "sql", "pandas", "scikit-learn", "kubernetes",
  "airflow", "aws", "pytorch", "tensorflow",
];

export default function Trends() {
  const [skill, setSkill] = useState("python");
  const [weeks, setWeeks] = useState(12);
  const [city, setCity] = useState<string | null>(null);
  const [data, setData] = useState<Row[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const url = new URL(`${API_BASE}/api/skills/trends`);
    url.searchParams.set("skill", skill);
    url.searchParams.set("weeks", String(weeks));
    if (city) url.searchParams.set("city", city);

    setLoading(true);
    fetch(url.toString())
      .then((r) => r.json())
      .then((d: Row[]) => setData(d))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [skill, weeks, city]);

  const weekTicks = useMemo(() => data.map(d => d.week), [data]);

  return (
    <div className="p-8 space-y-6">
      <div className="flex flex-wrap gap-3 items-end">
        <div className="flex flex-col">
          <label className="text-sm opacity-70">Skill</label>
          <select
            value={skill}
            onChange={(e) => setSkill(e.target.value)}
            className="bg-transparent border rounded px-3 py-2"
          >
            {SKILLS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="flex flex-col">
          <label className="text-sm opacity-70">Window (weeks)</label>
          <select
            value={weeks}
            onChange={(e) => setWeeks(Number(e.target.value))}
            className="bg-transparent border rounded px-3 py-2"
          >
            {[4, 8, 12, 24, 36, 52].map(w => <option key={w} value={w}>{w}</option>)}
          </select>
        </div>

        <div className="flex flex-col">
          <label className="text-sm opacity-70">City (US/UK)</label>
          <select
            value={city ?? ""}
            onChange={(e) => setCity(e.target.value || null)}
            className="bg-transparent border rounded px-3 py-2 min-w-[200px]"
          >
            <option value="">All cities</option>
            <optgroup label="United States">
              {ALL_CITIES.filter(c => c.country === "US").map(c =>
                <option key={`US-${c.name}`} value={c.name}>{c.name}</option>
              )}
            </optgroup>
            <optgroup label="United Kingdom">
              {ALL_CITIES.filter(c => c.country === "UK").map(c =>
                <option key={`UK-${c.name}`} value={c.name}>{c.name}</option>
              )}
            </optgroup>
          </select>
        </div>
      </div>

      <h1 className="text-2xl font-bold">
        Trend: {skill} ({weeks} weeks{city ? `, ${city}` : ""})
      </h1>

      <div className="w-full h-[420px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week" ticks={weekTicks} />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Line type="monotone" dataKey="cnt" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {loading && <div className="opacity-70">Loading…</div>}
      {!loading && data.length === 0 && (
        <div className="opacity-70">No data for this selection.</div>
      )}
    </div>
  );
}
