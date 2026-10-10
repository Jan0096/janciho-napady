import "server-only";
import { cache } from "react";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { isRole, type Role } from "@/lib/roles";

export type AuthUser = { id: string; email: string };

export type Profile = {
  id: string;
  organizationId: string;
  organizationName: string;
  role: Role;
  fullName: string;
  phone: string | null;
  email: string;
  isActive: boolean;
};

/** Signed-in user from the verified JWT, or null. */
export const getAuthUser = cache(async (): Promise<AuthUser | null> => {
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();
  const claims = data?.claims;
  if (!claims?.sub) return null;
  return { id: claims.sub, email: String(claims.email ?? "") };
});

/** Profile of the signed-in user, or null if they have not joined a company yet. */
export const getProfile = cache(async (): Promise<Profile | null> => {
  const user = await getAuthUser();
  if (!user) return null;

  const supabase = await createClient();
  const { data, error } = await supabase
    .from("profiles")
    .select("id, organization_id, role, full_name, phone, email, is_active, organizations(name)")
    .eq("id", user.id)
    .maybeSingle();

  if (error) throw new Error(`Failed to load profile: ${error.message}`);
  if (!data || !isRole(data.role)) return null;

  const org = data.organizations as { name: string } | { name: string }[] | null;
  return {
    id: data.id,
    organizationId: data.organization_id,
    organizationName: (Array.isArray(org) ? org[0]?.name : org?.name) ?? "",
    role: data.role,
    fullName: data.full_name,
    phone: data.phone,
    email: data.email,
    isActive: data.is_active,
  };
});

export async function requireUser(): Promise<AuthUser> {
  const user = await getAuthUser();
  if (!user) redirect("/login");
  return user;
}

/** Signed-in, active member of a company. */
export async function requireProfile(): Promise<Profile> {
  await requireUser();
  const profile = await getProfile();
  if (!profile) redirect("/onboarding");
  if (!profile.isActive) redirect("/deactivated");
  return profile;
}

export async function requireRole(...roles: Role[]): Promise<Profile> {
  const profile = await requireProfile();
  if (!roles.includes(profile.role)) redirect("/");
  return profile;
}
