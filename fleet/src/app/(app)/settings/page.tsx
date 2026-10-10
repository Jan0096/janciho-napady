import type { Metadata } from "next";
import { Card, PageTitle } from "@/components/ui";
import { requireRole } from "@/lib/auth";
import { SettingsForm } from "./settings-form";

export const metadata: Metadata = { title: "Nastavenia firmy" };

export default async function SettingsPage() {
  const profile = await requireRole("admin");
  return (
    <div className="flex max-w-xl flex-col gap-5">
      <PageTitle subtitle="Ďalšie nastavenia (schvaľovanie rezervácií, pravidlá jázd) pribudnú v ďalších krokoch.">
        Nastavenia firmy
      </PageTitle>
      <Card>
        <SettingsForm name={profile.organizationName} />
      </Card>
    </div>
  );
}
