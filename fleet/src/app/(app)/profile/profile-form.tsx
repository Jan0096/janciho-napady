"use client";

import { useActionState } from "react";
import { Alert, Field } from "@/components/ui";
import { SubmitButton } from "@/components/submit-button";
import { initialActionState } from "@/lib/action-state";
import { updateProfile } from "./actions";

export function ProfileForm({ fullName, phone }: { fullName: string; phone: string | null }) {
  const [state, action] = useActionState(updateProfile, initialActionState);
  return (
    <form action={action} className="flex flex-col gap-4">
      <Field label="Meno a priezvisko" name="full_name" autoComplete="name" defaultValue={fullName} required />
      <Field
        label="Telefón"
        name="phone"
        type="tel"
        autoComplete="tel"
        defaultValue={phone ?? ""}
        hint="Aby vás kolegovia vedeli zastihnúť pri odovzdaní auta."
      />
      {state.error && <Alert>{state.error}</Alert>}
      {state.success && <Alert kind="success">{state.success}</Alert>}
      <SubmitButton>Uložiť</SubmitButton>
    </form>
  );
}
