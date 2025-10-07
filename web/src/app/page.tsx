// src/app/page.tsx
"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";

import { API_BASE } from "@/lib/config";

type SkillRow = { skill: string; cnt: number };
type SortMode = "count-desc" | "count-asc" | "alpha-asc" | "alpha-desc";
type EndpointKey = "skills-top"; // extend later: "skills-trends" | "jobs-search" | ...



export default function Page() {
  // “Endpoint” + params (more endpoints can have their own param sets)
  const [endpoint, setEndpoint] = useState<EndpointKey>("skills-top");
  const [days, setDays] = useState<number>(90);
  const [limit, setLimit] = useState<number>(10);
  const [city, setCity] = useState<string>("");

  const [raw, setRaw] = useState<SkillRow[]>([]);
  const [sortMode, setSortMode] = useState<SortMode>("count-desc");
  const [loading, setLoading] = useState<boolean>(false);
  const [err, setErr] = useState<string | null>(null);

  // Build the URL for the selected endpoint
  const url = useMemo(() => {
    const u = new URL(API_BASE);
    if (endpoint === "skills-top") {
      u.pathname = "/api/skills/top";
      if (limit) u.searchParams.set("limit", String(limit));
      if (days) u.searchParams.set("days", String(days));
      if (city.trim()) u.searchParams.set("city", city.trim());
    }
    return u.toString();
  }, [endpoint, limit, days, city]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setErr(null);
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
      })
      .then((d: SkillRow[]) => {
        if (!cancelled) setRaw(d);
      })
      .catch((e) => !cancelled && setErr(String(e)))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [url]);

  const data = useMemo(() => {
    const arr = [...raw];
    switch (sortMode) {
      case "count-asc":  arr.sort((a, b) => a.cnt - b.cnt); break;
      case "alpha-asc":  arr.sort((a, b) => a.skill.localeCompare(b.skill)); break;
      case "alpha-desc": arr.sort((a, b) => b.skill.localeCompare(a.skill)); break;
      default:           arr.sort((a, b) => b.cnt - a.cnt);
    }
    return arr;
  }, [raw, sortMode]);

  return (
    <div className="p-8 space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            {endpoint === "skills-top" ? "Top Skills" : "Dashboard"}{" "}
            <span className="opacity-70 text-base">
              {endpoint === "skills-top" ? `(${days} days)` : ""}
            </span>
          </h1>
          <p className="text-sm opacity-70">Live from {API_BASE}</p>
        </div>

        <div className="flex flex-wrap gap-3">
          {/* Endpoint selector (more items later) */}
          <select
            value={endpoint}
            onChange={(e) => setEndpoint(e.target.value as EndpointKey)}
            className="px-3 py-2 rounded border border-neutral-600 bg-transparent"
            title="Select API endpoint"
          >
            <option value="skills-top">Skills: Top</option>
            {/* <option value="skills-trends" disabled>Skills: Trends (soon)</option> */}
          </select>

          {/* Params (visible for skills-top) */}
          {endpoint === "skills-top" && (
            <>
              <label className="flex items-center gap-2 text-sm">
                Days
                <input
                  type="number"
                  min={7}
                  max={365}
                  value={days}
                  onChange={(e) => setDays(Number(e.target.value))}
                  className="w-20 px-2 py-1 rounded border border-neutral-600 bg-transparent"
                />
              </label>

              <label className="flex items-center gap-2 text-sm">
                Limit
                <input
                  type="number"
                  min={5}
                  max={50}
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  className="w-20 px-2 py-1 rounded border border-neutral-600 bg-transparent"
                />
              </label>

              <input
                placeholder="City (optional)"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="px-3 py-2 rounded border border-neutral-600 bg-transparent"
              />

              <select
                value={sortMode}
                onChange={(e) => setSortMode(e.target.value as SortMode)}
                className="px-3 py-2 rounded border border-neutral-600 bg-transparent"
                title="Sort by"
              >
                <option value="count-desc">Sort: Count ↓</option>
                <option value="count-asc">Sort: Count ↑</option>
                <option value="alpha-asc">Sort: A–Z</option>
                <option value="alpha-desc">Sort: Z–A</option>
              </select>
            </>
          )}
        </div>
      </header>

      {loading && <div className="opacity-70 text-sm">Loading…</div>}
      {err && <div className="text-red-500 text-sm">Error: {err}</div>}

      {!loading && !err && (
        <ResponsiveContainer width="100%" height={440}>
          <BarChart data={data} layout="vertical">
            <XAxis type="number" />
            <YAxis dataKey="skill" type="category" width={140} />
            <Tooltip />
            <Bar dataKey="cnt" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
