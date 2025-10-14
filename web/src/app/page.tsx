// web/src/app/page.tsx
import { redirect } from "next/navigation";

export default function Home() {
  //redirect("/dashboard"); // 308 internal redirect at render
  redirect("/jobs"); //short term solution while dashboard is reworked.
}
