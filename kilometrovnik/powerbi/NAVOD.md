# Drivee → Power BI: návod krok za krokom

Tento priečinok obsahuje všetko na finančný prehľad dopravy v **Power BI Desktop**
(zadarmo pre Windows, Microsoft Store alebo powerbi.microsoft.com).

| Súbor | Na čo slúži |
|---|---|
| `dotazy-power-query.m` | Načítanie CSV z appky (Power Query) |
| `miery.dax` | Tabuľka Kalendár a všetky výpočty (tržby, zisk, marža, pohľadávky, cash flow, státie) |
| `vzorove-data/` | Ukážkové `jazdy.csv`, `firmy.csv`, `vozidla.csv`, `faktury.csv`, `plan_nakladov.csv` na vyskúšanie bez vlastných dát |

## 1. Priprav dáta

1. V appke otvor záložku **5. Financie a Power BI**.
2. Klikni **Stiahnuť všetky súbory** (jazdy, firmy, vozidlá, faktúry, plán nákladov) a ulož ich do jedného priečinka, napr. `C:\Kilometrovnik\`.
   Na vyskúšanie môžeš skopírovať súbory z `vzorove-data/`.
3. Aby boli financie presné, v záložke **Porovnanie ponúk** označuj jazdy ako
   **Zrealizovaná** a po prijatí platby **Zaplatená**. Pri ocenení jazdy vypĺňaj **Firmu**,
   **Dátum jazdy** a **Splatnosť faktúry**.

## 2. Načítaj dáta do Power BI

1. Otvor Power BI Desktop → **Prázdna zostava**.
2. **Domov → Transformovať údaje** (otvorí sa Power Query editor).
3. **Nový zdroj → Prázdny dotaz**, potom **Rozšírený editor**. Vlož blok `PriecinokDat`
   zo súboru `dotazy-power-query.m`, ulož a dotaz premenuj na `PriecinokDat`.
   Ak máš súbory inde, uprav cestu (musí končiť `\`).
4. Rovnako vytvor dotazy **Jazdy**, **Firmy**, **Vozidla**, **Faktury** a **PlanNakladov** (každý blok = jeden prázdny dotaz).
5. **Zavrieť a použiť**.

## 3. Prepoj tabuľky (zobrazenie Model)

1. **Modelovanie → Nová tabuľka** a vlož vzorec `Kalendar` zo súboru `miery.dax`.
   Potom **Označiť ako tabuľku dátumov** → stĺpec `Date`.
2. Rovnako vytvor tabuľku `Kategorie` (vzorec je v časti NÁKLADOVÉ FAKTÚRY v `miery.dax`).
3. V zobrazení **Model** pretiahni vzťahy (všetky 1 : N, jeden smer):

| Z tabuľky (1) | Do tabuľky (N) | Aktívny |
|---|---|---|
| `Firmy[firma]` | `Jazdy[firma]` | áno |
| `Vozidla[id]` | `Jazdy[vozidlo_id]` | áno |
| `Kalendar[Date]` | `Jazdy[datum]` | áno |
| `Kalendar[Date]` | `Jazdy[datum_splatnosti]` | **nie** (neaktívny, používa ho miera Očakávané príjmy) |
| `Kalendar[Date]` | `Faktury[datum]` | áno |
| `Vozidla[id]` | `Faktury[vozidlo_id]` | áno |
| `Vozidla[id]` | `PlanNakladov[vozidlo_id]` | áno |
| `Kategorie[kategoria]` | `Faktury[kategoria]` | áno |
| `Kategorie[kategoria]` | `PlanNakladov[kategoria]` | áno |

Faktúry bez vozidla (`vozidlo_id` prázdne) sú náklady celej firmy. Pri filtri na jedno auto sa nezobrazia.

## 4. Pridaj miery

V tabuľke **Jazdy** daj **Nová miera** a postupne vlož každú mieru zo súboru `miery.dax`
(každá začína `Názov = ...`). Percentá (Marža %, Km naprázdno % …) nastav na formát **Percento**,
sumy na **Mena €**.

## 5. Odporúčané strany zostavy

**Prehľad**
- Karty: `Tržby zrealizované`, `Zisk zrealizovaný`, `Marža zrealizovaná %`, `Zisk na deň`, `Km naprázdno %`.
- Čiarový graf: os X `Kalendar[Mesiac]`, hodnoty `Tržby zrealizované` a `Zisk zrealizovaný`.
- Slicery: `Kalendar[Mesiac]`, `Vozidla[nazov]`, `Jazdy[Stav jazdy]`.

**Firmy – pre koho sa oplatí jazdiť**
- Pruhový graf: os `Firmy[firma]`, hodnota `Zisk na deň`, zoradiť zostupne;
  farba pruhov cez **fx → Hodnota poľa → Farba zisku** (zelená zisk, červená strata).
- Tabuľka: `firma`, `Počet jázd`, `Tržby`, `Zisk`, `Marža %`, `Tržba na km`, `Náklad na km`,
  `Priemerná splatnosť (dni)`, `Neuhradené faktúry`, `Hodnotenie firmy`.
- Bodový graf: X `Priemerná splatnosť (dni)`, Y `Marža %`, veľkosť `Tržby`, podrobnosti `firma`.
  Vpravo dole sú firmy, ktoré platia neskoro a s nízkou maržou.

**Cash flow a pohľadávky**
- Karty: `Neuhradené faktúry`, `Po splatnosti`, `Po splatnosti %`.
- Stĺpcový graf: os `Kalendar[Mesiac]`, hodnota `Očakávané príjmy` (kedy prídu peniaze).
- Tabuľka filtrovaná na `Jazdy[Úhrada]` = *Po splatnosti*: firma, trasa, dátum splatnosti, tržba.

**Vozidlá a státie**
- Tabuľka: `Vozidla[nazov]`, `Tržby zrealizované`, `Zisk zrealizovaný`, `Náklad na km`, `Využitie vozidiel %`.
- Karty: `Fixné náklady za obdobie`, `Náklady na státie`, `Výsledok hospodárenia (odhad)`.
  Pozeraj ich s filtrom na mesiac, bez filtra na firmu.

**Skutočné náklady vs. plán (faktúry)**
- Karty: `Skutočné náklady`, `Plán nákladov`, `Odchýlka od plánu %`, `Nezaradené faktúry`, `Výsledok podľa faktúr`.
- Zoskupený pruhový graf: os `Kategorie[kategoria]`, hodnoty `Skutočné náklady` a `Plán nákladov`.
- Tabuľka: `kategoria`, `Skutočné náklady`, `Plán nákladov`, `Odchýlka od plánu`, `Odchýlka od plánu %`
  (farba písma cez **fx → Hodnota poľa → Farba odchýlky**).
- Čiarový graf: os `Kalendar[Mesiac]`, hodnota `Skutočné náklady`, legenda `Kategorie[kategoria]`.
- Slicery: `Kalendar[Mesiac]`, `Vozidla[nazov]`. Nezaradené faktúry zaraď v appke a exportuj znova.

**Prázdne km**
- Karty: `Km naprázdno %`, `Prázdne jazdy – km`, `Náklady na prázdne km (odhad)`.
- Stĺpcový graf: os `Jazdy[dovod]` (filter `Jazdy[typ]` = *prazdna*), hodnota `Prázdne jazdy – náklady`.
- Čiarový graf: os `Kalendar[Mesiac]`, hodnota `Km naprázdno %`.
- Čakanie: karty `Čakanie – hodiny`, `Čakanie – náklady`, `Zdržné vyúčtované`, `Čakanie – nepokryté náklady`;
  pruhový graf os `Firmy[firma]`, hodnota `Čakanie – hodiny` (u ktorých zákazníkov sa najviac čaká); pruhový graf os `Jazdy[dovod]` ukáže, koľko času a peňazí stojí čakanie na nakládke, vykládke a na colnici.

## 6. Aktualizácia

Keď v appke pribudnú jazdy alebo úhrady: znova **Stiahnuť všetky 3 súbory** do toho istého
priečinka (prepísať) → v Power BI **Domov → Obnoviť**.

## Ako sa počítajú financie

- **Náklady jazdy** = variabilné (nafta, AdBlue, pneu, servis) za všetky km + fixné náklady auta
  za dni na ceste + diéty + mýto + iné. Rozpis je v stĺpcoch `variabilne_naklady`, `fixne_naklady`,
  `diety`, `myto`, `ine_naklady`.
- **Náklady na státie** = fixné náklady všetkých áut za vybrané mesiace mínus fixné náklady,
  ktoré už pokryli zrealizované jazdy. Sú to peniaze, ktoré auto stojí, keď nejazdí.
- **Výsledok hospodárenia (odhad)** = zisk zo zrealizovaných jázd − náklady na státie.
  Je to odhad podľa nákladov zadaných v appke, nie údaj z účtovníctva.
- **Faktúry** sa v appke zaraďujú samé: najprv podľa zapamätaného dodávateľa, potom podľa slov
  v dodávateľovi a popise (nafta, mýto, servis, leasing…). K autu sa priradia podľa ŠPZ v popise.
  **Plán nákladov** pochádza z nastavení vozidla v appke (mesačne), mýto nemá plán, lebo závisí od trás.
- **Prázdne jazdy** (stĺpec `typ` = `prazdna`) nemajú tržbu, len náklady. **Čakanie** (`typ` = `cakanie`) má náklady za hodiny státia (fixné náklady auta a diéty) a ako tržbu prípadné zdržné. Ak sú priradené firme, ovplyvnia jej zisk.
- Všetky sumy sú **bez DPH**.
