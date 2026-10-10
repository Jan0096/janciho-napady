import Link from "next/link";
import { requireProfile } from "@/lib/auth";
import { can, ROLE_LABELS } from "@/lib/roles";

export default async function AppLayout({ children }: LayoutProps<"/">) {
  const profile = await requireProfile();

  const nav = [
    { href: "/", label: "Domov", show: true },
    { href: "/users", label: "Používatelia", show: can(profile.role, "manageUsers") },
    { href: "/settings", label: "Firma", show: can(profile.role, "manageOrganization") },
  ].filter((item) => item.show);

  return (
    <>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-x-4 gap-y-2 px-4 py-3">
          <Link href="/" className="min-w-0">
            <span className="block truncate text-lg font-bold text-slate-900">{profile.organizationName}</span>
          </Link>
          <Link
            href="/profile"
            className="flex min-h-12 items-center rounded-xl px-3 text-sm text-slate-700 hover:bg-slate-100"
          >
            {profile.fullName} · {ROLE_LABELS[profile.role]}
          </Link>
          {nav.length > 1 && (
            <nav className="-mx-1 flex w-full gap-1 overflow-x-auto">
              {nav.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex min-h-11 items-center rounded-lg px-4 font-medium text-slate-700 hover:bg-slate-100"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          )}
        </div>
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">{children}</main>
    </>
  );
}
