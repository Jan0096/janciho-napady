"""Ukážkové dáta – malá pekáreň, január až jún 2026."""

import random
import sqlite3
from datetime import date, timedelta

from . import evidencia as ev

SUROVINY = [
    # názov, jednotka, min. zásoba, cena v januári, mesačný rast ceny, spotreba za týždeň
    ("Pšeničná múka T650", "kg", 300, 0.42, 0.010, 900),
    ("Ražná múka", "kg", 80, 0.55, 0.005, 200),
    ("Droždie", "kg", 10, 2.10, 0.000, 25),
    ("Maslo", "kg", 20, 7.80, 0.025, 40),
    ("Cukor", "kg", 40, 0.85, -0.005, 90),
    ("Soľ", "kg", 15, 0.30, 0.000, 20),
    ("Vajcia", "ks", 300, 0.22, 0.015, 900),
    ("Mlieko", "l", 30, 0.95, 0.000, 80),
    ("Slnečnicové semienka", "kg", 10, 2.40, 0.000, 15),
]

DODAVATELIA = [
    ("Mlyn Pohronie s.r.o.", "36123456", ["Pšeničná múka T650", "Ražná múka"]),
    ("Gastro Veľkoobchod a.s.", "35987654", ["Droždie", "Cukor", "Soľ", "Slnečnicové semienka"]),
    ("Farma Zelená Lúka", "47111222", ["Maslo", "Vajcia", "Mlieko"]),
]


def napln_demo(conn: sqlite3.Connection, seed: int = 7) -> None:
    rnd = random.Random(seed)
    sur_id = {n: ev.pridaj_surovinu(conn, n, j, m) for n, j, m, *_ in SUROVINY}
    sur_info = {n: (c, r, t) for n, _, _, c, r, t in SUROVINY}
    dod_id = {n: ev.pridaj_dodavatela(conn, n, ico) for n, ico, _ in DODAVATELIA}

    od, do = date(2026, 1, 1), date(2026, 6, 30)

    # Týždenné dodávky surovín, mesačne fakturované každým dodávateľom.
    for mesiac in range(1, 7):
        for dodavatel, _, suroviny in DODAVATELIA:
            prijemky, suma = [], 0.0
            den = date(2026, mesiac, 1)
            while den.month == mesiac:
                polozky = []
                for n in suroviny:
                    cena0, rast, tyzden = sur_info[n]
                    cena = round(cena0 * (1 + rast) ** (mesiac - 1), 4)
                    mnozstvo = round(tyzden * rnd.uniform(0.9, 1.1), 1)
                    polozky.append(ev.Polozka(sur_id[n], mnozstvo, cena))
                    suma += mnozstvo * cena
                prijemky.append(ev.prijmi_suroviny(conn, den.isoformat(), dod_id[dodavatel], polozky))
                den += timedelta(days=7)
            vystavena = date(2026, mesiac, 28)
            # V júni dodávateľ vyfakturoval viac, než sa reálne prijalo – ukážka kontroly.
            if mesiac == 6 and dodavatel.startswith("Farma"):
                suma += 35.40
            fid = ev.pridaj_fakturu(
                conn,
                f"FA{mesiac:02d}{dod_id[dodavatel]:02d}/2026",
                dod_id[dodavatel],
                vystavena.isoformat(),
                (vystavena + timedelta(days=14)).isoformat(),
                round(suma, 2),
                round(suma * 0.2, 2),
            )
            for p in prijemky:
                ev.priradit_fakturu(conn, p, fid)
            if mesiac < 6:
                ev.uhrad_fakturu(conn, fid, (vystavena + timedelta(days=12)).isoformat())

    # Spotreba surovín (pre stav skladu).
    for n, (_, _, tyzden) in sur_info.items():
        ev.zapis_spotrebu(conn, "2026-06-30", sur_id[n], round(tyzden * 25.5, 1), "spotreba 1–6/2026")

    # Denné tržby (nedeľa zatvorené), v lete mierny pokles.
    den = od
    while den <= do:
        if den.weekday() != 6:
            sezona = 1.0 - 0.08 * (den.month >= 5)
            vikend = 1.3 if den.weekday() == 5 else 1.0
            ev.pridaj_trzbu(conn, den.isoformat(), round(rnd.uniform(780, 920) * sezona * vikend, 2))
            if den.weekday() in (0, 3):
                ev.pridaj_trzbu(conn, den.isoformat(), round(rnd.uniform(380, 450), 2), "veľkoodber")
        den += timedelta(days=1)

    # Pravidelné náklady.
    ev.pridaj_pravidelny_naklad(conn, "Nájom prevádzky", "najom", 1800, "2026-01-01")
    ev.pridaj_pravidelny_naklad(conn, "Mzdy – 3 pekári + predavačka (vrátane odvodov)", "mzdy", 9200, "2026-01-01")
    ev.pridaj_pravidelny_naklad(conn, "Účtovníctvo", "ostatne", 180, "2026-01-01")
    ev.pridaj_pravidelny_naklad(conn, "Poistenie prevádzky", "ostatne", 65, "2026-01-01")
    ev.pridaj_leasing(conn, "Etážová pec", 690, "2025-03-01", 48)
    ev.pridaj_leasing(conn, "Špirálový miesič", 210, "2026-02-01", 24)

    # Jednorazové a pohyblivé náklady.
    for mesiac in range(1, 7):
        kurenie = 1 - 0.1 * (mesiac - 1)
        ev.pridaj_naklad(conn, f"2026-{mesiac:02d}-15", "Elektrina", "energie", round(1250 * rnd.uniform(0.95, 1.05), 2))
        ev.pridaj_naklad(conn, f"2026-{mesiac:02d}-15", "Plyn", "energie", round(620 * kurenie, 2))
        ev.pridaj_naklad(conn, f"2026-{mesiac:02d}-15", "Voda", "energie", 95)
        ev.pridaj_naklad(conn, f"2026-{mesiac:02d}-20", "Obaly a vrecká", "pohyblive", round(rnd.uniform(380, 450), 2))
        ev.pridaj_naklad(conn, f"2026-{mesiac:02d}-25", "Palivo – rozvoz", "pohyblive", round(rnd.uniform(220, 280), 2))
    ev.pridaj_naklad(conn, "2026-03-11", "Oprava chladiaceho boxu", "udrzba", 640)
