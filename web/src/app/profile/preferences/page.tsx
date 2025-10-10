"use client";
import { useEffect, useState } from "react";

type RemoteMode = "remote" | "hybrid" | "office" | "any";
type Seniority  = "entry" | "junior" | "mid" | "senior" | "any";

type Prefs = {
  cities: string[];
  remote_mode: RemoteMode;
  target_skills: string[];
  companies: string[];
  seniority: Seniority;
};

const EMPTY_PREFS: Prefs = {
  cities: [],
  remote_mode: "any",
  target_skills: [],
  companies: [],
  seniority: "any",
};

export default function PrefsPage() {
  const [prefs, setPrefs] = useState<Prefs | null>(null);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch("/api/user/preferences");
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        const data = (await r.json()) as Partial<Prefs>;
        // merge with defaults to be defensive
        setPrefs({ ...EMPTY_PREFS, ...data });
      } catch (e: unknown) {
        setMsg(`Error loading: ${String(e)}`);
        setPrefs(EMPTY_PREFS);
      }
    })();
  }, []);

  const save = async () => {
    if (!prefs) return;
    setMsg("Saving…");
    try {
      const res = await fetch("/api/user/preferences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prefs),
      });
      setMsg(res.ok ? "Saved" : `Error: ${res.status}`);
    } catch (e: unknown) {
      setMsg(`Error: ${String(e)}`);
    }
  };

  if (!prefs) return <main className="p-6">Loading…</main>;

  return (
    <main className="p-6 space-y-3">
      <h1 className="text-2xl font-bold">Preferences</h1>

      <label className="block">
        Cities (comma-separated)
        <input
          className="border rounded px-2 py-1 w-full"
          value={(prefs.cities || []).join(", ")}
          onChange={(e) =>
            setPrefs({
              ...prefs,
              cities: e.target.value
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
            })
          }
        />
      </label>

      <label className="block">
        Remote mode
        <select
          className="border rounded px-2 py-1"
          value={prefs.remote_mode}
          onChange={(e) =>
            setPrefs({ ...prefs, remote_mode: e.target.value as RemoteMode })
          }
        >
          <option value="any">Any</option>
          <option value="remote">Remote</option>
          <option value="hybrid">Hybrid</option>
          <option value="office">In-Office</option>
        </select>
      </label>

      <label className="block">
        Target skills (comma-separated)
        <input
          className="border rounded px-2 py-1 w-full"
          value={(prefs.target_skills || []).join(", ")}
          onChange={(e) =>
            setPrefs({
              ...prefs,
              target_skills: e.target.value
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
            })
          }
        />
      </label>

      <label className="block">
        Companies (comma-separated)
        <input
          className="border rounded px-2 py-1 w-full"
          value={(prefs.companies || []).join(", ")}
          onChange={(e) =>
            setPrefs({
              ...prefs,
              companies: e.target.value
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
            })
          }
        />
      </label>

      <label className="block">
        Seniority
        <select
          className="border rounded px-2 py-1"
          value={prefs.seniority}
          onChange={(e) =>
            setPrefs({ ...prefs, seniority: e.target.value as Seniority })
          }
        >
          <option value="entry">Entry</option>
          <option value="junior">Junior</option>
          <option value="mid">Mid</option>
          <option value="senior">Senior</option>
          <option value="any">Any</option>
        </select>
      </label>

      <button className="border rounded px-3 py-2" onClick={save}>
        Save
      </button>
      <div className="opacity-70">{msg}</div>
    </main>
  );
}
