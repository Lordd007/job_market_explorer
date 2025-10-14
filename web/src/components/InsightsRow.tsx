"use client";
import React, { useState } from "react";
import CitySelect from "@/components/CitySelect";
import RisingSkillsCard from "@/components/RisingSkillsCard";
import SalaryCard from "@/components/SalaryCard";

export default function InsightsRow() {
  const [city, setCity] = useState<string | undefined>(undefined);
  const [skill, setSkill] = useState<string>("go");

  return (
    <section className="mb-4">
      <div className="flex items-center justify-end gap-4 mb-2">
        <CitySelect value={city} onChange={setCity} />
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Skill:</span>
          <input
            value={skill}
            onChange={(e)=>setSkill(e.target.value)}
            className="rounded-md border border-teal-200 bg-white px-2 py-1"
            placeholder="python"
          />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <RisingSkillsCard city={city} />
        <SalaryCard skill={skill} city={city} />
      </div>
    </section>
  );
}
