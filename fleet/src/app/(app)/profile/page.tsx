import type { Metadata } from "next";
import { Card, PageTitle } from "@/components/ui";
import { SignOutButton } from "@/components/sign-out-button";
import { requireProfile } from "@/lib/auth";
import { ROLE_LABELS } from "@/lib/roles";
import { ProfileForm } from "./profile-form";

export const metadata: Metadata = { title: "Môj profil" };

export default async function ProfilePage() {
  const profile = await requireProfile();
  return (
    <div className="mx-auto flex max-w-md flex-col gap-5">
      <PageTitle subtitle={`${profile.email} · ${ROLE_LABELS[profile.role]} · ${profile.organizationName}`}>
        Môj profil
      </PageTitle>
      <Card>
        <ProfileForm fullName={profile.fullName} phone={profile.phone} />
      </Card>
      <SignOutButton />
    </div>
  );
}
