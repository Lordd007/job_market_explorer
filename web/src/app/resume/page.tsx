"use client";
import { useState } from "react";

export default function ResumePage() {
  const [file, setFile] = useState<File | null>(null);
  const [msg, setMsg] = useState<string>("");

  const submit = async () => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    setMsg("Uploading…");
    const res = await fetch("/api/resumes", { method: "POST", body: fd });
    if (!res.ok) { setMsg(`Error: ${res.status}`); return; }
    const json = await res.json();
    setMsg(`Uploaded. Extracted ${json.skills?.length || 0} skills.`);
  };

  return (
    <main className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Upload Resume</h1>
      <input type="file" accept=".pdf,.docx,.txt" onChange={e => setFile(e.target.files?.[0] || null)} />
      <button className="border rounded px-3 py-2" onClick={submit} disabled={!file}>Upload</button>
      <div className="opacity-80">{msg}</div>
    </main>
  );
}
