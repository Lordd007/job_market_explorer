"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/jobs", label: "Jobs" },
  { href: "/preferences", label: "Preferences" },
  { href: "/feedback", label: "Feedback" },
  { href: "/support", label: "Support Us" },
];

export default function NavBar() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-20 bg-teal-50/90 backdrop-blur border-b border-teal-200">
      <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
        <Link href="/jobs" className="flex items-center gap-2 font-semibold text-teal-800">
          <span className="text-2xl">🜚</span>
          <span className="text-xl">JME</span>
        </Link>
        <nav className="flex items-center gap-2">
          {tabs.map(t => {
            const active = pathname?.startsWith(t.href);
            return (
              <Link
                key={t.href}
                href={t.href}
                className={`px-3 py-1.5 rounded-md text-sm ${
                  active ? "bg-white border border-teal-300 text-teal-800" : "text-teal-700 hover:bg-white/60"
                }`}
              >
                {t.label}
              </Link>
            );
          })}
          <Link href="/login" className="ml-2 px-3 py-1.5 rounded-md bg-teal-600 text-white text-sm">
            Log In
          </Link>
        </nav>
      </div>
    </header>
  );
}
