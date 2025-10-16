"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { isAuthed, clearToken } from "@/lib/auth";

const tabs = [
  { href: "/jobs", label: "Jobs" },
  { href: "/preferences", label: "Preferences" },
  { href: "/feedback", label: "Feedback" },
  { href: "/support", label: "Support Us" },
];

export default function NavBar() {
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = useState(false);

  // Detect auth status after mount and whenever localStorage changes
  useEffect(() => {
    setAuthed(isAuthed());
    const onStorage = (e: StorageEvent) => {
      if (e.key === "jme_token") setAuthed(isAuthed());
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  function logout() {
    clearToken();
    setAuthed(false);
    // optional redirect after logout
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-20 bg-teal-50/90 backdrop-blur border-b border-teal-200">
      <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
        <Link href="/jobs" className="flex items-center gap-2 font-semibold text-teal-800" aria-label="JME home">
          <span className="text-2xl">🜚</span>
          <span className="text-xl">JME</span>
        </Link>

        <nav className="flex items-center gap-2">
          {tabs.map((t) => {
            const active = pathname?.startsWith(t.href);
            return (
              <Link
                key={t.href}
                href={t.href}
                aria-current={active ? "page" : undefined}
                className={`px-3 py-1.5 rounded-md text-sm ${
                  active
                    ? "bg-white border border-teal-300 text-teal-800"
                    : "text-teal-700 hover:bg-white/60"
                }`}
              >
                {t.label}
              </Link>
            );
          })}

          {!authed ? (
            <Link
              href="/login"
              className="ml-2 px-3 py-1.5 rounded-md bg-white border border-teal-300 text-teal-800"
            >
              Log In
            </Link>
          ) : (
            <>
              <Link
                href="/profile/preferences"
                className="ml-2 px-3 py-1.5 rounded-md bg-white border text-sm"
              >
                My Account
              </Link>
              <button
                onClick={logout}
                className="px-3 py-1.5 rounded-md bg-teal-600 text-white text-sm"
              >
                Logout
              </button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
