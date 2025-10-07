import { Suspense } from "react";
import JobsClient from "./JobsClient";

// If this page should never be statically prerendered, uncomment one of these:
// export const dynamic = "force-dynamic";
// export const fetchCache = "force-no-store";

export default function Page() {
  return (
    <Suspense fallback={<div className="p-8">Loading jobs…</div>}>
      <JobsClient />
    </Suspense>
  );
}
