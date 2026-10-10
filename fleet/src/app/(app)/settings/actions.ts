"use server";

import { revalidatePath } from "next/cache";
import { requireRole } from "@/lib/auth";
import { GENERIC_ERROR } from "@/lib/db-errors";
import { createClient } from "@/lib/supabase/server";
import type { ActionState } from "@/lib/action-state";
import { isValidName, normalizeName } from "@/lib/validation";

export async function renameOrganization(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const profile = await requireRole("admin");
  const name = normalizeName(String(formData.get("name") ?? ""));
  if (!isValidName(name)) return { error: "Zadajte názov firmy." };

  const supabase = await createClient();
  const { error } = await supabase.from("organizations").update({ name }).eq("id", profile.organizationId);
  if (error) return { error: GENERIC_ERROR };

  revalidatePath("/", "layout");
  return { success: "Uložené." };
}
