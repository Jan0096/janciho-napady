"use server";

import { revalidatePath } from "next/cache";
import { requireRole } from "@/lib/auth";
import { dbErrorMessage } from "@/lib/db-errors";
import { env } from "@/lib/env";
import { isRole } from "@/lib/roles";
import { createClient, createMailerClient } from "@/lib/supabase/server";
import type { ActionState } from "@/lib/action-state";
import { isValidEmail, normalizeEmail } from "@/lib/validation";

/** Sends the login e-mail; the invitee then joins the company on the onboarding screen. */
async function sendInvitationEmail(email: string): Promise<boolean> {
  const { error } = await createMailerClient().auth.signInWithOtp({
    email,
    options: { shouldCreateUser: true, emailRedirectTo: `${env.siteUrl()}/auth/confirm` },
  });
  return !error;
}

function mailFailedMessage(email: string) {
  return `Pozvánka je uložená, ale e-mail sa nepodarilo odoslať. Nech sa ${email} prihlási na ${env.siteUrl()}.`;
}

export async function inviteUser(_prev: ActionState, formData: FormData): Promise<ActionState> {
  await requireRole("admin");
  const email = normalizeEmail(String(formData.get("email") ?? ""));
  const role = formData.get("role");
  if (!isValidEmail(email)) return { error: "Zadajte platný e-mail." };
  if (!isRole(role)) return { error: "Vyberte rolu." };

  const supabase = await createClient();
  const { error } = await supabase.rpc("create_invitation", { p_email: email, p_role: role });
  if (error) return { error: dbErrorMessage(error) };

  revalidatePath("/users");
  if (!(await sendInvitationEmail(email))) return { error: mailFailedMessage(email) };
  return { success: `Pozvánka odoslaná na ${email}.` };
}

export async function resendInvitation(_prev: ActionState, formData: FormData): Promise<ActionState> {
  await requireRole("admin");
  const supabase = await createClient();
  // RLS: admins only see invitations of their own company.
  const { data } = await supabase
    .from("invitations")
    .select("email")
    .eq("id", String(formData.get("invitation_id") ?? ""))
    .is("accepted_at", null)
    .is("revoked_at", null)
    .maybeSingle();
  if (!data) return { error: dbErrorMessage({ message: "invitation_not_found" }) };

  if (!(await sendInvitationEmail(data.email))) return { error: mailFailedMessage(data.email) };
  return { success: "Odoslané znova." };
}

export async function revokeInvitation(_prev: ActionState, formData: FormData): Promise<ActionState> {
  await requireRole("admin");
  const supabase = await createClient();
  const { error } = await supabase.rpc("revoke_invitation", {
    p_invitation_id: String(formData.get("invitation_id") ?? ""),
  });
  if (error) return { error: dbErrorMessage(error) };
  revalidatePath("/users");
  return { success: "Pozvánka zrušená." };
}

export async function changeRole(_prev: ActionState, formData: FormData): Promise<ActionState> {
  await requireRole("admin");
  const role = formData.get("role");
  if (!isRole(role)) return { error: "Vyberte rolu." };

  const supabase = await createClient();
  const { error } = await supabase.rpc("set_member_role", {
    p_user_id: String(formData.get("user_id") ?? ""),
    p_role: role,
  });
  if (error) return { error: dbErrorMessage(error) };
  revalidatePath("/", "layout");
  return { success: "Rola zmenená." };
}

export async function setActive(_prev: ActionState, formData: FormData): Promise<ActionState> {
  await requireRole("admin");
  const active = formData.get("active") === "true";
  const supabase = await createClient();
  const { error } = await supabase.rpc("set_member_active", {
    p_user_id: String(formData.get("user_id") ?? ""),
    p_active: active,
  });
  if (error) return { error: dbErrorMessage(error) };
  revalidatePath("/users");
  return { success: active ? "Účet aktivovaný." : "Účet deaktivovaný." };
}
