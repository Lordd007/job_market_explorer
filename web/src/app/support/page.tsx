"use client";
import React, { useMemo, useState } from "react";

const VENMO_HANDLE = "jme-support";

export default function SupportPage() {
  const [amount, setAmount] = useState<string>("10.00");
  const note = "Support JME";
  const webUrl = `https://venmo.com/${VENMO_HANDLE}`;
  // Venmo app deep link; some browsers will open the app if installed
  const appUrl = useMemo(() => {
    const params = new URLSearchParams({
      txn: "pay",
      recipients: VENMO_HANDLE,
      amount: amount || "",
      note,
    });
    return `venmo://paycharge?${params.toString()}`;
  }, [amount]);

  return (
    <main className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Support JME</h1>
      <p className="text-gray-700">
        If JME has been helpful, you can support ongoing hosting and development via Venmo.
      </p>

      <div className="rounded-xl border border-teal-200 bg-white p-4 space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-gray-600">Amount (USD):</span>
          <input
            value={amount}
            onChange={(e)=>setAmount(e.target.value)}
            className="w-24 rounded border border-gray-300 px-2 py-1"
            placeholder="10.00"
          />
          <div className="flex gap-1 ml-2">
            {["5","10","20","50"].map(v => (
              <button key={v} onClick={()=>setAmount(`${v}.00`)}
                className="px-2 py-1 rounded border border-teal-300 text-teal-700 hover:bg-teal-50">
                ${v}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <a href={appUrl} className="px-3 py-2 rounded border border-teal-300 text-teal-700 hover:bg-teal-50">
            Open Venmo App
          </a>
          <a href={webUrl} target="_blank" rel="noreferrer"
             className="px-3 py-2 rounded border border-teal-300 text-teal-700 hover:bg-teal-50">
            Open Venmo Web
          </a>
        </div>

        <div className="text-sm text-gray-500">
          Handle: <b>@{VENMO_HANDLE}</b> &nbsp;|&nbsp; Note: “{note}”
        </div>
      </div>
    </main>
  );
}
