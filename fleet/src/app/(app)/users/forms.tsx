"use client";

import { useActionState } from "react";
import { Alert, Field, Select } from "@/components/ui";
import { SubmitButton } from "@/components/submit-button";
import { initialActionState, type ActionState } from "@/lib/action-state";
import { ROLE_LABELS, ROLES, type Role } from "@/lib/roles";
import { changeRole, inviteUser, resendInvitation, revokeInvitation, setActive } from "./actions";

function Feedback({ state }: { state: ActionState }) {
  if (state.error) return <Alert>{state.error}</Alert>;
  if (state.success) return <Alert kind="success">{state.success}</Alert>;
  return null;
}

function RoleOptions() {
  return ROLES.map((r) => (
    <option key={r} value={r}>
      {ROLE_LABELS[r]}
    </option>
  ));
}

export function InviteForm() {
  const [state, action] = useActionState(inviteUser, initialActionState);
  return (
    <form action={action} className="flex flex-col gap-4">
      <div className="grid gap-4 sm:grid-cols-[1fr_12rem]">
        <Field label="E-mail kolegu" name="email" type="email" inputMode="email" autoComplete="off" required />
        <Select label="Rola" name="role" defaultValue="driver">
          <RoleOptions />
        </Select>
      </div>
      <Feedback state={state} />
      <SubmitButton pendingText="Posielam…" className="sm:self-start">
        Poslať pozvánku
      </SubmitButton>
    </form>
  );
}

export function MemberControls({
  userId,
  role,
  isActive,
  isSelf,
}: {
  userId: string;
  role: Role;
  isActive: boolean;
  isSelf: boolean;
}) {
  const [roleState, roleAction] = useActionState(changeRole, initialActionState);
  const [activeState, activeAction] = useActionState(setActive, initialActionState);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-end gap-2">
        <form action={roleAction} className="flex items-end gap-2">
          <input type="hidden" name="user_id" value={userId} />
          <Select label="Rola" name="role" defaultValue={role} disabled={!isActive}>
            <RoleOptions />
          </Select>
          <SubmitButton variant="secondary" disabled={!isActive}>
            Uložiť
          </SubmitButton>
        </form>
        {!isSelf && (
          <form action={activeAction}>
            <input type="hidden" name="user_id" value={userId} />
            <input type="hidden" name="active" value={String(!isActive)} />
            <SubmitButton variant={isActive ? "danger" : "secondary"}>
              {isActive ? "Deaktivovať" : "Aktivovať"}
            </SubmitButton>
          </form>
        )}
      </div>
      <Feedback state={roleState} />
      <Feedback state={activeState} />
    </div>
  );
}

export function InvitationControls({ invitationId, expired }: { invitationId: string; expired: boolean }) {
  const [resendState, resendAction] = useActionState(resendInvitation, initialActionState);
  const [revokeState, revokeAction] = useActionState(revokeInvitation, initialActionState);
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        {!expired && (
          <form action={resendAction}>
            <input type="hidden" name="invitation_id" value={invitationId} />
            <SubmitButton variant="secondary">Poslať znova</SubmitButton>
          </form>
        )}
        <form action={revokeAction}>
          <input type="hidden" name="invitation_id" value={invitationId} />
          <SubmitButton variant="danger">Zrušiť</SubmitButton>
        </form>
      </div>
      <Feedback state={resendState} />
      <Feedback state={revokeState} />
    </div>
  );
}
