"use client";
import { useMemo } from "react";

type Props = {
  value: string;                    // city name or "" (All)
  onChange: (val: string) => void;
  className?: string;
  includeAll?: boolean;
};

const US = [
  "New York", "San Francisco", "Austin", "Seattle", "Boston",
  "Chicago", "Atlanta", "Los Angeles", "Denver", "Dallas", "Miami"
];

const UK = [
  "London", "Manchester", "Birmingham", "Edinburgh",
  "Glasgow", "Leeds", "Bristol", "Cambridge", "Oxford"
];

export default function CitySelect({ value, onChange, className, includeAll = true }: Props) {
  const groups = useMemo(() => [
    { label: "United States", options: US },
    { label: "United Kingdom", options: UK },
  ], []);

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={className ?? "border rounded px-3 py-2"}
    >
      {includeAll && <option value="">All cities</option>}
      {groups.map((g) => (
        <optgroup key={g.label} label={g.label}>
          {g.options.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </optgroup>
      ))}
    </select>
  );
}
