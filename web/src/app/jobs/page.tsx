import { Suspense } from "react";
import JobsClient from "./JobsClient";
import InsightsRow from "@/components/InsightsRow";

// export const dynamic = "force-dynamic";  // (optional) if needed
// export const fetchCache = "force-no-store";

export default function Page() {
  return (
    <>
      <InsightsRow />
      <Suspense fallback={<div className="p-8">Loading jobs…</div>}>
        <JobsClient />
      </Suspense>
    </>
  );
}

