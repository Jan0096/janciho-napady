"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { env } from "@/lib/env";
import { isValidEmail, isValidOtp, normalizeEmail, normalizeOtp, safeNextPath } from "@/lib/validation";

export type LoginState = { step: "email" | "code"; email: string; error?: string };

/** Two-step login: send a magic link + code, then optionally verify the code. */
export async function login(_prev: LoginState, formData: FormData): Promise<LoginState> {
  const intent = String(formData.get("intent") ?? "send");
  const email = normalizeEmail(String(formData.get("email") ?? ""));

  if (intent === "restart") {
    return { step: "email", email };
  }
  if (!isValidEmail(email)) {
    return { step: "email", email, error: "Zadajte platný e-mail." };
  }

  const supabase = await createClient();

  if (intent === "verify") {
    const token = normalizeOtp(String(formData.get("code") ?? ""));
    if (!isValidOtp(token)) {
      return { step: "code", email, error: "Kód má 6 číslic." };
    }
    const { error } = await supabase.auth.verifyOtp({ email, token, type: "email" });
    if (error) {
      return { step: "code", email, error: "Kód je nesprávny alebo vypršal." };
    }
    redirect(safeNextPath(String(formData.get("next") ?? "")));
  }

  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: { shouldCreateUser: true, emailRedirectTo: `${env.siteUrl()}/auth/confirm` },
  });
  if (error) {
    return {
      step: "email",
      email,
      error:
        error.status === 429
          ? "Príliš veľa pokusov. Počkajte chvíľu a skúste znova."
          : "E-mail sa nepodarilo odoslať. Skúste to znova.",
    };
  }
  return { step: "code", email };
}
