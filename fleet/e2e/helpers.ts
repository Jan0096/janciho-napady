import { expect, type Page } from "@playwright/test";

const MAILPIT = process.env.MAILPIT_URL ?? "http://127.0.0.1:54324";

type MailMessage = { Text: string; HTML: string };

/** Latest login e-mail sent to `email` after `since`. */
async function latestMail(email: string, since: Date): Promise<MailMessage> {
  for (let attempt = 0; attempt < 30; attempt++) {
    const res = await fetch(`${MAILPIT}/api/v1/search?query=${encodeURIComponent(`to:${email}`)}`);
    const { messages } = (await res.json()) as { messages: { ID: string; Created: string }[] };
    const latest = messages.find((m) => new Date(m.Created) >= since);
    if (latest) {
      return (await (await fetch(`${MAILPIT}/api/v1/message/${latest.ID}`)).json()) as MailMessage;
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`No login e-mail for ${email}`);
}

export async function loginCode(email: string, since: Date): Promise<string> {
  const code = (await latestMail(email, since)).Text.match(/\b(\d{6})\b/)?.[1];
  if (!code) throw new Error("No code in login e-mail");
  return code;
}

export async function loginLink(email: string, since: Date): Promise<string> {
  const href = (await latestMail(email, since)).HTML.match(/href="([^"]*\/auth\/confirm[^"]*)"/)?.[1];
  if (!href) throw new Error("No link in login e-mail");
  return href.replaceAll("&amp;", "&");
}

export async function signIn(page: Page, email: string) {
  const since = new Date(Date.now() - 1000);
  await page.goto("/login");
  await page.getByLabel("Váš pracovný e-mail").fill(email);
  await page.getByRole("button", { name: "Poslať prihlasovací e-mail" }).click();
  await expect(page.getByText(`E-mail sme poslali na ${email}`)).toBeVisible();
  await page.getByLabel("6-miestny kód z e-mailu").fill(await loginCode(email, since));
  await page.getByRole("button", { name: "Prihlásiť sa" }).click();
}

export async function signOut(page: Page) {
  await page.goto("/profile");
  await page.getByRole("button", { name: "Odhlásiť sa" }).click();
  await expect(page).toHaveURL(/\/login/);
}
