# 🚗 Správa vozidiel

Webová aplikácia (PWA, mobile-first) na správu firemných áut. Zadanie a pravidlá: [`CLAUDE.md`](./CLAUDE.md).

**Stav:** Fáza 1, krok 1 – prihlásenie, firma, pozvánky používateľov s rolami.

## Čo už funguje

Ukážky obrazoviek (vymyslené dáta): [`docs/screenshots/`](./docs/screenshots).

- **Prihlásenie bez hesla** – e-mail s odkazom aj 6-miestnym kódom (kód sa hodí v appke nainštalovanej na ploche telefónu; odkaz funguje aj na inom zariadení, než kde ste o prihlásenie požiadali).
- **Založenie firmy** – kto nemá pozvánku, môže založiť firmu a stane sa jej administrátorom.
- **Pozvánky** – admin zadá e-mail a rolu (Administrátor / Správca / Vodič). Kolega dostane e-mail, prihlási sa a pridá sa k firme. Pozvánka platí 14 dní, dá sa poslať znova alebo zrušiť.
- **Správa používateľov** – zmena roly, deaktivácia účtu (nemaže sa). Firma nemôže ostať bez aktívneho administrátora.
- **Môj profil** – meno a telefón, odhlásenie.
- **Oddelenie firiem** – každá tabuľka má `organization_id` a RLS politiky; firma nikdy nevidí dáta inej firmy (overené testami).

## Technológie

Next.js 16 (App Router) + TypeScript + Tailwind CSS 4, Supabase (Postgres, Auth, RLS), Vitest, Playwright.

> Next.js 16 má zmeny oproti starším verziám (napr. `middleware.ts` → `src/proxy.ts`). Dokumentácia k nainštalovanej verzii je v `node_modules/next/dist/docs/`.

## Spustenie lokálne (vývoj)

Potrebuješ **Node.js 20+** a **Docker** (pre lokálny Supabase).

```bash
cd fleet
npm install
npm run db:start          # spustí lokálny Supabase, aplikuje migrácie a seed
cp .env.example .env.local
# do .env.local vlož PUBLISHABLE_KEY, ktorý vypísal db:start (alebo `npx supabase status`)
npm run dev               # http://localhost:3000
```

Prihlasovacie e-maily lokálne nikam neodchádzajú – nájdeš ich v **Mailpite: http://localhost:54324**.

Seed dáta (firma „Testovacia firma s.r.o.“):

| E-mail | Rola |
|---|---|
| admin@firma.test | Administrátor |
| spravca@firma.test | Správca |
| vodic1@firma.test | Vodič |
| vodic2@firma.test | Vodič |
| nova@firma.test | (čakajúca pozvánka – vyskúšaj pridanie k firme) |

Autá a rezervácie pribudnú do seedu v ďalších krokoch.

`npm run db:reset` zmaže lokálnu databázu a znova aplikuje migrácie + seed.

## Premenné prostredia

| Premenná | Popis |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | URL Supabase projektu |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Publishable key (`sb_publishable_…`) alebo starší „anon“ kľúč |
| `NEXT_PUBLIC_SITE_URL` | Verejná adresa appky (odkazy v e-mailoch), napr. `https://vozidla.mojafirma.sk` |

`service_role` / secret kľúč appka **nepotrebuje** a nikdy ho nedávaj do premenných s `NEXT_PUBLIC_`.

## Nasadenie na Supabase cloud

1. Na **https://supabase.com** vytvor projekt (región EU, napr. Frankfurt).
2. Migrácie: `npx supabase login`, `npx supabase link --project-ref <ref>`, `npx supabase db push`.
   (Alebo skopíruj obsah súborov zo `supabase/migrations/` do **SQL Editora** v poradí podľa názvu.)
   Seed (`supabase/seed.sql`) na produkciu **nespúšťaj**.
3. **Authentication → URL Configuration:** *Site URL* = adresa appky, do *Redirect URLs* pridaj `https://<adresa>/**`.
4. **Authentication → Email Templates → Magic Link** aj **Confirm signup:** predmet „Prihlásenie do Správy vozidiel“, telo skopíruj zo `supabase/templates/magic_link.html`. Bez toho by odkaz nefungoval na inom zariadení a v e-maile by nebol kód.
5. **Authentication → SMTP Settings:** nastav vlastné SMTP (napr. Brevo, Resend, firemný server). Vstavaný e-mail Supabase posiela len pár e-mailov za hodinu a len členom tímu projektu – na pozvánky kolegov nestačí.
6. Appku nasaď napr. na Vercel s premennými prostredia vyššie.

## Testy

```bash
npm test            # Vitest – logika (validácie, roly, chybové hlášky)
npm run test:db     # migrácie + RLS/RPC testy na dočasnom Postgres (bez Dockeru, treba Postgres binárky)
npm run test:e2e    # Playwright – hlavné toky (treba bežiaci `npm run db:start`)
npm run lint && npm run typecheck
```

`test:db` (`supabase/db-tests/`) overuje izoláciu firiem: vodič nevidí inú firmu, nemôže si zmeniť rolu, správca nemôže pozývať, admin nemôže meniť používateľov inej firmy, deaktivovaný účet nevidí nič, cudzí človek nemôže použiť cudziu pozvánku atď.

## Štruktúra

```
src/proxy.ts                 obnovenie session, presmerovanie neprihlásených na /login
src/lib/auth.ts              aktuálny používateľ a profil, requireProfile / requireRole
src/lib/supabase/            Supabase klienti (server, proxy)
src/app/login, auth/         prihlásenie, overenie odkazu, odhlásenie
src/app/onboarding/          prijatie pozvánky / založenie firmy
src/app/(app)/               chránená časť: domov, používatelia, firma, profil
supabase/migrations/         schéma databázy + RLS
supabase/seed.sql            vývojové dáta
supabase/db-tests/           testy RLS
e2e/                         Playwright testy
```

## Databáza (krok 1)

- `organizations` – firma, `settings` (jsonb pre ďalšie nastavenia).
- `profiles` – používateľ (`id` = `auth.users.id`), `organization_id`, `role` (`admin`/`manager`/`driver`), meno, telefón, e-mail, `is_active`.
- `invitations` – e-mail, rola, platnosť, prijatie/zrušenie (história sa nemaže).

Klienti môžu cez API len **čítať** (podľa RLS) a meniť si vlastné meno a telefón. Všetko ostatné (založenie firmy, pozvánky, roly, deaktivácia) ide cez databázové funkcie, ktoré oprávnenie overia samy.
