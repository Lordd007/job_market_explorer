// web/src/app/login/page.tsx
export const dynamic = "force-dynamic";

export default function LoginSmoke() {
  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold">LOGIN SMOKE</h1>
      <p>If you can see this, /login is wired in the deployed build.</p>
    </main>
  );
}
