import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { Card, PageTitle } from "@/components/ui";
import { SignOutButton } from "@/components/sign-out-button";
import { getProfile, requireUser } from "@/lib/auth";

export const metadata: Metadata = { title: "Účet deaktivovaný" };

export default async function DeactivatedPage() {
  await requireUser();
  const profile = await getProfile();
  if (!profile) redirect("/onboarding");
  if (profile.isActive) redirect("/");

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-5 px-4 py-8">
      <PageTitle>Účet je deaktivovaný</PageTitle>
      <Card>
        <p className="text-slate-700">
          Administrátor vašej firmy vám zablokoval prístup. Ak ide o omyl, kontaktujte ho.
        </p>
      </Card>
      <SignOutButton />
    </main>
  );
}
