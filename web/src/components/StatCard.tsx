"use client";
import React from "react";

type Props = {
  title: string;
  value?: React.ReactNode;
  subtitle?: string;
  right?: React.ReactNode;
};

export default function StatCard({ title, value, subtitle, right }: Props) {
  return (
    <div className="rounded-2xl border border-teal-200/60 bg-white shadow-sm p-4 flex items-start justify-between">
      <div>
        <div className="text-xs uppercase tracking-wide text-teal-700/80">{title}</div>
        <div className="text-2xl font-semibold mt-1">{value ?? "—"}</div>
        {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
      </div>
      {right && <div className="ml-4">{right}</div>}
    </div>
  );
}
