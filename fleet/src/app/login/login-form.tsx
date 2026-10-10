"use client";

import { useActionState } from "react";
import { Alert, Button, Field } from "@/components/ui";
import { SubmitButton } from "@/components/submit-button";
import { login, type LoginState } from "./actions";

const initialState: LoginState = { step: "email", email: "" };

export function LoginForm({ next }: { next: string }) {
  const [state, action] = useActionState(login, initialState);

  if (state.step === "email") {
    return (
      <form action={action} className="flex flex-col gap-4">
        <input type="hidden" name="intent" value="send" />
        <Field
          label="Váš pracovný e-mail"
          name="email"
          type="email"
          autoComplete="email"
          inputMode="email"
          required
          defaultValue={state.email}
          autoFocus
        />
        {state.error && <Alert>{state.error}</Alert>}
        <SubmitButton pendingText="Posielam…">Poslať prihlasovací e-mail</SubmitButton>
        <p className="text-sm text-slate-500">Heslo netreba. Pošleme vám odkaz a kód na prihlásenie.</p>
      </form>
    );
  }

  return (
    <form action={action} className="flex flex-col gap-4">
      <Alert kind="success">
        E-mail sme poslali na <strong>{state.email}</strong>. Kliknite na odkaz v e-maile, alebo sem zadajte kód.
      </Alert>
      <input type="hidden" name="email" value={state.email} />
      <input type="hidden" name="next" value={next} />
      <Field
        label="6-miestny kód z e-mailu"
        name="code"
        inputMode="numeric"
        autoComplete="one-time-code"
        maxLength={7}
        autoFocus
        className="text-center text-2xl tracking-[0.4em]"
      />
      {state.error && <Alert>{state.error}</Alert>}
      <SubmitButton name="intent" value="verify" pendingText="Overujem…">
        Prihlásiť sa
      </SubmitButton>
      <Button type="submit" name="intent" value="restart" variant="ghost" formNoValidate>
        Zadať iný e-mail
      </Button>
    </form>
  );
}
