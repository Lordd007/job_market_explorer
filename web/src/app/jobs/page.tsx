"use client";
import { useEffect, useMemo, useState } from "react";
import { fetchJSON } from "@/lib/api";
import { ALL_CITIES } from "@/data/cities";

type Job = {
  job_id: string; title: string; company: string;
  city: string | null; region: string | null; country: string | null;
  posted_at: string | null; created_at: string; url: string | null;
};
type JobsResp = { total: number; page: number; page_size: number; items: Job[] };

export default function Jobs() {
  const [q, setQ] = useState("");
  const [skill, setSkill] = useState("");
  const [suggest, setSuggest] = useState<string[]>([]);
  const [city, setCity] = useState("");
  const [days, setDays] = useState(90);
  const [page, setPage] = useState(1);
  const [resp, setResp] = useState<JobsResp | null>(null);
  const [loading, setLoading] = useState(false);

  // fetch jobs
  useEffect(() => {
    console.log("🚀 Attempting to fetch from /api/skills/trends");
    console.log("Constructed URL:", url);  // 👈 this will reveal the problem

    if (!url || typeof url.toString !== "function") {
        console.error("Invalid URL:", url);
        return;
    }

    setLoading(true);
    fetchJSON<JobsResp>("/api/jobs", { q, city, skill, days, page, page_size: 20 })
      .then(setResp)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [q, city, skill, days, page]);

  // skill typeahead
  useEffect(() => {
    if (!skill || skill.length < 2) { setSuggest([]); return; }
    const t = setTimeout(() => {
      fetchJSON<string[]>("/api/skills/suggest", { term: skill })
        .then(setSuggest)
        .catch(() => setSuggest([]));
    }, 200);
    return () => clearTimeout(t);
  }, [skill]);

  const totalPages = useMemo(() =>
    resp ? Math.max(1, Math.ceil(resp.total / (resp.page_size || 20))) : 1,
  [resp]);

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">Browse Jobs</h1>

      <div className="flex flex-wrap gap-3 items-end">
        <div className="flex flex-col">
          <label className="text-sm opacity-70">Search</label>
          <input
            value={q} onChange={e => { setPage(1); setQ(e.target.value); }}
            placeholder="title, company, description…"
            className="bg-transparent border rounded px-3 py-2 min-w-[260px]"
          />
        </div>

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

        <div className="flex flex-col">
          <label className="text-sm opacity-70">Posted within</label>
          <select
            value={days}
            onChange={e => { setPage(1); setDays(Number(e.target.value)); }}
            className="bg-transparent border rounded px-3 py-2"
          >
            {[7, 14, 30, 60, 90, 180, 365].map(d => <option key={d} value={d}>{d} days</option>)}
          </select>
        </div>
      </div>

      {loading && <div className="opacity-70">Loading…</div>}

      {!loading && resp && (
        <>
          <div className="text-sm opacity-70">
            Showing {(resp.page-1)*resp.page_size + 1}–
            {Math.min(resp.page*resp.page_size, resp.total)} of {resp.total}
          </div>

          <ul className="divide-y divide-neutral-800 rounded border">
            {resp.items.map((j) => (
              <li key={j.job_id} className="p-4 hover:bg-neutral-900">
                <div className="flex justify-between gap-4 flex-wrap">
                  <div>
                    <div className="font-semibold">{j.title}</div>
                    <div className="opacity-80">{j.company}</div>
                    <div className="opacity-60 text-sm">
                      {j.city || "N/A"} · {new Date(j.posted_at || j.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  {j.url && (
                    <a className="border rounded px-3 py-2" href={j.url} target="_blank" rel="noreferrer">
                      View Posting
                    </a>
                  )}
                </div>
              </li>
            ))}
          </ul>

          <div className="flex gap-2 items-center pt-4">
            <button
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(1, p-1))}
              className="border rounded px-3 py-2 disabled:opacity-50"
            >
              Prev
            </button>
            <div className="text-sm opacity-80">
              Page {page} / {totalPages}
            </div>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(p => Math.min(totalPages, p+1))}
              className="border rounded px-3 py-2 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
