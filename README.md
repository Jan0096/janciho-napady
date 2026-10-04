# 💡 Janciho nápady

Jednoduchá webová aplikácia na nahrávanie a hodnotenie nápadov. Beží priamo v prehliadači, nič netreba inštalovať.

## Čo appka vie

1. **🎤 Nahrať nápad** – hovoríš do mikrofónu po slovensky a text sa priebežne prepisuje do poľa. Potom ho môžeš ručne upraviť.
2. **Moje slovné hodnotenie** – sem napíšeš, čo si o nápade myslíš.
3. **Hodnotenie 1–10** v troch kategóriách: Konkurencia, Udržateľnosť, Kvalita nápadu (posuvníky).
4. **✨ Navrhni skóre** – Claude (umelá inteligencia od Anthropic) prečíta nápad a tvoje hodnotenie, nastaví skóre a ku každému pridá krátke odôvodnenie.
5. **💾 Uložiť nápad** – uloží nápad do zoznamu nižšie (ostane v prehliadači aj po zatvorení).

## Súbory

| Súbor | Na čo slúži |
|---|---|
| `index.html` | Štruktúra stránky (tlačidlá, textové polia, posuvníky) |
| `style.css` | Vzhľad (farby, rozloženie) |
| `app.js` | Logika: rozpoznávanie reči, volanie Claude, ukladanie |

## Ako appku spustiť

1. Stiahni si súbory do počítača (na GitHube zelené tlačidlo **Code → Download ZIP**, potom ZIP rozbaľ).
2. Otvor priečinok a **dvakrát klikni na `index.html`**.
3. Stránka sa musí otvoriť v **Google Chrome** alebo **Microsoft Edge** – iba tieto prehliadače podporujú rozpoznávanie reči. Ak sa otvorí v inom prehliadači, klikni na súbor pravým tlačidlom → **Otvoriť v programe** → Chrome.
4. Pri prvom kliknutí na **Nahrať nápad** sa prehliadač spýta na povolenie mikrofónu → klikni **Povoliť**.

> Potrebuješ internet – prepis reči aj Claude bežia online.

## Ako získať API kľúč (pre tlačidlo „Navrhni skóre“)

Nahrávanie a ručné hodnotenie fungujú aj bez kľúča. Kľúč treba iba na automatický návrh skóre.

1. Choď na **https://console.anthropic.com** a zaregistruj sa (e-mail alebo Google účet).
2. V ľavom menu otvor **Billing** (Fakturácia) a pridaj kredit – stačí minimum (napr. 5 $). Jedno hodnotenie stojí len zlomok centu.
3. V ľavom menu otvor **API Keys** a klikni **Create Key**.
4. Kľúč pomenuj (napr. „napady“) a klikni **Create**.
5. Kľúč (začína `sk-ant-...`) si **hneď skopíruj** – zobrazí sa iba raz.
6. V appke rozklikni hore **⚙️ Nastavenia (API kľúč)**, vlož kľúč do poľa a klikni **Uložiť kľúč**.

Kľúč sa ukladá len v tvojom prehliadači na tvojom počítači. **Nikomu ho neposielaj a nedávaj ho do súborov na GitHub.** Ak by unikol, v Anthropic Console ho zmažeš a vytvoríš nový.

## Ako to funguje vo vnútri (krok za krokom)

1. **Prepis reči:** `app.js` používa vstavané Web Speech API prehliadača (`SpeechRecognition`) s jazykom `sk-SK`. Priebežné (ešte neisté) výsledky sa zobrazujú hneď, finálne vety sa pripájajú k textu. Keď Chrome po chvíli ticha nahrávanie sám ukončí, appka ho automaticky znova spustí, kým nestlačíš **Zastaviť**.
2. **Návrh skóre:** po kliknutí appka načíta oficiálnu knižnicu Anthropic SDK a pošle Claudovi (model `claude-opus-5-5`) tvoj nápad aj tvoje hodnotenie. Claude vráti odpoveď v pevnom formáte (skóre 1–10 + odôvodnenie pre každú kategóriu + krátke zhrnutie) a appka podľa nej nastaví posuvníky.
3. **Ukladanie:** uložené nápady sú v `localStorage` prehliadača – teda len na tvojom počítači a v tom istom prehliadači.

## Časté problémy

| Problém | Riešenie |
|---|---|
| „Tento prehliadač nepodporuje rozpoznávanie reči“ | Otvor appku v Chrome alebo Edge. |
| „Prístup k mikrofónu bol zamietnutý“ | Klikni na ikonu vľavo od adresy → Mikrofón → Povoliť, potom obnov stránku. |
| „Neplatný API kľúč“ | Skontroluj, či si skopíroval celý kľúč bez medzier. |
| „Na účte nie je kredit“ | Dobi kredit v Anthropic Console → Billing. |

---

# 🚛 Drivee (`kilometrovnik/`)

Samostatná appka pre dopravcov: vypočíta, koľko stojí **1 km jazdy konkrétneho auta**, a podľa toho ukáže, či sa ponuka (napr. z burzy prepráv) oplatí. Spustíš ju dvojklikom na `kilometrovnik/index.html` (funguje v akomkoľvek prehliadači, netreba internet ani API kľúč; bez internetu sa len použije náhradné písmo).

## Tri záložky

1. **Náklady vozidla** – zadáš fixné náklady (leasing, poistenie, vodič, réžia, dane…), variabilné (nafta, AdBlue, pneumatiky, servis) a prevádzku (km a dni za mesiac, diéty, cieľový zisk). Appka ukáže:
   - **náklad na 1 km**, minimálnu a odporúčanú cenu za km,
   - z čoho sa kilometer skladá (zoradené od najväčšej položky),
   - graf, ako klesá náklad na km s vyšším mesačným nájazdom,
   - tipy, kde ušetriť, a porovnanie všetkých áut (najlacnejšie zvýraznené).
2. **Ocenenie jazdy** – zadáš ponuku: km s nákladom, km naprázdno, mýto, iné náklady a cenu (spolu alebo €/km). Appka vypočíta náklady jazdy, zisk, zisk za deň a dá verdikt **Oplatí sa / Hraničné / Neoplatí sa** + minimálnu a odporúčanú cenu.
   Prepínačom **Prázdna jazda / čakanie** zapíšeš aj presun bez nákladu (pristavenie, návrat domov, presun medzi zákazkami, cesta na servis): km, mýto, dátum, auto a voliteľne firmu, kvôli ktorej si išiel naprázdno. Appka ukáže, koľko jazda stála a koľko km s nákladom treba odjazdiť na jej pokrytie.
   Dôvod **Čakanie na nakládku / vykládku / na colnici** zapíše státie v hodinách (fixné náklady auta a diéty za ten čas) a voliteľne **zdržné** vyúčtované zákazníkovi. Pri colnici sa do poplatkov zadáva colná deklarácia, špeditér a parkovanie. Appka ukáže náklad za hodinu a odporúčané zdržné za deň.
3. **Jazdy a ponuky** – súhrn km s nákladom a naprázdno (aj % a náklady na prázdne km), hodiny a náklady čakania a uložené ponuky zoradené podľa **zisku za deň**, aby si vybral tú najlepšiu. Jazdy, ktoré si naozaj odviezol, označíš ako **Zrealizovaná**.
4. **Firmy** – grafické vyhodnotenie zákazníkov (firmu zadáš pri ocenení jazdy):
   - kartičky **Najviac sa oplatí / Najmenej sa oplatí / Najväčší zákazník**,
   - stĺpcový graf firiem od najvýhodnejšej po najmenej výhodnú (zelená = zisk, červená = strata), dá sa prepnúť medzi **zisk za deň, marža %, zisk spolu a tržba €/km**, aj na **len zrealizované jazdy**,
   - tabuľka so súčtami za každú firmu (jazdy, km, tržba, náklady, zisk, marža, priemerná splatnosť faktúr) a hodnotenie **Výhodná / Slabá marža / Stratová**,
   - tlačidlo **Načítať ukážkové jazdy**, ak si chceš vyhodnotenie najprv pozrieť na príklade.
5. **Financie a Power BI** – prehľad tržieb, zisku, neuhradených faktúr a faktúr po splatnosti (jazdy označuješ ako *Zrealizovaná* a *Zaplatená*, pri jazde zadáš dátum a splatnosť) a **export troch CSV súborov** (`jazdy.csv`, `firmy.csv`, `vozidla.csv`) pre Power BI.

6. **Nákladové faktúry** – faktúry nahráš zo súboru z účtovníctva alebo banky (CSV, Excel), vložíš skopírované riadky z Excelu alebo zadáš ručne. Appka ich **sama zaradí do skupiny nákladov** (nafta, AdBlue, mýto, pneumatiky, servis, leasing, poistenie, mzdy, diéty, dane a známky, réžia, ostatné):
   - najprv podľa **zapamätaného dodávateľa** (keď faktúru zaradíš ručne, ďalšie od toho istého dodávateľa sa zaradia rovnako),
   - potom podľa **slov v dodávateľovi a popise** (napr. „nafta“, „Shell“, „mýto“, „leasing“, „poisťovňa“, „oprava“),
   - k **vozidlu** podľa ŠPZ v popise (ŠPZ daj do názvu vozidla, napr. „Ťahač ZA123AB“).

   **PDF faktúry:** vyber jedno alebo viac PDF. Appka z nich prečíta text a nájde dodávateľa, číslo faktúry, dátum dodania, sumu bez DPH, celkovú sumu, položky a ŠPZ. Faktúru zaradí ako pri ostatných faktúrach a ukáže ju na **kontrolu pred uložením**. Ak suma bez DPH na faktúre nie je, dopočíta ju z celkovej sumy ÷ 1,23 a upozorní na to. Na otvorenie PDF treba internet (čítačka pdf.js sa načíta pri prvom PDF). Na odkaze claude.ai je navyše tlačidlo **Prečítať pomocou Claude** pre neprehľadné alebo naskenované faktúry. Na skúšku je v repozitári `kilometrovnik/ukazkova-faktura.pdf`.

   Potom porovná **skutočné náklady s plánom** z nastavení vozidla po skupinách a mesiacoch a ukáže, kde míňaš viac, než si počítal. Zo súboru berie sumu **bez DPH** (stĺpec „Základ“ / „bez DPH“, ak existuje).

### Power BI (`kilometrovnik/powerbi/`)

Hotové dotazy Power Query (`dotazy-power-query.m`), miery DAX (`miery.dax`: tržby, zisk, marža, zisk na deň, pohľadávky, cash flow podľa splatnosti, náklady na státie, odhad hospodárskeho výsledku, poradie firiem), miery pre faktúry (skutočné náklady vs. plán, odchýlka, výsledok podľa faktúr), ukážkové dáta a návod krok za krokom v [`kilometrovnik/powerbi/NAVOD.md`](kilometrovnik/powerbi/NAVOD.md).

## Ako počíta

- **Variabilné €/km** = nafta (spotreba × cena) + AdBlue + pneumatiky (cena sady ÷ životnosť) + servis.
- **Fixné €/km** = (mesačné fixné náklady + diéty × dni) ÷ km za mesiac.
- **Náklady jazdy** = variabilné €/km × všetky km (aj prázdne) + fixné náklady za deň × počet dní + diéty × dni + mýto + iné.
  Fixné náklady sa do jazdy počítajú **podľa dní**, lebo leasing, poistenie aj mzda bežia aj keď auto stojí alebo čaká. Počet dní sa dopočíta z priemerných km za deň, alebo ho zadáš ručne.
- **Odporúčaná cena** = náklady × (1 + cieľový zisk %).

Všetky sumy zadávaj **bez DPH**. Dáta sa ukladajú iba v tvojom prehliadači (`localStorage`).
