"use client";

import { useEffect, useState } from "react";
import { fetchJSON } from "@/lib/api";

type ModeRow = { mode: "Remote" | "Hybrid" | "On-site"; count: number };

export default function ModeSelect({
  value,
  onChange,
  placeholder = "All",
  className = "",
}: {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  className?: string;
}) {
  const [items, setItems] = useState<ModeRow[]>([]);

  useEffect(() => {
    fetchJSON<ModeRow[]>("/api/modes", { min_count: 0 })
      .then(setItems)
      .catch(() => { /* noop */ });
  }, []);

  return (
    <select
      value={value || ""}
      onChange={(e) => onChange(e.target.value)}
      className={`rounded border border-teal-200 px-3 py-2 bg-white text-slate-900 ${className}`}
    >
      <option value="">{placeholder}</option>
      {items.map((r) => (
        <option key={r.mode} value={r.mode}>
          {r.mode} ({r.count})
        </option>
      ))}
    </select>
  );
}
