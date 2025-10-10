"use client";
import { useEffect, useState } from "react";

type Job = { job_id:string; title:string; company:string; city?:string|null; posted_at?:string|null; created_at:string; url?:string|null; sim?:number };
export default function RecsPage() {
  const [items, setItems] = useState<Job[]>([]);
  const [err, setErr] = useState<string>(""); const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true); setErr("");
    fetch("/api/recommendations", { method: "POST" })
      .then(r=> r.ok ? r.json() : Promise.reject(r.statusText))
      .then(json => setItems(json.items || []))
      .catch(e => setErr(String(e)))
      .finally(()=>setLoading(false));
  }, []);

  return (
    <main className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Recommended Jobs</h1>
      {loading && <div>Loading…</div>}
      {err && <div className="text-red-400">Error: {err}</div>}
      {!loading && !err && items.length===0 && <div>No strong matches yet. Try broadening preferences or update your resume.</div>}
      <ul className="divide-y divide-neutral-800 rounded border">
        {items.map(j => (
          <li key={j.job_id} className="p-4">
            <div className="font-semibold">{j.title}</div>
            <div className="opacity-80">{j.company}</div>
            <div className="opacity-60 text-sm">{j.city || "N/A"} {j.sim ? `· score ${(j.sim*100).toFixed(0)}` : ""}</div>
            {j.url && <a className="border rounded px-3 py-2 mt-2 inline-block" href={j.url} target="_blank">View</a>}
          </li>
        ))}
      </ul>
    </main>
  );
}
