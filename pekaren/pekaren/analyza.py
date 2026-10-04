"""Finančná analýza prevádzky: výsledok hospodárenia, ukazovatele a upozornenia."""

import sqlite3
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date

from .evidencia import KATEGORIE, pridaj_mesiace

# Odporúčané hranice pre pekárne (podiel na tržbách).
LIMIT_SUROVINY = 0.35
LIMIT_MZDY = 0.35
LIMIT_NAJOM = 0.12


@dataclass
class VysledokObdobia:
    od: date
    do: date
    trzby: float = 0.0
    trzby_podla_kanalu: dict[str, float] = field(default_factory=dict)
    suroviny: float = 0.0
    naklady_podla_kategorii: dict[str, float] = field(default_factory=dict)
    fixne: float = 0.0
    variabilne_prevadzkove: float = 0.0

    @property
    def nazov(self) -> str:
        if self.od.day == 1 and self.do == _koniec_mesiaca(self.od.year, self.od.month):
            return f"{self.od.month:02d}/{self.od.year}"
        return f"{self.od.isoformat()} – {self.do.isoformat()}"

    @property
    def prevadzkove_naklady(self) -> float:
        return self.fixne + self.variabilne_prevadzkove

    @property
    def naklady_spolu(self) -> float:
        return self.suroviny + self.prevadzkove_naklady

    @property
    def hruba_marza(self) -> float:
        """Tržby mínus náklady na suroviny."""
        return self.trzby - self.suroviny

    @property
    def zisk(self) -> float:
        """Výsledok hospodárenia (pred zdanením a odpismi)."""
        return self.trzby - self.naklady_spolu

    @property
    def variabilne_spolu(self) -> float:
        return self.suroviny + self.variabilne_prevadzkove

    @property
    def prispevok_na_uhradu(self) -> float:
        return self.trzby - self.variabilne_spolu

    def podiel(self, suma: float) -> float | None:
        return suma / self.trzby if self.trzby else None

    @property
    def marza_zisku(self) -> float | None:
        return self.podiel(self.zisk)

    @property
    def bod_zvratu(self) -> float | None:
        """Tržby, pri ktorých je zisk nulový: fixné / (1 − variabilné/tržby)."""
        pomer = self.podiel(self.prispevok_na_uhradu)
        if pomer is None or pomer <= 0:
            return None
        return self.fixne / pomer

    @property
    def bezpecnostna_rezerva(self) -> float | None:
        """O koľko % môžu tržby klesnúť, kým sa prevádzka dostane do straty."""
        bz = self.bod_zvratu
        if bz is None or not self.trzby:
            return None
        return (self.trzby - bz) / self.trzby

    def upozornenia(self) -> list[str]:
        vysledok = []
        if not self.trzby:
            vysledok.append("V období nie sú zadané žiadne tržby – zisk nie je možné posúdiť.")
            return vysledok
        if self.zisk < 0:
            vysledok.append(f"Prevádzka je v STRATE {_eur(-self.zisk)}.")
        podiel_surovin = self.podiel(self.suroviny)
        if podiel_surovin > LIMIT_SUROVINY:
            vysledok.append(
                f"Suroviny tvoria {_pct(podiel_surovin)} tržieb (odporúčané max. {LIMIT_SUROVINY:.0%}) "
                "– skontroluj ceny dodávateľov, odpad alebo predajné ceny."
            )
        podiel_mzdy = self.podiel(self.naklady_podla_kategorii.get("mzdy", 0))
        if podiel_mzdy > LIMIT_MZDY:
            vysledok.append(
                f"Mzdy tvoria {_pct(podiel_mzdy)} tržieb (odporúčané max. {LIMIT_MZDY:.0%})."
            )
        podiel_najom = self.podiel(self.naklady_podla_kategorii.get("najom", 0))
        if podiel_najom > LIMIT_NAJOM:
            vysledok.append(
                f"Nájom tvorí {_pct(podiel_najom)} tržieb (odporúčané max. {LIMIT_NAJOM:.0%})."
            )
        if self.bod_zvratu is None:
            vysledok.append("Variabilné náklady sú vyššie ako tržby – každý predaj prehlbuje stratu.")
        return vysledok


def _eur(x: float) -> str:
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _koniec_mesiaca(rok: int, mesiac: int) -> date:
    return date(rok, mesiac, monthrange(rok, mesiac)[1])


def mesiace_v_obdobi(od: date, do: date) -> list[tuple[int, int]]:
    vysledok = []
    rok, mesiac = od.year, od.month
    while (rok, mesiac) <= (do.year, do.month):
        vysledok.append((rok, mesiac))
        rok, mesiac = (rok + 1, 1) if mesiac == 12 else (rok, mesiac + 1)
    return vysledok


def _pocet_dni(od: date, do: date) -> int:
    return (do - od).days + 1


def analyzuj(conn: sqlite3.Connection, od: date, do: date) -> VysledokObdobia:
    """Výsledok hospodárenia za obdobie od–do (vrátane).

    Pravidelné náklady sa počítajú za každý mesiac, v ktorom platia; ak obdobie
    nepokrýva celý mesiac, náklad sa pomerne kráti podľa počtu dní.
    """
    if do < od:
        raise ValueError("Koniec obdobia je pred začiatkom.")
    v = VysledokObdobia(od=od, do=do)
    params = (od.isoformat(), do.isoformat())

    for row in conn.execute(
        "SELECT kanal, SUM(suma_bez_dph) AS s FROM trzba WHERE datum BETWEEN ? AND ? GROUP BY kanal",
        params,
    ):
        v.trzby_podla_kanalu[row["kanal"]] = row["s"]
    v.trzby = sum(v.trzby_podla_kanalu.values())

    v.suroviny = conn.execute(
        """SELECT COALESCE(SUM(pp.mnozstvo * pp.jednotkova_cena), 0)
           FROM prijem p JOIN prijem_polozka pp ON pp.prijem_id = p.id
           WHERE p.datum BETWEEN ? AND ?""",
        params,
    ).fetchone()[0]

    def pripocitaj(kategoria: str, typ: str, suma: float) -> None:
        v.naklady_podla_kategorii[kategoria] = v.naklady_podla_kategorii.get(kategoria, 0) + suma
        if typ == "fixny":
            v.fixne += suma
        else:
            v.variabilne_prevadzkove += suma

    for row in conn.execute(
        "SELECT kategoria, typ, SUM(suma) AS s FROM naklad WHERE datum BETWEEN ? AND ? GROUP BY kategoria, typ",
        params,
    ):
        pripocitaj(row["kategoria"], row["typ"], row["s"])

    pravidelne = conn.execute("SELECT * FROM naklad_pravidelny").fetchall()
    for rok, mesiac in mesiace_v_obdobi(od, do):
        zac_mes, kon_mes = date(rok, mesiac, 1), _koniec_mesiaca(rok, mesiac)
        dni_mesiaca = kon_mes.day
        for n in pravidelne:
            zac = max(zac_mes, od, date.fromisoformat(n["platny_od"]))
            kon = min(kon_mes, do)
            if n["platny_do"]:
                kon = min(kon, date.fromisoformat(n["platny_do"]))
            if kon < zac:
                continue
            # Ak náklad platí v celom analyzovanom úseku mesiaca, počíta sa celá
            # mesačná suma; inak pomerná časť podľa dní.
            pomer = _pocet_dni(zac, kon) / dni_mesiaca
            if zac == zac_mes and kon == kon_mes:
                pomer = 1.0
            pripocitaj(n["kategoria"], n["typ"], n["mesacna_suma"] * pomer)
    return v


def analyzuj_mesiac(conn: sqlite3.Connection, rok: int, mesiac: int) -> VysledokObdobia:
    return analyzuj(conn, date(rok, mesiac, 1), _koniec_mesiaca(rok, mesiac))


def mesacny_vyvoj(conn: sqlite3.Connection, od: date, do: date) -> list[VysledokObdobia]:
    """Výsledky po jednotlivých mesiacoch obdobia."""
    vysledok = []
    for rok, mesiac in mesiace_v_obdobi(od, do):
        zac = max(od, date(rok, mesiac, 1))
        kon = min(do, _koniec_mesiaca(rok, mesiac))
        vysledok.append(analyzuj(conn, zac, kon))
    return vysledok


def nazov_kategorie(kod: str) -> str:
    return KATEGORIE.get(kod, (kod, ""))[0]


# ------------------------------------------------------- suroviny a faktúry


def vyvoj_cien_surovin(conn: sqlite3.Connection, od: date, do: date) -> list[dict]:
    """Porovná priemernú nákupnú cenu suroviny na začiatku a na konci obdobia."""
    vysledok = []
    for s in conn.execute("SELECT id, nazov, jednotka FROM surovina ORDER BY nazov"):
        riadky = conn.execute(
            """SELECT substr(p.datum, 1, 7) AS mesiac,
                      SUM(pp.mnozstvo * pp.jednotkova_cena) / SUM(pp.mnozstvo) AS cena,
                      SUM(pp.mnozstvo) AS mnozstvo, SUM(pp.mnozstvo * pp.jednotkova_cena) AS suma
               FROM prijem p JOIN prijem_polozka pp ON pp.prijem_id = p.id
               WHERE pp.surovina_id = ? AND p.datum BETWEEN ? AND ?
               GROUP BY mesiac ORDER BY mesiac""",
            (s["id"], od.isoformat(), do.isoformat()),
        ).fetchall()
        if not riadky:
            continue
        prva, posledna = riadky[0]["cena"], riadky[-1]["cena"]
        vysledok.append(
            {
                "surovina": s["nazov"],
                "jednotka": s["jednotka"],
                "mnozstvo": sum(r["mnozstvo"] for r in riadky),
                "suma": sum(r["suma"] for r in riadky),
                "prva_cena": prva,
                "posledna_cena": posledna,
                "zmena": round((posledna - prva) / prva, 4) if prva else None,
            }
        )
    vysledok.sort(key=lambda r: r["suma"], reverse=True)
    return vysledok


def stav_faktur(conn: sqlite3.Connection, k_datumu: date) -> dict:
    """Neuhradené faktúry, faktúry po splatnosti a nesúlad s príjemkami."""
    from .evidencia import zoznam_faktur

    neuhradene, po_splatnosti, nesulad = [], [], []
    for f in zoznam_faktur(conn):
        if f["datum_uhrady"] is None:
            neuhradene.append(f)
            if f["datum_splatnosti"] < k_datumu.isoformat():
                po_splatnosti.append(f)
        if f["suma_prijemok"] and abs(f["suma_prijemok"] - f["suma_bez_dph"]) > 0.01:
            nesulad.append(f)
    return {
        "neuhradene": neuhradene,
        "po_splatnosti": po_splatnosti,
        "nesulad": nesulad,
        "zavazky": sum(f["suma_bez_dph"] + f["dph"] for f in neuhradene),
    }


def zostatok_leasingov(conn: sqlite3.Connection, k_datumu: date) -> list[dict]:
    """Koľko splátok a peňazí ešte zostáva zaplatiť na leasingoch."""
    vysledok = []
    for n in conn.execute(
        "SELECT * FROM naklad_pravidelny WHERE kategoria = 'leasing' AND platny_do IS NOT NULL"
    ):
        koniec = date.fromisoformat(n["platny_do"])
        # Splátky sú mesačne v deň začiatku leasingu; zostávajú tie po k_datumu.
        zaciatok = date.fromisoformat(n["platny_od"])
        splatky, i = [], 0
        while (d := pridaj_mesiace(zaciatok, i)) <= koniec:
            splatky.append(d)
            i += 1
        zostava = sum(1 for d in splatky if d > k_datumu)
        if not zostava:
            continue
        vysledok.append(
            {
                "nazov": n["nazov"],
                "splatka": n["mesacna_suma"],
                "koniec": koniec,
                "zostava_splatok": zostava,
                "zostava_suma": zostava * n["mesacna_suma"],
            }
        )
    return vysledok
