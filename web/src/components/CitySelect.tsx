"use client";

import { useEffect, useState } from "react";
import { fetchJSON } from "@/lib/api";

type CityRow = { city: string; count?: number; n?: number };

type Props = {
  value?: string;
  onChange: (val?: string) => void;
  placeholder?: string;      // <-- add this
  className?: string;
};

export default function CitySelect({
  value,
  onChange,
  placeholder = "All",
  className = "",
}: Props) {
  const [items, setItems] = useState<CityRow[]>([]);

  useEffect(() => {
    // tolerant to either `count` or `n`
    fetchJSON<CityRow[]>("/api/cities", { min_count: 5, limit: 500 })
      .then(setItems)
      .catch(() => setItems([]));
  }, []);

  return (
    <select
      value={value ?? ""}                               // keep "" for "All"
      onChange={(e) => onChange(e.target.value || undefined)}
      className={`rounded border border-teal-200 px-3 py-2 bg-white text-slate-900 ${className}`}
    >
      <option value="">{placeholder}</option>
      {items.map((r) => {
        const cnt = r.count ?? r.n ?? 0;
        return (
          <option key={r.city} value={r.city}>
            {r.city}{cnt ? ` (${cnt})` : ""}
          </option>
        );
      })}
    </select>
  );
}
