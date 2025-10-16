"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { fetchJSON } from "@/lib/api";
import CitySelect from "@/components/CitySelect";

/* ---------- helpers for consistent location/mode rendering ---------- */

function deriveMode(city: string | null | undefined, remoteFlag?: boolean): "" | "Remote" | "Hybrid" | "In-Office" {
  if (remoteFlag) return "Remote";
  const s = (city || "").toLowerCase();
  if (/\bhybrid\b/.test(s)) return "Hybrid";
  if (/\b(in[- ]?office|office|onsite|on[- ]?site)\b/.test(s)) return "In-Office";
  return "";
}

function cleanCity(
  city: string | null | undefined,
  region?: string | null,
  country?: string | null,
  remoteFlag?: boolean
): string {
  if (!city || !city.trim()) {
    if (remoteFlag) return country ? `Remote - ${country}` : "Remote";
    const parts = [region, country].filter(Boolean);
    return parts.length ? parts.join(", ") : "N/A";
  }
  const c = city
    .replace(/^\s*home\s*based\s*-\s*/i, "")
    .replace(/\s*\boffice\b.*$/i, "")
    .replace(/\s*remote\s*-\s*.*$/i, "")
    .replace(/\s*\bhybrid\b.*$/i, "")
    .trim();

  if (!c && remoteFlag) return country ? `Remote - ${country}` : "Remote";
  if (!c) {
    const parts = [region, country].filter(Boolean);
    return parts.length ? parts.join(", ") : "N/A";
  }
  return c;
}

/* -------------------------- types -------------------------- */

type Job = {
  job_id: string;
  title: string;
  company: string;
  city: string | null;
  region: string | null;
  country: string | null;
  posted_at: string | null;
  created_at: string;
  url: string | null;
  remote_flag?: boolean;
};

type JobsResp = { total: number; page: number; page_size: number; items: Job[] };
type SortMode = "newest" | "title" | "company";

/* ------------------------ component ------------------------ */

export default function JobsClient() {
  const router = useRouter();
  const params = useSearchParams();

  // filters / state
  const [qInput, setQInput] = useState("");
  const [q, setQ] = useState("");
  const [skill, setSkill] = useState("");
  const [suggest, setSuggest] = useState<string[]>([]);
  const [city, setCity] = useState<string | undefined>(undefined); // <- undefined = "All"
  const [days, setDays] = useState(90);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<SortMode>("newest");

  const [resp, setResp] = useState<JobsResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // hydrate filters from URL on first mount
  useEffect(() => {
    const q0    = params.get("q") || "";
    const city0 = params.get("city") || undefined;   // <- undefined when not present
    const skill0= params.get("skill") || "";
    const days0 = Number(params.get("days") || 90);
    const page0 = Number(params.get("page") || 1);
    const sort0 = (params.get("sort") as SortMode) || "newest";

    setQInput(q0); setQ(q0);
    setCity(city0); setSkill(skill0);
    setDays(days0); setPage(page0);
    setSort(sort0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // persist filters to URL (shallow)
  useEffect(() => {
    const sp = new URLSearchParams();
    if (q) sp.set("q", q);
    if (city) sp.set("city", city);  // omitted when undefined
    if (skill) sp.set("skill", skill);
    if (days) sp.set("days", String(days));
    if (page) sp.set("page", String(page));
    if (sort && sort !== "newest") sp.set("sort", sort);
    router.replace(`/jobs?${sp.toString()}`, { scroll: false });
  }, [q, city, skill, days, page, sort, router]);

  // debounce search input → q
  useEffect(() => {
    const t = setTimeout(() => { setQ(qInput); setPage(1); }, 250);
    return () => clearTimeout(t);
  }, [qInput]);

  // fetch jobs
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

  // derived: client-side sort & pagination label
  const totalPages = useMemo(
    () => (resp ? Math.max(1, Math.ceil(resp.total / (resp.page_size || 20))) : 1),
    [resp]
  );

  const items = useMemo(() => {
    if (!resp) return [];
    let out = [...resp.items];

    // optional: when a city is selected, hide pure-remote rows
    if (city) {
      out = out.filter(j => !j.remote_flag);
    }

    if (sort === "title") out.sort((a, b) => a.title.localeCompare(b.title));
    else if (sort === "company") out.sort((a, b) => a.company.localeCompare(b.company));
    return out;  // newest = API order
  }, [resp, sort, city]);

  // UI
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

        {/* City (dynamic) */}
        <div className="flex flex-col">
          <label className="text-sm opacity-70">City</label>
          <CitySelect
            value={city}
            onChange={(v) => { setPage(1); setCity(v); }}  // v is string | undefined
          />
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
            onChange={e => setSort(e.target.value as SortMode)}
            className="bg-transparent border rounded px-3 py-2"
          >
            <option value="newest">Newest</option>
            <option value="title">Title (A→Z)</option>
            <option value="company">Company (A→Z)</option>
          </select>
        </div>
      </div>

      {error && <div className="text-red-400">Error: {error}</div>}

      {loading && (
        <ul className="divide-y divide-neutral-800 rounded border animate-pulse">
          {Array.from({ length: 6 }).map((_, i) => (
            <li key={i} className="p-4">
              <div className="h-4 w-48 bg-neutral-800 rounded mb-2" />
              <div className="h-3 w-32 bg-neutral-900 rounded" />
            </li>
          ))}
        </ul>
      )}

      {!loading && resp && resp.total === 0 && (
        <div className="opacity-70">No jobs found. Try clearing filters or increasing the day window.</div>
      )}

      {!loading && resp && resp.total > 0 && (
        <>
          <div className="text-sm opacity-70">
            Showing {(resp.page - 1) * resp.page_size + 1}–{Math.min(resp.page * resp.page_size, resp.total)} of {resp.total}
          </div>

          <ul className="divide-y divide-neutral-800 rounded border">
            {items.map((j) => {
              const mode = deriveMode(j.city, j.remote_flag);
              const place = cleanCity(j.city, j.region, j.country, j.remote_flag);
              const when = new Date(j.posted_at || j.created_at).toLocaleDateString();

              return (
                <li key={j.job_id} className="p-4 hover:bg-white/70 transition-colors border-b border-teal-100">
                  <div className="flex justify-between gap-4 flex-wrap">
                    <div>
                      <div className="font-semibold">{j.title}</div>
                      <div className="opacity-80">{j.company}</div>
                      <div className="opacity-80">{place}</div>
                      <div className="opacity-60 text-sm">
                        {mode ? `${mode} · ` : ""}{when}
                      </div>
                    </div>
                    {j.url && (
                      <a className="border rounded px-3 py-2" href={j.url} target="_blank" rel="noreferrer">
                        View Posting
                      </a>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>

          <div className="flex gap-2 items-center pt-4">
            <button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))} className="border rounded px-3 py-2 disabled:opacity-50">
              Prev
            </button>
            <div className="text-sm opacity-80">Page {page} / {totalPages}</div>
            <button disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))} className="border rounded px-3 py-2 disabled:opacity-50">
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
