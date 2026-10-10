"use client";

import { useActionState } from "react";
import { Alert, Field } from "@/components/ui";
import { SubmitButton } from "@/components/submit-button";
import { initialActionState } from "@/lib/action-state";
import { renameOrganization } from "./actions";

export function SettingsForm({ name }: { name: string }) {
  const [state, action] = useActionState(renameOrganization, initialActionState);
  return (
    <form action={action} className="flex flex-col gap-4">
      <Field label="Názov firmy" name="name" autoComplete="organization" defaultValue={name} required />
      {state.error && <Alert>{state.error}</Alert>}
      {state.success && <Alert kind="success">{state.success}</Alert>}
      <SubmitButton className="sm:self-start">Uložiť</SubmitButton>
    </form>
  );
}
