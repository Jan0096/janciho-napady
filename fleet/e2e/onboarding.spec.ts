import { expect, test } from "@playwright/test";
import { loginLink, signIn, signOut } from "./helpers";

test("anonymous visitor is sent to login", async ({ page }) => {
  await page.goto("/users");
  await expect(page).toHaveURL(/\/login\?next=%2Fusers/);
});

test("admin invites a colleague who then joins the company", async ({ page }) => {
  const invitee = `kolega-${Date.now()}@firma.test`;

  await signIn(page, "admin@firma.test");
  await expect(page.getByRole("heading", { name: "Dobrý deň, Anna" })).toBeVisible();

  await page.getByRole("link", { name: "Používatelia", exact: true }).click();
  await page.getByLabel("E-mail kolegu").fill(invitee);
  await page.getByLabel("Rola").first().selectOption("manager");
  await page.getByRole("button", { name: "Poslať pozvánku" }).click();
  await expect(page.getByText(`Pozvánka odoslaná na ${invitee}`)).toBeVisible();
  await expect(page.getByText(invitee)).toHaveCount(2); // message + pending list
  await signOut(page);

  await signIn(page, invitee);
  await expect(page).toHaveURL(/\/onboarding/);
  await expect(page.getByText("Pozvánka do firmy Testovacia firma s.r.o.")).toBeVisible();
  await page.getByLabel("Vaše meno a priezvisko").first().fill("Karol Kolega");
  await page.getByRole("button", { name: "Pridať sa k firme" }).click();
  await expect(page.getByRole("heading", { name: "Dobrý deň, Karol" })).toBeVisible();
  await expect(page.getByText("Karol Kolega · Správca")).toBeVisible();
  // Managers do not manage users.
  await expect(page.getByRole("link", { name: "Používatelia", exact: true })).toHaveCount(0);
  await page.goto("/users");
  await expect(page).toHaveURL("/");
});

test("a stranger can found their own company and sees nothing of others", async ({ page }) => {
  const founder = `zakladatel-${Date.now()}@nova-firma.test`;
  await signIn(page, founder);
  await expect(page).toHaveURL(/\/onboarding/);
  await expect(page.getByText("Pre tento e-mail nemáme pozvánku")).toBeVisible();
  await page.getByLabel("Názov firmy").fill("Nová firma s.r.o.");
  await page.getByLabel("Vaše meno a priezvisko").fill("Zora Zakladateľka");
  await page.getByRole("button", { name: "Založiť firmu" }).click();
  await expect(page.getByRole("heading", { name: "Dobrý deň, Zora" })).toBeVisible();

  await page.goto("/users");
  await expect(page.getByText("Členovia firmy (1)")).toBeVisible();
  await expect(page.getByText("admin@firma.test")).toHaveCount(0);
});

test("the last admin cannot demote themselves", async ({ page }) => {
  const founder = `admin-${Date.now()}@solo.test`;
  await signIn(page, founder);
  await page.getByLabel("Názov firmy").fill("Solo s.r.o.");
  await page.getByLabel("Vaše meno a priezvisko").fill("Sára Sólová");
  await page.getByRole("button", { name: "Založiť firmu" }).click();
  await page.goto("/users");
  await page.getByLabel("Rola").nth(1).selectOption("driver");
  await page.getByRole("button", { name: "Uložiť" }).click();
  await expect(page.getByText("Firma musí mať aspoň jedného aktívneho administrátora.")).toBeVisible();
});

test("magic link from the e-mail works in another browser", async ({ page, browser }) => {
  const since = new Date(Date.now() - 1000);
  await page.goto("/login");
  await page.getByLabel("Váš pracovný e-mail").fill("vodic1@firma.test");
  await page.getByRole("button", { name: "Poslať prihlasovací e-mail" }).click();
  await expect(page.getByText("E-mail sme poslali")).toBeVisible();

  // e.g. requested on the PC, opened on the phone
  const otherDevice = await browser.newContext();
  const phone = await otherDevice.newPage();
  await phone.goto(await loginLink("vodic1@firma.test", since));
  await expect(phone.getByRole("heading", { name: "Dobrý deň, Jana" })).toBeVisible();
  await otherDevice.close();
});

test("an invalid magic link shows an error", async ({ page }) => {
  await page.goto("/auth/confirm?token_hash=nonsense&type=email");
  await expect(page.getByText("Odkaz na prihlásenie je neplatný")).toBeVisible();
});
