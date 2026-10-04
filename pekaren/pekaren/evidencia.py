"""Evidencia: dodávatelia, suroviny, príjemky, faktúry, náklady a tržby."""

import sqlite3
from dataclasses import dataclass
from datetime import date

# Kategórie prevádzkových nákladov a ich predvolený typ (fixný / variabilný).
KATEGORIE = {
    "najom": ("Nájom", "fixny"),
    "energie": ("Energie (elektrina, plyn, voda)", "variabilny"),
    "mzdy": ("Mzdy a odvody", "fixny"),
    "leasing": ("Leasing strojov", "fixny"),
    "pohyblive": ("Pohyblivé náklady (obaly, doprava, ...)", "variabilny"),
    "udrzba": ("Údržba a opravy", "fixny"),
    "ostatne": ("Ostatné", "fixny"),
}

KANALY_TRZIEB = ("predajňa", "veľkoodber", "rozvoz", "iné")


class ChybaEvidencie(ValueError):
    """Chyba vo vstupných údajoch."""


def over_datum(text: str) -> str:
    """Overí dátum vo formáte RRRR-MM-DD a vráti ho."""
    try:
        return date.fromisoformat(text).isoformat()
    except (TypeError, ValueError):
        raise ChybaEvidencie(f"Neplatný dátum '{text}', použi formát RRRR-MM-DD.") from None


def _over_kategoriu(kategoria: str, typ: str | None) -> str:
    if kategoria not in KATEGORIE:
        raise ChybaEvidencie(
            f"Neznáma kategória '{kategoria}'. Možnosti: {', '.join(KATEGORIE)}"
        )
    typ = typ or KATEGORIE[kategoria][1]
    if typ not in ("fixny", "variabilny"):
        raise ChybaEvidencie("Typ nákladu musí byť 'fixny' alebo 'variabilny'.")
    return typ


def pridaj_mesiace(d: date, mesiace: int) -> date:
    """Posunie dátum o daný počet mesiacov (deň sa skráti na koniec mesiaca)."""
    m = d.month - 1 + mesiace
    rok, mesiac = d.year + m // 12, m % 12 + 1
    for den in (d.day, 30, 29, 28):
        try:
            return date(rok, mesiac, den)
        except ValueError:
            continue
    raise AssertionError("nedosiahnuteľné")


# ---------------------------------------------------------------- dodávatelia


def pridaj_dodavatela(conn: sqlite3.Connection, nazov: str, ico: str = "", kontakt: str = "") -> int:
    nazov = nazov.strip()
    if not nazov:
        raise ChybaEvidencie("Názov dodávateľa nesmie byť prázdny.")
    try:
        cur = conn.execute(
            "INSERT INTO dodavatel (nazov, ico, kontakt) VALUES (?, ?, ?)",
            (nazov, ico.strip(), kontakt.strip()),
        )
    except sqlite3.IntegrityError:
        raise ChybaEvidencie(f"Dodávateľ '{nazov}' už existuje.") from None
    conn.commit()
    return cur.lastrowid


def zoznam_dodavatelov(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM dodavatel ORDER BY nazov").fetchall()


def najdi_dodavatela(conn: sqlite3.Connection, nazov: str) -> int | None:
    row = conn.execute("SELECT id FROM dodavatel WHERE nazov = ?", (nazov.strip(),)).fetchone()
    return row["id"] if row else None


# ------------------------------------------------------------------ suroviny


def pridaj_surovinu(conn: sqlite3.Connection, nazov: str, jednotka: str = "kg", min_zasoba: float = 0) -> int:
    nazov = nazov.strip()
    if not nazov:
        raise ChybaEvidencie("Názov suroviny nesmie byť prázdny.")
    if min_zasoba < 0:
        raise ChybaEvidencie("Minimálna zásoba nemôže byť záporná.")
    try:
        cur = conn.execute(
            "INSERT INTO surovina (nazov, jednotka, min_zasoba) VALUES (?, ?, ?)",
            (nazov, jednotka.strip() or "kg", min_zasoba),
        )
    except sqlite3.IntegrityError:
        raise ChybaEvidencie(f"Surovina '{nazov}' už existuje.") from None
    conn.commit()
    return cur.lastrowid


def zoznam_surovin(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM surovina ORDER BY nazov").fetchall()


def najdi_surovinu(conn: sqlite3.Connection, nazov: str) -> int | None:
    row = conn.execute("SELECT id FROM surovina WHERE nazov = ?", (nazov.strip(),)).fetchone()
    return row["id"] if row else None


# ------------------------------------------------------------------- faktúry


def pridaj_fakturu(
    conn: sqlite3.Connection,
    cislo: str,
    dodavatel_id: int,
    datum_vystavenia: str,
    datum_splatnosti: str,
    suma_bez_dph: float,
    dph: float = 0,
) -> int:
    cislo = cislo.strip()
    if not cislo:
        raise ChybaEvidencie("Číslo faktúry nesmie byť prázdne.")
    if suma_bez_dph < 0 or dph < 0:
        raise ChybaEvidencie("Suma faktúry nemôže byť záporná.")
    vyst, spl = over_datum(datum_vystavenia), over_datum(datum_splatnosti)
    if spl < vyst:
        raise ChybaEvidencie("Dátum splatnosti nemôže byť skôr ako dátum vystavenia.")
    try:
        cur = conn.execute(
            """INSERT INTO faktura (cislo, dodavatel_id, datum_vystavenia, datum_splatnosti,
                                    suma_bez_dph, dph) VALUES (?, ?, ?, ?, ?, ?)""",
            (cislo, dodavatel_id, vyst, spl, suma_bez_dph, dph),
        )
    except sqlite3.IntegrityError:
        raise ChybaEvidencie(f"Faktúra '{cislo}' od tohto dodávateľa už existuje.") from None
    conn.commit()
    return cur.lastrowid


def uhrad_fakturu(conn: sqlite3.Connection, faktura_id: int, datum_uhrady: str) -> None:
    cur = conn.execute(
        "UPDATE faktura SET datum_uhrady = ? WHERE id = ?", (over_datum(datum_uhrady), faktura_id)
    )
    if cur.rowcount == 0:
        raise ChybaEvidencie(f"Faktúra s ID {faktura_id} neexistuje.")
    conn.commit()


def zoznam_faktur(conn: sqlite3.Connection, len_neuhradene: bool = False) -> list[sqlite3.Row]:
    sql = """
        SELECT f.*, d.nazov AS dodavatel,
               COALESCE((SELECT SUM(pp.mnozstvo * pp.jednotkova_cena)
                         FROM prijem p JOIN prijem_polozka pp ON pp.prijem_id = p.id
                         WHERE p.faktura_id = f.id), 0) AS suma_prijemok
        FROM faktura f JOIN dodavatel d ON d.id = f.dodavatel_id
    """
    if len_neuhradene:
        sql += " WHERE f.datum_uhrady IS NULL"
    return conn.execute(sql + " ORDER BY f.datum_splatnosti, f.id").fetchall()


# ------------------------------------------------------------------ príjemky


@dataclass
class Polozka:
    surovina_id: int
    mnozstvo: float
    jednotkova_cena: float  # bez DPH
    sadzba_dph: float = 20.0


def prijmi_suroviny(
    conn: sqlite3.Connection,
    datum: str,
    dodavatel_id: int,
    polozky: list[Polozka],
    faktura_id: int | None = None,
    poznamka: str = "",
) -> int:
    """Zaeviduje príjem surovín na sklad (príjemku), voliteľne naviazaný na faktúru."""
    if not polozky:
        raise ChybaEvidencie("Príjemka musí obsahovať aspoň jednu položku.")
    for p in polozky:
        if p.mnozstvo <= 0:
            raise ChybaEvidencie("Množstvo musí byť väčšie ako 0.")
        if p.jednotkova_cena < 0:
            raise ChybaEvidencie("Cena nemôže byť záporná.")
    datum = over_datum(datum)
    with conn:
        cur = conn.execute(
            "INSERT INTO prijem (datum, dodavatel_id, faktura_id, poznamka) VALUES (?, ?, ?, ?)",
            (datum, dodavatel_id, faktura_id, poznamka),
        )
        prijem_id = cur.lastrowid
        conn.executemany(
            """INSERT INTO prijem_polozka (prijem_id, surovina_id, mnozstvo, jednotkova_cena, sadzba_dph)
               VALUES (?, ?, ?, ?, ?)""",
            [(prijem_id, p.surovina_id, p.mnozstvo, p.jednotkova_cena, p.sadzba_dph) for p in polozky],
        )
    return prijem_id


def priradit_fakturu(conn: sqlite3.Connection, prijem_id: int, faktura_id: int) -> None:
    cur = conn.execute("UPDATE prijem SET faktura_id = ? WHERE id = ?", (faktura_id, prijem_id))
    if cur.rowcount == 0:
        raise ChybaEvidencie(f"Príjemka s ID {prijem_id} neexistuje.")
    conn.commit()


def zoznam_prijemok(conn: sqlite3.Connection, limit: int = 50) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT p.id, p.datum, d.nazov AS dodavatel, f.cislo AS faktura,
                  SUM(pp.mnozstvo * pp.jednotkova_cena) AS suma_bez_dph,
                  COUNT(pp.id) AS pocet_poloziek
           FROM prijem p
           JOIN dodavatel d ON d.id = p.dodavatel_id
           LEFT JOIN faktura f ON f.id = p.faktura_id
           LEFT JOIN prijem_polozka pp ON pp.prijem_id = p.id
           GROUP BY p.id ORDER BY p.datum DESC, p.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()


def zapis_spotrebu(conn: sqlite3.Connection, datum: str, surovina_id: int, mnozstvo: float, poznamka: str = "") -> int:
    if mnozstvo <= 0:
        raise ChybaEvidencie("Množstvo musí byť väčšie ako 0.")
    cur = conn.execute(
        "INSERT INTO spotreba (datum, surovina_id, mnozstvo, poznamka) VALUES (?, ?, ?, ?)",
        (over_datum(datum), surovina_id, mnozstvo, poznamka),
    )
    conn.commit()
    return cur.lastrowid


def stav_skladu(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Aktuálna zásoba = prijaté − spotrebované, s priemernou nákupnou cenou."""
    return conn.execute(
        """SELECT s.id, s.nazov, s.jednotka, s.min_zasoba,
                  COALESCE(pr.mnozstvo, 0) - COALESCE(sp.mnozstvo, 0) AS zasoba,
                  pr.priemerna_cena
           FROM surovina s
           LEFT JOIN (SELECT surovina_id, SUM(mnozstvo) AS mnozstvo,
                             SUM(mnozstvo * jednotkova_cena) / SUM(mnozstvo) AS priemerna_cena
                      FROM prijem_polozka GROUP BY surovina_id) pr ON pr.surovina_id = s.id
           LEFT JOIN (SELECT surovina_id, SUM(mnozstvo) AS mnozstvo
                      FROM spotreba GROUP BY surovina_id) sp ON sp.surovina_id = s.id
           ORDER BY s.nazov"""
    ).fetchall()


# ------------------------------------------------------------------- náklady


def pridaj_pravidelny_naklad(
    conn: sqlite3.Connection,
    nazov: str,
    kategoria: str,
    mesacna_suma: float,
    platny_od: str,
    platny_do: str | None = None,
    typ: str | None = None,
) -> int:
    """Mesačne sa opakujúci náklad (nájom, mzdy, leasing, paušál za energie...)."""
    typ = _over_kategoriu(kategoria, typ)
    if mesacna_suma < 0:
        raise ChybaEvidencie("Suma nemôže byť záporná.")
    od = over_datum(platny_od)
    do = over_datum(platny_do) if platny_do else None
    if do and do < od:
        raise ChybaEvidencie("Koniec platnosti nemôže byť pred začiatkom.")
    cur = conn.execute(
        """INSERT INTO naklad_pravidelny (nazov, kategoria, typ, mesacna_suma, platny_od, platny_do)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (nazov.strip(), kategoria, typ, mesacna_suma, od, do),
    )
    conn.commit()
    return cur.lastrowid


def pridaj_leasing(
    conn: sqlite3.Connection, stroj: str, mesacna_splatka: float, zaciatok: str, pocet_splatok: int
) -> int:
    """Leasing stroja = pravidelný fixný náklad na presný počet mesiacov."""
    if pocet_splatok <= 0:
        raise ChybaEvidencie("Počet splátok musí byť kladný.")
    od = date.fromisoformat(over_datum(zaciatok))
    do = pridaj_mesiace(od, pocet_splatok) - date.resolution
    return pridaj_pravidelny_naklad(
        conn, f"Leasing: {stroj}", "leasing", mesacna_splatka, od.isoformat(), do.isoformat(), "fixny"
    )


def ukonci_pravidelny_naklad(conn: sqlite3.Connection, naklad_id: int, platny_do: str) -> None:
    cur = conn.execute(
        "UPDATE naklad_pravidelny SET platny_do = ? WHERE id = ?", (over_datum(platny_do), naklad_id)
    )
    if cur.rowcount == 0:
        raise ChybaEvidencie(f"Pravidelný náklad s ID {naklad_id} neexistuje.")
    conn.commit()


def zoznam_pravidelnych_nakladov(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM naklad_pravidelny ORDER BY kategoria, nazov").fetchall()


def pridaj_naklad(
    conn: sqlite3.Connection, datum: str, nazov: str, kategoria: str, suma: float, typ: str | None = None
) -> int:
    """Jednorazový náklad (oprava pece, faktúra za energie, obaly...)."""
    typ = _over_kategoriu(kategoria, typ)
    if suma < 0:
        raise ChybaEvidencie("Suma nemôže byť záporná.")
    cur = conn.execute(
        "INSERT INTO naklad (datum, nazov, kategoria, typ, suma) VALUES (?, ?, ?, ?, ?)",
        (over_datum(datum), nazov.strip(), kategoria, typ, suma),
    )
    conn.commit()
    return cur.lastrowid


# -------------------------------------------------------------------- tržby


def pridaj_trzbu(conn: sqlite3.Connection, datum: str, suma_bez_dph: float, kanal: str = "predajňa") -> int:
    if suma_bez_dph < 0:
        raise ChybaEvidencie("Tržba nemôže byť záporná.")
    cur = conn.execute(
        "INSERT INTO trzba (datum, suma_bez_dph, kanal) VALUES (?, ?, ?)",
        (over_datum(datum), suma_bez_dph, kanal.strip() or "predajňa"),
    )
    conn.commit()
    return cur.lastrowid
