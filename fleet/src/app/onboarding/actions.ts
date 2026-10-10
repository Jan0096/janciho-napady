"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { requireUser } from "@/lib/auth";
import { dbErrorMessage } from "@/lib/db-errors";
import type { ActionState } from "@/lib/action-state";
import { isValidName, normalizeName } from "@/lib/validation";

export async function acceptInvitation(_prev: ActionState, formData: FormData): Promise<ActionState> {
  await requireUser();
  const fullName = normalizeName(String(formData.get("full_name") ?? ""));
  if (!isValidName(fullName)) return { error: "Zadajte svoje meno a priezvisko." };

  const supabase = await createClient();
  const { error } = await supabase.rpc("accept_invitation", {
    p_invitation_id: String(formData.get("invitation_id") ?? ""),
    p_full_name: fullName,
  });
  if (error) return { error: dbErrorMessage(error) };
  redirect("/");
}

export async function createOrganization(_prev: ActionState, formData: FormData): Promise<ActionState> {
  await requireUser();
  const name = normalizeName(String(formData.get("name") ?? ""));
  const fullName = normalizeName(String(formData.get("full_name") ?? ""));
  if (!isValidName(name)) return { error: "Zadajte názov firmy." };
  if (!isValidName(fullName)) return { error: "Zadajte svoje meno a priezvisko." };

  const supabase = await createClient();
  const { error } = await supabase.rpc("create_organization", { p_name: name, p_full_name: fullName });
  if (error) return { error: dbErrorMessage(error) };
  redirect("/");
}
