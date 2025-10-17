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
  const [items, setItems] = useState<{ city: string; n: number }[]>([]);

  useEffect(() => {
    // tolerant to either `count` or `n`
    fetchJSON<CityRow[]>("/api/cities", { params: { min_count: 5, limit: 500 } })
      .then((rows) =>
        setItems(rows.map((r) => ({ city: r.city, n: r.n ?? r.count ?? 0 })))
      )
      .catch(() => setItems([]));
  }, []);

  return (
    <select
      value={value || ""}
      onChange={(e) => onChange(e.target.value || undefined)}
      className={`rounded border border-teal-200 px-3 py-2 bg-white text-slate-900 ${className}`}
    >
      <option value="">{placeholder}</option>
      {items.map((r) => (
        <option key={r.city} value={r.city}>
          {r.city} {r.n ? `(${r.n})` : ""}
        </option>
      ))}
    </select>
  );
}
