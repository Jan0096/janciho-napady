import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { format } from "date-fns";
import { sk } from "date-fns/locale";
import { Card, PageTitle } from "@/components/ui";
import { SignOutButton } from "@/components/sign-out-button";
import { getProfile, requireUser } from "@/lib/auth";
import { createClient } from "@/lib/supabase/server";
import { ROLE_LABELS, isRole } from "@/lib/roles";
import { AcceptInvitationForm, CreateOrganizationForm } from "./forms";

export const metadata: Metadata = { title: "Vitajte" };

type PendingInvitation = { id: string; organization_name: string; role: string; expires_at: string };

export default async function OnboardingPage() {
  const user = await requireUser();
  if (await getProfile()) redirect("/");

  const supabase = await createClient();
  const { data } = await supabase.rpc("my_pending_invitations");
  const invitations = (data ?? []) as PendingInvitation[];

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-5 px-4 py-8">
      <PageTitle subtitle={<>Prihlásený ako {user.email}</>}>Vitajte</PageTitle>

      {invitations.map((inv) => (
        <Card key={inv.id}>
          <h2 className="text-lg font-semibold text-slate-900">Pozvánka do firmy {inv.organization_name}</h2>
          <p className="mb-4 mt-1 text-slate-600">
            Rola: {isRole(inv.role) ? ROLE_LABELS[inv.role] : inv.role} · platí do{" "}
            {format(new Date(inv.expires_at), "d. M. yyyy", { locale: sk })}
          </p>
          <AcceptInvitationForm invitationId={inv.id} />
        </Card>
      ))}

      {invitations.length === 0 && (
        <Card>
          <p className="text-slate-700">
            Pre tento e-mail nemáme pozvánku. Ak vás má pridať firma, požiadajte administrátora, aby vás pozval
            na adresu <strong>{user.email}</strong>.
          </p>
        </Card>
      )}

      <Card>
        <h2 className="mb-4 text-lg font-semibold text-slate-900">Založiť novú firmu</h2>
        <CreateOrganizationForm />
      </Card>

      <SignOutButton />
    </main>
  );
}
