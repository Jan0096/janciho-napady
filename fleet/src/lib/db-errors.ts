/** Error codes raised by our SQL functions (see supabase/migrations). */
const MESSAGES: Record<string, string> = {
  not_authenticated: "Nie ste prihlásený. Prihláste sa znova.",
  forbidden: "Na túto akciu nemáte oprávnenie.",
  already_member: "Tento používateľ už je členom firmy.",
  invitation_not_found: "Pozvánka neexistuje, vypršala alebo bola zrušená.",
  member_not_found: "Používateľ sa nenašiel.",
  last_admin: "Firma musí mať aspoň jedného aktívneho administrátora.",
};

export const GENERIC_ERROR = "Niečo sa pokazilo. Skúste to znova.";

export function dbErrorMessage(error: { message?: string } | null | undefined): string {
  if (!error?.message) return GENERIC_ERROR;
  const key = Object.keys(MESSAGES).find((k) => error.message!.includes(k));
  return key ? MESSAGES[key] : GENERIC_ERROR;
}
