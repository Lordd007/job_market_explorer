"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { fetchJSON } from "@/lib/api";         // <- remove apiUrl (unused)
import { ALL_CITIES } from "@/data/cities";

type Job = {
  job_id: string; title: string; company: string;
  city: string | null; region: string | null; country: string | null;
  posted_at: string | null; created_at: string; url: string | null;
};
type JobsResp = { total: number; page: number; page_size: number; items: Job[] };
type SortMode = "newest" | "title" | "company";

export default function JobsClient() {
  const router = useRouter();
  const params = useSearchParams();

  // ── filters / state ───────────────────────────────────────────────────────────
  const [qInput, setQInput] = useState("");
  const [q, setQ] = useState("");
  const [skill, setSkill] = useState("");
  const [suggest, setSuggest] = useState<string[]>([]);
  const [city, setCity] = useState("");
  const [days, setDays] = useState(90);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<SortMode>("newest");

  const [resp, setResp] = useState<JobsResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── hydrate filters from URL on first mount ───────────────────────────────────
  useEffect(() => {
    const q0 = params.get("q") ?? "";
    const city0 = params.get("city") ?? "";
    const skill0 = params.get("skill") ?? "";
    const days0 = Number(params.get("days") ?? 90);
    const page0 = Number(params.get("page") ?? 1);
    const sort0 = (params.get("sort") as SortMode) ?? "newest";

    setQInput(q0); setQ(q0);
    setCity(city0); setSkill(skill0);
    setDays(days0); setPage(page0);
    setSort(sort0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── persist filters to URL (shallow) ─────────────────────────────────────────
  useEffect(() => {
    const sp = new URLSearchParams();
    if (q) sp.set("q", q);
    if (city) sp.set("city", city);
    if (skill) sp.set("skill", skill);
    if (days) sp.set("days", String(days));
    if (page) sp.set("page", String(page));
    if (sort && sort !== "newest") sp.set("sort", sort);
    router.replace(`/jobs?${sp.toString()}`, { scroll: false });
  }, [q, city, skill, days, page, sort, router]);

  // ── debounce search input → q ────────────────────────────────────────────────
  useEffect(() => {
    const t = setTimeout(() => { setQ(qInput); setPage(1); }, 250);
    return () => clearTimeout(t);
  }, [qInput]);

  // ── fetch jobs ───────────────────────────────────────────────────────────────
  useEffect(() => {
    const ac = new AbortController();
    setLoading(true);
    setError(null);

    fetchJSON<JobsResp>("/api/jobs", { q, city, skill, days, page, page_size: 20 })
      .then((data) => { if (!ac.signal.aborted) setResp(data); })
      .catch((e) => { if (!ac.signal.aborted) setError(String(e)); })
      .finally(() => { if (!ac.signal.aborted) setLoading(false); });

    return () => ac.abort();
  }, [q, city, skill, days, page]);

  // ── skill typeahead ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!skill || skill.length < 2) { setSuggest([]); return; }
    const t = setTimeout(() => {
      fetchJSON<string[]>("/api/skills/suggest", { term: skill })
        .then(setSuggest)
        .catch(() => setSuggest([]));
    }, 200);
    return () => clearTimeout(t);
  }, [skill]);

  // ── derived: client-side sort & pagination label ─────────────────────────────
  const totalPages = useMemo(
    () => (resp ? Math.max(1, Math.ceil(resp.total / (resp.page_size || 20))) : 1),
    [resp]
  );

  const items = useMemo(() => {
    if (!resp) return [];
    const out = [...resp.items];
    if (sort === "title") out.sort((a,b)=>a.title.localeCompare(b.title));
    else if (sort === "company") out.sort((a,b)=>a.company.localeCompare(b.company));
    return out; // newest = API order
  }, [resp, sort]);

  // ── UI ───────────────────────────────────────────────────────────────────────
  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">Browse Jobs</h1>

      <div className="flex flex-wrap gap-3 items-end">
        {/* Search */}
        <div className="flex flex-col">
          <label className="text-sm opacity-70">Search</label>
          <input
            value={qInput} onChange={e => setQInput(e.target.value)}
            placeholder="title, company, description…"
            className="bg-transparent border rounded px-3 py-2 min-w-[260px]"
          />
        </div>

        {/* Skill + typeahead */}
        <div className="flex flex-col relative">
          <label className="text-sm opacity-70">Skill</label>
          <input
            value={skill}
            onChange={e => { setPage(1); setSkill(e.target.value); }}
            placeholder="e.g. python"
            className="bg-transparent border rounded px-3 py-2 min-w-[200px]"
            list="skill-suggest"
          />
          <datalist id="skill-suggest">
            {suggest.map(s => <option key={s} value={s} />)}
          </datalist>
        </div>

        {/* City */}
        <div className="flex flex-col">
          <label className="text-sm opacity-70">City (US/UK)</label>
          <select
            value={city}
            onChange={e => { setPage(1); setCity(e.target.value); }}
            className="bg-transparent border rounded px-3 py-2 min-w-[200px]"
          >
            <option value="">All</option>
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

        {/* Days */}
        <div className="flex flex-col">
          <label className="text-sm opacity-70">Posted within</label>
          <select
            value={days}
            onChange={e => { setPage(1); setDays(Number(e.target.value)); }}
            className="bg-transparent border rounded px-3 py-2"
          >
            {[7, 14, 30, 60, 90, 180, 365].map(d =>
              <option key={d} value={d}>{d} days</option>
            )}
          </select>
        </div>

        {/* Sort */}
        <div className="flex flex-col">
          <label className="text-sm opacity-70">Sort</label>
          <select
            value={sort}
            onChange={e => setSort(e.ta
