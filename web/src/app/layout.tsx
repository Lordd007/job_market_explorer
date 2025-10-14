// web/src/app/layout.tsx
import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata = { title: "Job Market Explorer" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-teal-50 text-gray-900">
        <NavBar />
        <div className="mx-auto max-w-6xl px-4 py-6">{children}</div>
      </body>
    </html>
  );
}