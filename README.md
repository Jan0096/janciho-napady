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

## 🥖 Ďalšia aplikácia: Pekáreň

V priečinku [`pekaren/`](pekaren/) je aplikácia v Pythone pre pekárov – príjem surovín, faktúry, náklady prevádzky a finančná analýza (zisk/strata). Návod je v [`pekaren/README.md`](pekaren/README.md).
