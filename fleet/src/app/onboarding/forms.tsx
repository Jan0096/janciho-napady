"use client";

import { useActionState } from "react";
import { Alert, Field } from "@/components/ui";
import { SubmitButton } from "@/components/submit-button";
import { initialActionState } from "@/lib/action-state";
import { acceptInvitation, createOrganization } from "./actions";

export function AcceptInvitationForm({ invitationId }: { invitationId: string }) {
  const [state, action] = useActionState(acceptInvitation, initialActionState);
  return (
    <form action={action} className="flex flex-col gap-4">
      <input type="hidden" name="invitation_id" value={invitationId} />
      <Field label="Vaše meno a priezvisko" name="full_name" autoComplete="name" required minLength={2} />
      {state.error && <Alert>{state.error}</Alert>}
      <SubmitButton>Pridať sa k firme</SubmitButton>
    </form>
  );
}

export function CreateOrganizationForm() {
  const [state, action] = useActionState(createOrganization, initialActionState);
  return (
    <form action={action} className="flex flex-col gap-4">
      <Field label="Názov firmy" name="name" autoComplete="organization" required minLength={2} />
      <Field label="Vaše meno a priezvisko" name="full_name" autoComplete="name" required minLength={2} />
      {state.error && <Alert>{state.error}</Alert>}
      <SubmitButton variant="secondary">Založiť firmu</SubmitButton>
      <p className="text-sm text-slate-500">Stanete sa administrátorom a môžete pozvať kolegov.</p>
    </form>
  );
}
