import { Card, LinkButton, PageTitle } from "@/components/ui";
import { requireProfile } from "@/lib/auth";
import { can, ROLE_DESCRIPTIONS, ROLE_LABELS } from "@/lib/roles";

export default async function HomePage() {
  const profile = await requireProfile();
  const firstName = profile.fullName.split(" ")[0];

  return (
    <>
      <PageTitle subtitle={`${ROLE_LABELS[profile.role]} – ${ROLE_DESCRIPTIONS[profile.role]}`}>
        Dobrý deň, {firstName}
      </PageTitle>

      <div className="grid gap-4 sm:grid-cols-2">
        {can(profile.role, "manageUsers") && (
          <Card>
            <h2 className="text-lg font-semibold">Používatelia</h2>
            <p className="mb-4 mt-1 text-slate-600">Pozvite kolegov a nastavte im role.</p>
            <LinkButton href="/users" className="w-full">
              Spravovať používateľov
            </LinkButton>
          </Card>
        )}
        <Card className="opacity-70">
          <h2 className="text-lg font-semibold">Autá a rezervácie</h2>
          <p className="mt-1 text-slate-600">Pripravujeme v ďalšom kroku.</p>
        </Card>
      </div>
    </>
  );
}
