# Správa firemných vozidiel – projektové zadanie

Tento súbor je zadanie a pravidlá pre Claude Code. Pred každou väčšou zmenou si ho prečítaj.

## O čo ide

Webová aplikácia (PWA, mobile-first) pre malé a stredné firmy na správu firemných áut. Nahrádza papiere v aute, telefonáty a SMS s PIN-mi. Robí prácu správcu vozového parku za firmy, ktoré žiadneho nemajú.

Appka má **dva režimy**, nastavené pri každom aute:

1. **Zdieľané auto** – viacerí zamestnanci sa striedajú, jadrom je kalendár rezervácií.
2. **Pridelené auto** – jeden zamestnanec ho má 2–4 roky na služobné aj súkromné jazdy. Keď ho požičia kolegovi, zapne sa preň kalendár a požičanie sa dohodne vopred.

Prvý zákazník a testovacie prostredie je vlastná firma autora.

## Technológie

- **Next.js (App Router) + TypeScript + Tailwind CSS**
- **Supabase**: Postgres, Auth (e-mail + magic link), Storage (fotky, skeny), Row Level Security
- **PWA**: manifest + service worker, inštalovateľná na plochu telefónu
- QR čítanie cez kameru: `@zxing/browser` alebo `html5-qrcode`
- Generovanie QR: `qrcode`
- PDF export: `@react-pdf/renderer`
- Dátumy: `date-fns` s lokalizáciou `sk`
- Testy: Vitest (logika), Playwright (hlavné toky)

Nepridávaj ďalšie veľké knižnice bez toho, aby si sa najprv opýtal.

## Pravidlá

- **UI je po slovensky**, kód, názvy tabuliek, premenných a commity po anglicky.
- **Mobile-first**: vodič používa appku v telefóne, často v strese alebo v rukaviciach. Veľké tlačidlá, málo textu, jeden krok na obrazovku.
- **Správca** pracuje hlavne na počítači: tabuľky, prehľady, kalendár.
- Každá tabuľka má `organization_id` a **RLS politiky**, aby firma nikdy nevidela dáta inej firmy. Toto otestuj.
- **PIN k tankovacím kartám**: šifrovaný v databáze (pgsodium / Supabase Vault alebo šifrovanie na serveri), zobrazí sa len tomu, kto má auto práve rezervované alebo pridelené, a každé zobrazenie sa zapíše do logu.
- Fotky a skeny v Storage v privátnych bucketoch, prístup cez podpísané URL.
- **GDPR**: zbierame len to, čo treba. Poloha sa ukladá len pri prevzatí, odovzdaní a nehode, nie priebežne.
- Nevymýšľaj zákonné hodnoty (minimálny dezén, sadzby daní, podmienky privolania polície). Daj ich do nastavení alebo konštánt s komentárom `// TODO: overiť podľa aktuálnych predpisov`.
- Robím malé, funkčné kroky. Po každej fáze appka beží a dá sa vyskúšať.
- Pred väčšou zmenou databázy navrhni migráciu a opýtaj sa.

## Roly

- `admin` – nastavenia firmy, používatelia, všetko.
- `manager` (správca) – autá, doklady, schvaľovanie, kontroly, prehľady.
- `driver` (zamestnanec/vodič) – rezervácie, prevzatie, fotky, hlásenia, svoje pridelené auto.

## Dátový model (návrh, uprav podľa potreby)

- `organizations` – firma, nastavenia (schvaľovanie rezervácií áno/nie, pravidlá súkromných jázd, sezónne dátumy).
- `profiles` – používateľ, `organization_id`, `role`, meno, telefón.
- `vehicles` – EČV, značka, model, VIN, `fuel_type` (petrol, diesel, hybrid, ev), `mode` (shared, assigned), `assigned_to`, `assigned_from`, `assigned_until`, `status` (active, blocked, in_service, retired), aktuálne km, `qr_token` (náhodný, nie ID).
- `vehicle_documents` – typ (stk, ek, insurance_mtpl, insurance_casco, vignette, toll_unit, other), platné od/do, sken, kto obnovil. **Nikdy sa nemaže**, nová platnosť = nový záznam (história).
- `fuel_cards` – vozidlo, vydavateľ, číslo karty (maskované), zašifrovaný PIN.
- `pin_access_log` – kto, kedy, ktorá karta, ktorá rezervácia.
- `reservations` – vozidlo, používateľ, začiatok, koniec, `purpose` (business, private), `status` (pending, approved, active, completed, cancelled), `kind` (shared_booking, lending), dohodnuté podmienky (jsonb: miesto a čas odovzdania, palivo pri vrátení, kto platí tankovanie, zahraničie), potvrdenia strán. **Kolízie zakáž v databáze** (exclusion constraint s `tstzrange` na vozidlo, len pre aktívne stavy).
- `handovers` – prevzatie/odovzdanie: rezervácia, typ (pickup, return), km, fotka tachometra, palivo/batéria %, čas, poloha.
- `vehicle_photos` – fotky auta pri handover, uhol (front, rear, left, right, interior, dashboard).
- `quick_checks` – krátka kontrola vodiča pred jazdou (svetlá, pneumatiky, poškodenie: ok / problém + poznámka).
- `inspections` – kontroly správcu (olej, brzdová a chladiaca kvapalina, ostrekovače, tlak a dezén pneumatík, stierače, kontrolky), kto, kedy, zistenia, čo sa doplnilo.
- `defects` – nahlásená závada, `severity` (minor, blocking), stav, kto potvrdil opravu.
- `service_events` – servis, STK, prezutie, oprava: dátum, km, popis, cena, faktúra.
- `incident_reports` – interná správa o nehode/škode: typ (accident_other_party, accident_single, minor_damage), popis, fotky, poloha, km, pojazdné áno/nie, fotka papierovej správy o nehode, svedkovia, stav riešenia (reported, insurer, in_service, repaired).
- `notifications` – komu, čo, kedy, prečítané.

## Fázy

### Fáza 1 – MVP: zdieľané autá
1. Projekt, Supabase, prihlásenie, firma a pozvánky používateľov s rolami.
2. Autá: zoznam, detail, pridanie, vygenerovanie a tlač QR kódu do auta.
3. Kalendár obsadenosti (riadok = auto, týždenný/denný pohľad), vytvorenie rezervácie, zákaz kolízií, voliteľné schvaľovanie správcom.
4. Prevzatie cez QR: overenie rezervácie → doklady a PIN sa odomknú → stav km + fotka tachometra → fotky auta → krátka kontrola.
5. Odovzdanie: km, fotky, palivo, výpočet prejdených km a dĺžky jazdy.
6. Doklady a platnosti s históriou, upozornenia pred koncom platnosti (e-mail, neskôr push).
7. Hlásenie závady; blokujúca závada auto zablokuje, zruší budúce rezervácie a upozorní dotknutých.
8. Interná správa o nehode/škode (fotky + popis + automatické údaje), tlačidlo Nehoda/škoda počas jazdy, PDF export.
9. Prehľad pre správcu: kto má aké auto, blížiace sa termíny, otvorené závady a nehody.
10. Vyhľadanie „kto mal auto v čase X“ (pre pokuty).

### Fáza 2 – pridelené autá
- Režim `assigned`, digitálny odovzdávací protokol pri pridelení a vrátení (km, fotky, výbava, kľúče, karta, podpis).
- Označovanie jázd služobná/súkromná, mesačná kniha jázd, export CSV/PDF.
- Požičiavanie kolegovi cez kalendár s dohodnutými podmienkami a súhlasom.
- Pripomienky zamestnancovi (STK, servis, prezutie), mesačná samokontrola a štvrťročné fotky.
- Sledovanie limitu km pri lízingu.

### Fáza 3 – neskôr
- AI čítanie km z fotky tachometra (Claude API, vision) a AI porovnanie fotiek pred/po jazde (nálezy potvrdzuje človek).
- Plánované kontroly správcu, sezónne pneumatiky, servisná história ako „servisná knižka“.
- Auto so šoférom, elektromobily (batéria, nabíjanie, dojazd), tankovanie a spotreba.
- Offline režim pre prevzatie, fotky a nehodu.
- Export do účtovníctva, viac jazykov, natívna appka.

## Ako pracovať

- Začni Fázou 1, krokom 1. Na konci každého kroku napíš, čo je hotové a ako to vyskúšať.
- Priebežne udržiavaj `README.md` (spustenie, premenné prostredia) a `supabase/migrations/`.
- Seed dáta pre vývoj: firma, 3 autá, 4 používatelia (admin, správca, 2 vodiči), niekoľko rezervácií.
- Ak je niečo v zadaní nejasné, opýtaj sa, nehádaj.
