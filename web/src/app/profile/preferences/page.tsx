"use client";
import { useEffect, useState } from "react";

export default function PrefsPage() {
  const [prefs, setPrefs] = useState<any>(null);
  const [msg, setMsg] = useState("");

  useEffect(() => { fetch("/api/user/preferences").then(r=>r.json()).then(setPrefs); }, []);

  const save = async () => {
    setMsg("Saving…");
    const res = await fetch("/api/user/preferences", { method: "PUT", headers:{ "Content-Type":"application/json" }, body: JSON.stringify(prefs) });
    setMsg(res.ok ? "Saved" : "Error");
  };

  if (!prefs) return <main className="p-6">Loading…</main>;
  return (
    <main className="p-6 space-y-3">
      <h1 className="text-2xl font-bold">Preferences</h1>
      <label className="block">Cities (comma-separated)
        <input className="border rounded px-2 py-1 w-full"
          value={(prefs.cities||[]).join(", ")}
          onChange={e=>setPrefs({...prefs, cities: e.target.value.split(",").map(s=>s.trim()).filter(Boolean)})}/>
      </label>
      <label className="block">Remote mode
        <select className="border rounded px-2 py-1"
          value={prefs.remote_mode}
          onChange={e=>setPrefs({...prefs, remote_mode: e.target.value})}>
          <option value="any">Any</option><option value="remote">Remote</option><option value="hybrid">Hybrid</option><option value="office">In-Office</option>
        </select>
      </label>
      <label className="block">Target skills (comma-separated)
        <input className="border rounded px-2 py-1 w-full"
          value={(prefs.target_skills||[]).join(", ")}
          onChange={e=>setPrefs({...prefs, target_skills: e.target.value.split(",").map(s=>s.trim()).filter(Boolean)})}/>
      </label>
      <label className="block">Companies (comma-separated)
        <input className="border rounded px-2 py-1 w-full"
          value={(prefs.companies||[]).join(", ")}
          onChange={e=>setPrefs({...prefs, companies: e.target.value.split(",").map(s=>s.trim()).filter(Boolean)})}/>
      </label>
      <label className="block">Seniority
        <select className="border rounded px-2 py-1"
          value={prefs.seniority}
          onChange={e=>setPrefs({...prefs, seniority: e.target.value})}>
          <option value="any">Any</option><option value="entry">Entry</option><option value="mid">Mid</option><option value="senior">Senior</option>
        </select>
      </label>
      <button className="border rounded px-3 py-2" onClick={save}>Save</button>
      <div className="opacity-70">{msg}</div>
    </main>
  );
}
