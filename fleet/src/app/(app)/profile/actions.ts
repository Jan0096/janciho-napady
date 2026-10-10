"use server";

import { revalidatePath } from "next/cache";
import { requireProfile } from "@/lib/auth";
import { GENERIC_ERROR } from "@/lib/db-errors";
import { createClient } from "@/lib/supabase/server";
import type { ActionState } from "@/lib/action-state";
import { isValidName, normalizeName } from "@/lib/validation";

export async function updateProfile(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const profile = await requireProfile();
  const fullName = normalizeName(String(formData.get("full_name") ?? ""));
  const phone = String(formData.get("phone") ?? "").trim() || null;
  if (!isValidName(fullName)) return { error: "Zadajte meno a priezvisko." };
  if (phone && phone.length > 40) return { error: "Telefón je príliš dlhý." };

  const supabase = await createClient();
  const { error } = await supabase
    .from("profiles")
    .update({ full_name: fullName, phone })
    .eq("id", profile.id);
  if (error) return { error: GENERIC_ERROR };

  revalidatePath("/", "layout");
  return { success: "Uložené." };
}
