import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { Alert, Card } from "@/components/ui";
import { getAuthUser } from "@/lib/auth";
import { safeNextPath } from "@/lib/validation";
import { LoginForm } from "./login-form";

export const metadata: Metadata = { title: "Prihlásenie" };

export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const params = await searchParams;
  const next = safeNextPath(typeof params.next === "string" ? params.next : null);

  if (await getAuthUser()) redirect(next);

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-6 px-4 py-10">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-slate-900">Správa vozidiel</h1>
        <p className="mt-2 text-slate-600">Firemné autá bez papierov a telefonátov</p>
      </div>
      <Card>
        {params.error === "link" && (
          <div className="mb-4">
            <Alert>Odkaz na prihlásenie je neplatný alebo už vypršal. Pošlite si nový.</Alert>
          </div>
        )}
        <LoginForm next={next} />
      </Card>
    </main>
  );
}
