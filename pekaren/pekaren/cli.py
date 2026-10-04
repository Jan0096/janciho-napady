"""Ovládanie aplikácie – interaktívne menu a príkazy z príkazového riadka."""

import argparse
import sqlite3
import sys
import webbrowser
from datetime import date
from pathlib import Path

from . import evidencia as ev
from .analyza import _koniec_mesiaca
from .db import pripoj
from .demo import napln_demo
from .report import eur, report_html, report_text, zostav_report

# ------------------------------------------------------------ vstupy


def _vstup(otazka: str, predvolene: str | None = None) -> str:
    text = input(f"{otazka}{f' [{predvolene}]' if predvolene else ''}: ").strip()
    return text or (predvolene or "")


def _cislo(otazka: str, predvolene: float | None = None) -> float:
    while True:
        text = _vstup(otazka, None if predvolene is None else str(predvolene))
        try:
            return float(text.replace(",", ".").replace(" ", ""))
        except ValueError:
            print("  Zadaj číslo, napr. 12,50")


def _datum(otazka: str, predvolene: str | None = None) -> str:
    while True:
        text = _vstup(otazka + " (RRRR-MM-DD)", predvolene)
        try:
            return ev.over_datum(text)
        except ev.ChybaEvidencie as e:
            print(f"  {e}")


def _ano(otazka: str) -> bool:
    return _vstup(otazka + " (a/n)", "n").lower().startswith("a")


def _vyber(otazka: str, moznosti: list[tuple[str, str]]) -> str:
    """Vyber z očíslovaného zoznamu; vracia kľúč možnosti."""
    for i, (_, popis) in enumerate(moznosti, 1):
        print(f"  {i}) {popis}")
    while True:
        text = _vstup(otazka)
        if text.isdigit() and 1 <= int(text) <= len(moznosti):
            return moznosti[int(text) - 1][0]
        print("  Neplatná voľba.")


def _mesiac(text: str) -> tuple[int, int]:
    rok, mes = text.split("-")
    return int(rok), int(mes)


def _vyber_dodavatela(conn: sqlite3.Connection) -> int:
    dodavatelia = ev.zoznam_dodavatelov(conn)
    moznosti = [(str(d["id"]), d["nazov"]) for d in dodavatelia] + [("novy", "+ nový dodávateľ")]
    volba = _vyber("Dodávateľ", moznosti)
    if volba == "novy":
        return ev.pridaj_dodavatela(conn, _vstup("Názov dodávateľa"), _vstup("IČO", ""))
    return int(volba)


def _vyber_surovinu(conn: sqlite3.Connection) -> int:
    suroviny = ev.zoznam_surovin(conn)
    moznosti = [(str(s["id"]), f"{s['nazov']} ({s['jednotka']})") for s in suroviny]
    moznosti.append(("nova", "+ nová surovina"))
    volba = _vyber("Surovina", moznosti)
    if volba == "nova":
        return ev.pridaj_surovinu(
            conn, _vstup("Názov suroviny"), _vstup("Jednotka (kg, l, ks)", "kg"), _cislo("Minimálna zásoba", 0)
        )
    return int(volba)


def _vyber_kategoriu() -> tuple[str, str]:
    kat = _vyber("Kategória", [(k, v[0]) for k, v in ev.KATEGORIE.items()])
    predvoleny = ev.KATEGORIE[kat][1]
    typ = _vyber(
        f"Typ nákladu (predvolene {'fixný' if predvoleny == 'fixny' else 'variabilný'})",
        [("fixny", "fixný – nemení sa s objemom výroby"), ("variabilny", "variabilný – rastie s výrobou")],
    )
    return kat, typ


# ------------------------------------------------------------ akcie menu


def akcia_prijem(conn: sqlite3.Connection) -> None:
    print("\n--- Príjem surovín (príjemka) ---")
    datum = _datum("Dátum príjmu", date.today().isoformat())
    dodavatel_id = _vyber_dodavatela(conn)
    polozky = []
    while True:
        surovina_id = _vyber_surovinu(conn)
        mnozstvo = _cislo("Množstvo")
        cena = _cislo("Cena za jednotku bez DPH (€)")
        dph = _cislo("Sadzba DPH %", 20)
        polozky.append(ev.Polozka(surovina_id, mnozstvo, cena, dph))
        print(f"  + položka {mnozstvo} × {eur(cena)} = {eur(mnozstvo * cena)}")
        if not _ano("Pridať ďalšiu položku?"):
            break
    faktura_id = None
    if _ano("Je k dodávke faktúra?"):
        faktura_id = _zadaj_fakturu(conn, dodavatel_id, sum(p.mnozstvo * p.jednotkova_cena for p in polozky),
                                    sum(p.mnozstvo * p.jednotkova_cena * p.sadzba_dph / 100 for p in polozky))
    pid = ev.prijmi_suroviny(conn, datum, dodavatel_id, polozky, faktura_id, _vstup("Poznámka", ""))
    print(f"✔ Príjemka č. {pid} uložená.")


def _zadaj_fakturu(conn: sqlite3.Connection, dodavatel_id: int, navrh_suma: float | None = None,
                   navrh_dph: float | None = None) -> int:
    cislo = _vstup("Číslo faktúry")
    vyst = _datum("Dátum vystavenia", date.today().isoformat())
    spl = _datum("Dátum splatnosti", vyst)
    suma = _cislo("Suma bez DPH (€)", None if navrh_suma is None else round(navrh_suma, 2))
    dph = _cislo("DPH (€)", None if navrh_dph is None else round(navrh_dph, 2))
    fid = ev.pridaj_fakturu(conn, cislo, dodavatel_id, vyst, spl, suma, dph)
    print(f"✔ Faktúra {cislo} uložená.")
    return fid


def akcia_faktura(conn: sqlite3.Connection) -> None:
    print("\n--- Nová faktúra za suroviny ---")
    dodavatel_id = _vyber_dodavatela(conn)
    fid = _zadaj_fakturu(conn, dodavatel_id)
    nepriradene = [
        p for p in ev.zoznam_prijemok(conn, 200) if p["faktura"] is None
        and conn.execute("SELECT dodavatel_id FROM prijem WHERE id=?", (p["id"],)).fetchone()[0] == dodavatel_id
    ]
    if nepriradene and _ano("Priradiť k faktúre nevyfakturované príjemky tohto dodávateľa?"):
        for p in nepriradene:
            if _ano(f"  Príjemka č. {p['id']} z {p['datum']} na {eur(p['suma_bez_dph'])}?"):
                ev.priradit_fakturu(conn, p["id"], fid)


def akcia_uhrada(conn: sqlite3.Connection) -> None:
    faktury = ev.zoznam_faktur(conn, len_neuhradene=True)
    if not faktury:
        print("Žiadne neuhradené faktúry. 👍")
        return
    moznosti = [
        (str(f["id"]), f"{f['cislo']} – {f['dodavatel']} – {eur(f['suma_bez_dph'] + f['dph'])} "
                       f"(splatná {f['datum_splatnosti']})")
        for f in faktury
    ]
    fid = int(_vyber("Ktorú faktúru si uhradil?", moznosti))
    ev.uhrad_fakturu(conn, fid, _datum("Dátum úhrady", date.today().isoformat()))
    print("✔ Označená ako uhradená.")


def akcia_spotreba(conn: sqlite3.Connection) -> None:
    print("\n--- Spotreba suroviny vo výrobe ---")
    surovina_id = _vyber_surovinu(conn)
    ev.zapis_spotrebu(conn, _datum("Dátum", date.today().isoformat()), surovina_id, _cislo("Množstvo"))
    print("✔ Zapísané.")


def akcia_pravidelny(conn: sqlite3.Connection) -> None:
    print("\n--- Pravidelný mesačný náklad (nájom, mzdy, paušály...) ---")
    nazov = _vstup("Názov")
    kat, typ = _vyber_kategoriu()
    suma = _cislo("Mesačná suma (€)")
    od = _datum("Platí od", date.today().replace(day=1).isoformat())
    do = _vstup("Platí do (RRRR-MM-DD, prázdne = neurčito)", "") or None
    ev.pridaj_pravidelny_naklad(conn, nazov, kat, suma, od, do, typ)
    print("✔ Uložené.")


def akcia_leasing(conn: sqlite3.Connection) -> None:
    print("\n--- Leasing stroja ---")
    ev.pridaj_leasing(
        conn,
        _vstup("Stroj (napr. Etážová pec)"),
        _cislo("Mesačná splátka (€)"),
        _datum("Prvá splátka", date.today().replace(day=1).isoformat()),
        int(_cislo("Počet splátok (mesiacov)", 48)),
    )
    print("✔ Leasing uložený.")


def akcia_naklad(conn: sqlite3.Connection) -> None:
    print("\n--- Jednorazový náklad (faktúra za energie, oprava, obaly...) ---")
    datum = _datum("Dátum", date.today().isoformat())
    nazov = _vstup("Popis")
    kat, typ = _vyber_kategoriu()
    ev.pridaj_naklad(conn, datum, nazov, kat, _cislo("Suma bez DPH (€)"), typ)
    print("✔ Uložené.")


def akcia_trzba(conn: sqlite3.Connection) -> None:
    print("\n--- Tržba ---")
    datum = _datum("Dátum", date.today().isoformat())
    kanal = _vyber("Kanál", [(k, k) for k in ev.KANALY_TRZIEB])
    ev.pridaj_trzbu(conn, datum, _cislo("Tržba bez DPH (€)"), kanal)
    print("✔ Uložené.")


def akcia_sklad(conn: sqlite3.Connection) -> None:
    print(f"\n{'Surovina':<24}{'Zásoba':>12}  {'Priem. cena':>12}")
    for s in ev.stav_skladu(conn):
        varovanie = "  ⚠ pod minimom" if s["min_zasoba"] and s["zasoba"] < s["min_zasoba"] else ""
        print(f"{s['nazov']:<24}{s['zasoba']:>9.1f} {s['jednotka']:<3}  {eur(s['priemerna_cena']):>12}{varovanie}")


def akcia_faktury(conn: sqlite3.Connection) -> None:
    print(f"\n{'Číslo':<16}{'Dodávateľ':<26}{'Splatnosť':<12}{'S DPH':>12}  Stav")
    dnes = date.today().isoformat()
    for f in ev.zoznam_faktur(conn):
        if f["datum_uhrady"]:
            stav = f"uhradená {f['datum_uhrady']}"
        else:
            stav = "PO SPLATNOSTI" if f["datum_splatnosti"] < dnes else "neuhradená"
        print(f"{f['cislo']:<16}{f['dodavatel'][:25]:<26}{f['datum_splatnosti']:<12}"
              f"{eur(f['suma_bez_dph'] + f['dph']):>12}  {stav}")


def akcia_naklady(conn: sqlite3.Connection) -> None:
    print(f"\n{'ID':>3} {'Názov':<44}{'Kategória':<12}{'Mesačne':>12}  Platnosť")
    for n in ev.zoznam_pravidelnych_nakladov(conn):
        print(f"{n['id']:>3} {n['nazov'][:43]:<44}{n['kategoria']:<12}{eur(n['mesacna_suma']):>12}  "
              f"{n['platny_od']} – {n['platny_do'] or '...'}")
    if _ano("Ukončiť niektorý pravidelný náklad?"):
        ev.ukonci_pravidelny_naklad(conn, int(_cislo("ID nákladu")), _datum("Posledný deň platnosti"))
        print("✔ Ukončené.")


def akcia_analyza(conn: sqlite3.Connection) -> None:
    print("\n--- Finančná analýza ---")
    dnes = date.today()
    od = _vstup("Od mesiaca (RRRR-MM)", f"{dnes.year}-01")
    do = _vstup("Do mesiaca (RRRR-MM)", f"{dnes.year}-{dnes.month:02d}")
    try:
        od_d = date(*_mesiac(od), 1)
        do_d = _koniec_mesiaca(*_mesiac(do))
    except ValueError:
        print("Neplatný mesiac.")
        return
    r = zostav_report(conn, od_d, do_d)
    print()
    print(report_text(r))
    if _ano("\nUložiť report ako HTML a otvoriť v prehliadači?"):
        subor = Path(f"report_{od}_{do}.html").resolve()
        subor.write_text(report_html(r), encoding="utf-8")
        print(f"✔ Uložené do {subor}")
        webbrowser.open(subor.as_uri())


MENU = [
    ("Príjem surovín (príjemka)", akcia_prijem),
    ("Nová faktúra za suroviny", akcia_faktura),
    ("Úhrada faktúry", akcia_uhrada),
    ("Spotreba suroviny", akcia_spotreba),
    ("Pravidelný náklad (nájom, mzdy, ...)", akcia_pravidelny),
    ("Leasing stroja", akcia_leasing),
    ("Jednorazový náklad (energie, opravy, obaly, ...)", akcia_naklad),
    ("Tržba", akcia_trzba),
    ("Stav skladu", akcia_sklad),
    ("Prehľad faktúr", akcia_faktury),
    ("Prehľad pravidelných nákladov", akcia_naklady),
    ("📊 FINANČNÁ ANALÝZA – zisk a strata", akcia_analyza),
]


def interaktivne(conn: sqlite3.Connection) -> None:
    while True:
        print("\n========== 🥖 PEKÁREŇ – evidencia a financie ==========")
        for i, (nazov, _) in enumerate(MENU, 1):
            print(f" {i:>2}) {nazov}")
        print("  0) Koniec")
        volba = input("Vyber: ").strip()
        if volba == "0":
            return
        if not volba.isdigit() or not 1 <= int(volba) <= len(MENU):
            print("Neplatná voľba.")
            continue
        try:
            MENU[int(volba) - 1][1](conn)
        except ev.ChybaEvidencie as e:
            print(f"✘ {e}")
        except (KeyboardInterrupt, EOFError):
            print("\n(zrušené)")


# ------------------------------------------------------- príkazový riadok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pekaren", description="Evidencia surovín, faktúr a nákladov pekárne.")
    parser.add_argument("--db", default="pekaren.db", help="súbor s databázou (predvolene pekaren.db)")
    sub = parser.add_subparsers(dest="prikaz")
    sub.add_parser("menu", help="interaktívne menu (predvolené)")
    demo = sub.add_parser("demo", help="naplní databázu ukážkovými dátami (1–6/2026)")
    demo.add_argument("--prepisat", action="store_true", help="zmaže existujúcu databázu")
    rep = sub.add_parser("report", help="finančná analýza za obdobie")
    rep.add_argument("--od", required=True, help="prvý mesiac RRRR-MM")
    rep.add_argument("--do", required=True, help="posledný mesiac RRRR-MM")
    rep.add_argument("--html", help="uloží report aj do HTML súboru")
    rep.add_argument("--k-datumu", help="dátum pre stav faktúr a leasingov (RRRR-MM-DD, predvolene dnes)")
    args = parser.parse_args(argv)

    if args.prikaz == "demo":
        cesta = Path(args.db)
        if cesta.exists():
            if not args.prepisat:
                print(f"Databáza {cesta} už existuje. Použi --prepisat alebo iný --db.", file=sys.stderr)
                return 1
            cesta.unlink()
        napln_demo(pripoj(str(cesta)))
        print(f"✔ Ukážkové dáta uložené do {cesta}. Skús: python -m pekaren --db {cesta} report --od 2026-01 --do 2026-06")
        return 0

    conn = pripoj(args.db)
    if args.prikaz == "report":
        try:
            od = date(*_mesiac(args.od), 1)
            do = _koniec_mesiaca(*_mesiac(args.do))
            k_datumu = date.fromisoformat(args.k_datumu) if args.k_datumu else None
        except ValueError:
            print("Neplatný dátum – mesiace zadaj ako RRRR-MM, dátum ako RRRR-MM-DD.", file=sys.stderr)
            return 1
        r = zostav_report(conn, od, do, k_datumu)
        print(report_text(r))
        if args.html:
            Path(args.html).write_text(report_html(r), encoding="utf-8")
            print(f"\n✔ HTML report uložený do {args.html}")
        return 0

    try:
        interaktivne(conn)
    except (KeyboardInterrupt, EOFError):
        print()
    return 0
