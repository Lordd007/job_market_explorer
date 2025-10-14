"use client";
import React, { useEffect, useState } from "react";
import { fetchJSON } from "@/lib/api";

type Prefs = {
  cities: string[];
  remote_mode: "any" | "remote" | "hybrid" | "office";
  target_skills: string[];
  companies: string[];
  seniority: "any" | "entry" | "mid" | "senior" | "lead" | "manager";
};

const DEFAULTS: Prefs = {
  cities: [],
  remote_mode: "any",
  target_skills: [],
  companies: [],
  seniority: "any",
};

export default function PreferencesPage() {
  const [prefs, setPrefs] = useState<Prefs>(DEFAULTS);
  const [cities, setCities] = useState<{city:string;n:number}[]>([]);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  // load existing from localStorage
  useEffect(() => {
    const raw = localStorage.getItem("prefs");
    if (raw) {
      try { setPrefs({ ...DEFAULTS, ...JSON.parse(raw) }); } catch {}
    }
    fetchJSON<{city:string;n:number}[]>("/api/cities", { min_support: 30 })
      .then(setCities)
      .catch(() => setCities([]));
  }, []);

  function update<K extends keyof Prefs>(key: K, value: Prefs[K]) {
    setPrefs(p => ({ ...p, [key]: value }));
  }

  async function save() {
    setSaving(true); setMsg(null);
    localStorage.setItem("prefs", JSON.stringify(prefs));
    try {
      // optional server save (will 404 if endpoint not implemented)
      const res = await fetch("/api/user/preferences", {
        method: "POST",
        headers: { "Content-Type":"application/json" },
        body: JSON.stringify(prefs),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setMsg("Saved to server and local");
    } catch {
      setMsg("Saved locally (server endpoint not available)");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="space-y-6">
      <h1 className="text-2xl font-bold">Preferences</h1>

      {/* Cities */}
      <section className="rounded-xl border border-teal-200 bg-white p-4">
        <h2 className="font-semibold mb-2">Cities</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {cities.map(c => {
            const sel = prefs.cities.includes(c.city);
            return (
              <label key={c.city} className={`px-2 py-1 rounded border cursor-pointer ${sel ? "bg-teal-50 border-teal-300" : "bg-white border-gray-300"}`}>
                <input
                  type="checkbox"
                  checked={sel}
                  onChange={(e) => {
                    const next = e.target.checked
                      ? [...prefs.cities, c.city]
                      : prefs.cities.filter(x => x !== c.city);
                    update("cities", next);
                  }}
                  className="mr-2"
                />
                {c.city} <span className="text-xs text-gray-500">({c.n})</span>
              </label>
            );
          })}
        </div>
      </section>

      {/* Remote mode */}
      <section className="rounded-xl border border-teal-200 bg-white p-4">
        <h2 className="font-semibold mb-2">Remote/Onsite</h2>
        {["any","remote","hybrid","office"].map(m => (
          <label key={m} className="mr-4">
            <input
              type="radio"
              name="remote"
              checked={prefs.remote_mode === m}
              onChange={() => update("remote_mode", m as Prefs["remote_mode"])}
              className="mr-1"
            />
            {m}
          </label>
        ))}
      </section>

      {/* Target skills */}
      <section className="rounded-xl border border-teal-200 bg-white p-4">
        <h2 className="font-semibold mb-2">Target skills</h2>
        <input
          className="w-full rounded border border-gray-300 px-3 py-2"
          placeholder="comma-separated, e.g. python, sql, tableau"
          value={prefs.target_skills.join(", ")}
          onChange={(e) => update("target_skills", e.target.value.split(",").map(s => s.trim()).filter(Boolean))}
        />
      </section>

      {/* Companies */}
      <section className="rounded-xl border border-teal-200 bg-white p-4">
        <h2 className="font-semibold mb-2">Preferred companies</h2>
        <input
          className="w-full rounded border border-gray-300 px-3 py-2"
          placeholder="comma-separated"
          value={prefs.companies.join(", ")}
          onChange={(e) => update("companies", e.target.value.split(",").map(s => s.trim()).filter(Boolean))}
        />
      </section>

      {/* Seniority */}
      <section className="rounded-xl border border-teal-200 bg-white p-4">
        <h2 className="font-semibold mb-2">Seniority</h2>
        {["any","entry","mid","senior","lead","manager"].map(m => (
          <label key={m} className="mr-4">
            <input
              type="radio"
              name="seniority"
              checked={prefs.seniority === m}
              onChange={() => update("seniority", m as Prefs["seniority"])}
              className="mr-1"
            />
            {m}
          </label>
        ))}
      </section>

      <button
        onClick={save}
        disabled={saving}
        className="px-4 py-2 rounded bg-teal-600 text-white disabled:opacity-60"
      >
        {saving ? "Saving..." : "Save preferences"}
      </button>
      {msg && <div className="text-sm text-gray-600">{msg}</div>}
    </main>
  );
}
