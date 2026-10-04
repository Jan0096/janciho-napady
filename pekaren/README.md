# 🥖 Pekáreň – suroviny, faktúry, náklady a finančná analýza

Aplikácia v Pythone pre pekárov. Eviduje príjem surovín a faktúry za suroviny, všetky náklady prevádzky
(nájom, energie, mzdy, leasingy strojov, pohyblivé náklady…) a tržby. Výsledkom je **finančná analýza
prevádzky** s výkazom ziskov a strát, bodom zvratu a upozorneniami.

Netreba nič inštalovať okrem Pythonu 3.10+ – aplikácia používa len štandardnú knižnicu a dáta ukladá
do jedného súboru `pekaren.db` (SQLite).

## Webová verzia (bez inštalácie)

Aplikácia je dostupná aj ako webová stránka: <https://claude.ai/artifact/QPMkbt8xKiMfnLPTDbLXwH>
(otvorte ju prihlásený na claude.ai, údaje sa ukladajú automaticky). Má rovnaké funkcie a výpočty
ako verzia v Pythone. Zdrojový kód je v `web/pekaren.html`.

## Spustenie verzie v Pythone

V priečinku `pekaren` spusti:

```bash
python -m pekaren
```

Otvorí sa menu:

```
========== 🥖 PEKÁREŇ – evidencia a financie ==========
  1) Príjem surovín (príjemka)
  2) Nová faktúra za suroviny
  3) Úhrada faktúry
  4) Spotreba suroviny
  5) Pravidelný náklad (nájom, mzdy, ...)
  6) Leasing stroja
  7) Jednorazový náklad (energie, opravy, obaly, ...)
  8) Tržba
  9) Stav skladu
 10) Prehľad faktúr
 11) Prehľad pravidelných nákladov
 12) 📊 FINANČNÁ ANALÝZA – zisk a strata
  0) Koniec
```

### Vyskúšanie s ukážkovými dátami

```bash
python -m pekaren --db ukazka.db demo
python -m pekaren --db ukazka.db report --od 2026-01 --do 2026-06 --html report.html
```

Druhý príkaz vypíše analýzu za 1.–6. 2026 a uloží ju aj ako `report.html` – otvor ho v prehliadači.

## Čo aplikácia vie

| Oblasť | Funkcie |
|---|---|
| **Príjem surovín** | príjemka s položkami (surovina, množstvo, cena bez DPH, sadzba DPH), dodávatelia, stav skladu, upozornenie pod minimálnou zásobou |
| **Faktúry za suroviny** | evidencia, splatnosť, úhrady, faktúry po splatnosti, **kontrola faktúry voči príjemkám** (dodávateľ vyfakturoval viac, než prišlo) |
| **Náklady prevádzky** | pravidelné mesačné (nájom, mzdy, paušály), leasingy strojov na počet splátok, jednorazové (energie, opravy, obaly, doprava); každý náklad je fixný alebo variabilný |
| **Tržby** | denné tržby podľa kanála (predajňa, veľkoodber, rozvoz…) |
| **Finančná analýza** | výkaz ziskov a strát, hrubá marža, zisk/strata, marža zisku, food cost, podiel miezd, bod zvratu, bezpečnostná rezerva, vývoj po mesiacoch, vývoj nákupných cien surovín, záväzky, zostatok leasingov |

### Ako sa počíta

- **Náklady na suroviny** = hodnota prijatých surovín (príjemky) v období, bez DPH.
- **Hrubá marža** = tržby − suroviny.
- **Zisk / strata** = tržby − suroviny − prevádzkové náklady (pred daňou z príjmu a odpismi).
- **Pravidelné náklady** sa započítajú za každý mesiac, v ktorom platia; ak začnú alebo skončia
  v priebehu mesiaca, krátia sa pomerne podľa dní.
- **Bod zvratu** = fixné náklady / (1 − variabilné náklady ÷ tržby) – tržby, pri ktorých je zisk nulový.
- **Bezpečnostná rezerva** – o koľko % môžu klesnúť tržby, kým sa prevádzka dostane do straty.
- **Upozornenia**: strata, suroviny nad 35 % tržieb, mzdy nad 35 %, nájom nad 12 %
  (hranice sa dajú zmeniť na začiatku `pekaren/analyza.py`).

Všetky sumy sa zadávajú **bez DPH** (pri faktúre sa DPH zadáva zvlášť kvôli prehľadu záväzkov).

## Súbory

| Súbor | Na čo slúži |
|---|---|
| `pekaren/db.py` | databáza (tabuľky) |
| `pekaren/evidencia.py` | zadávanie surovín, faktúr, nákladov, tržieb |
| `pekaren/analyza.py` | výpočty – zisk, strata, ukazovatele |
| `pekaren/report.py` | textový a HTML report |
| `pekaren/cli.py` | menu a príkazy |
| `pekaren/demo.py` | ukážkové dáta |
| `web/pekaren.html` | webová verzia (beží v prehliadači) |
| `tests/` | testy (`python -m unittest discover -s tests`) |
