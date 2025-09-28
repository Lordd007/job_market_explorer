"use client";

import { useEffect, useState } from "react";

type Skill = {
  skill: string;
  cnt: number;
};

export default function DashboardPage() {
  const [skills, setSkills] = useState<Skill[]>([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/skills/top?limit=10&days=90")
      .then((res) => res.json())
      .then((data) => setSkills(data));
  }, []);

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold mb-4">Top Skills (last 90 days)</h1>
      <table className="min-w-full border border-gray-300">
        <thead className="bg-gray-100">
          <tr>
            <th className="px-4 py-2 text-left border">Skill</th>
            <th className="px-4 py-2 text-left border">Count</th>
          </tr>
        </thead>
        <tbody>
          {skills.map((s) => (
            <tr key={s.skill}>
              <td className="px-4 py-2 border">{s.skill}</td>
              <td className="px-4 py-2 border">{s.cnt}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
