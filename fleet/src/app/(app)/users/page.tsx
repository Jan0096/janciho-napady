import type { Metadata } from "next";
import { format } from "date-fns";
import { sk } from "date-fns/locale";
import { Card, PageTitle } from "@/components/ui";
import { requireRole } from "@/lib/auth";
import { createClient } from "@/lib/supabase/server";
import { ROLE_LABELS, isRole } from "@/lib/roles";
import { InvitationControls, InviteForm, MemberControls } from "./forms";

export const metadata: Metadata = { title: "Používatelia" };

function isExpired(iso: string) {
  return new Date(iso).getTime() < Date.now();
}

export default async function UsersPage() {
  const me = await requireRole("admin");
  const supabase = await createClient();

  const [{ data: members }, { data: invitations }] = await Promise.all([
    supabase.from("profiles").select("id, full_name, email, phone, role, is_active").order("full_name"),
    supabase
      .from("invitations")
      .select("id, email, role, expires_at")
      .is("accepted_at", null)
      .is("revoked_at", null)
      .order("created_at", { ascending: false }),
  ]);

  return (
    <>
      <PageTitle subtitle="Pozvite kolegov e-mailom. Prihlásia sa bez hesla a pridajú sa k firme.">
        Používatelia
      </PageTitle>

      <div className="flex flex-col gap-5">
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Pozvať kolegu</h2>
          <InviteForm />
        </Card>

        {invitations && invitations.length > 0 && (
          <Card>
            <h2 className="mb-2 text-lg font-semibold">Čakajúce pozvánky</h2>
            <ul className="divide-y divide-slate-200">
              {invitations.map((inv) => {
                const expired = isExpired(inv.expires_at);
                return (
                  <li key={inv.id} className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="font-medium text-slate-900">{inv.email}</p>
                      <p className="text-sm text-slate-600">
                        {isRole(inv.role) ? ROLE_LABELS[inv.role] : inv.role} ·{" "}
                        {expired ? (
                          <span className="text-red-700">vypršala – pozvite znova</span>
                        ) : (
                          <>platí do {format(new Date(inv.expires_at), "d. M. yyyy", { locale: sk })}</>
                        )}
                      </p>
                    </div>
                    <InvitationControls invitationId={inv.id} expired={expired} />
                  </li>
                );
              })}
            </ul>
          </Card>
        )}

        <Card>
          <h2 className="mb-2 text-lg font-semibold">Členovia firmy ({members?.length ?? 0})</h2>
          <ul className="divide-y divide-slate-200">
            {(members ?? []).map((m) => (
              <li key={m.id} className="flex flex-col gap-3 py-4 lg:flex-row lg:items-start lg:justify-between">
                <div className={m.is_active ? "" : "opacity-60"}>
                  <p className="font-medium text-slate-900">
                    {m.full_name}
                    {m.id === me.id && <span className="text-slate-500"> (vy)</span>}
                    {!m.is_active && <span className="ml-2 text-sm text-red-700">deaktivovaný</span>}
                  </p>
                  <p className="text-sm text-slate-600">
                    {m.email}
                    {m.phone && <> · {m.phone}</>}
                  </p>
                </div>
                {isRole(m.role) && (
                  <MemberControls userId={m.id} role={m.role} isActive={m.is_active} isSelf={m.id === me.id} />
                )}
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </>
  );
}
