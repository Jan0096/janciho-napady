"""Zostavenie finančného reportu – textovo do terminálu alebo ako HTML stránka."""

import html
import sqlite3
from dataclasses import dataclass
from datetime import date

from .analyza import (
    VysledokObdobia,
    analyzuj,
    mesacny_vyvoj,
    nazov_kategorie,
    stav_faktur,
    vyvoj_cien_surovin,
    zostatok_leasingov,
)
from .evidencia import KATEGORIE, stav_skladu


def eur(x: float | None) -> str:
    if x is None:
        return "–"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def pct(x: float | None) -> str:
    if x is None:
        return "–"
    return f"{x * 100:.1f} %".replace(".", ",")


@dataclass
class Report:
    celkom: VysledokObdobia
    mesiace: list[VysledokObdobia]
    ceny: list[dict]
    faktury: dict
    leasingy: list[dict]
    sklad_pod_minimom: list[sqlite3.Row]
    k_datumu: date


def zostav_report(conn: sqlite3.Connection, od: date, do: date, k_datumu: date | None = None) -> Report:
    k_datumu = k_datumu or date.today()
    return Report(
        celkom=analyzuj(conn, od, do),
        mesiace=mesacny_vyvoj(conn, od, do),
        ceny=vyvoj_cien_surovin(conn, od, do),
        faktury=stav_faktur(conn, k_datumu),
        leasingy=zostatok_leasingov(conn, k_datumu),
        sklad_pod_minimom=[s for s in stav_skladu(conn) if s["min_zasoba"] and s["zasoba"] < s["min_zasoba"]],
        k_datumu=k_datumu,
    )


def _vykaz_riadky(v: VysledokObdobia) -> list[tuple[str, float, float | None, bool]]:
    """Riadky výkazu ziskov a strát: (popis, suma, podiel na tržbách, zvýraznený)."""
    riadky = [("TRŽBY (bez DPH)", v.trzby, v.podiel(v.trzby), True)]
    for kanal, suma in sorted(v.trzby_podla_kanalu.items()):
        riadky.append((f"   z toho {kanal}", suma, v.podiel(suma), False))
    riadky.append(("Náklady na suroviny", -v.suroviny, v.podiel(v.suroviny), False))
    riadky.append(("HRUBÁ MARŽA", v.hruba_marza, v.podiel(v.hruba_marza), True))
    for kod in KATEGORIE:
        suma = v.naklady_podla_kategorii.get(kod)
        if suma:
            riadky.append((nazov_kategorie(kod), -suma, v.podiel(suma), False))
    for kod, suma in v.naklady_podla_kategorii.items():
        if kod not in KATEGORIE and suma:
            riadky.append((kod, -suma, v.podiel(suma), False))
    riadky.append(("Prevádzkové náklady spolu", -v.prevadzkove_naklady, v.podiel(v.prevadzkove_naklady), False))
    riadky.append(("ZISK / STRATA", v.zisk, v.marza_zisku, True))
    return riadky


def _ukazovatele(v: VysledokObdobia) -> list[tuple[str, str]]:
    return [
        ("Náklady spolu", eur(v.naklady_spolu)),
        ("Fixné náklady", eur(v.fixne)),
        ("Variabilné náklady (vrátane surovín)", eur(v.variabilne_spolu)),
        ("Podiel surovín na tržbách (food cost)", pct(v.podiel(v.suroviny))),
        ("Podiel miezd na tržbách", pct(v.podiel(v.naklady_podla_kategorii.get("mzdy", 0)))),
        ("Marža zisku", pct(v.marza_zisku)),
        ("Bod zvratu (potrebné tržby)", eur(v.bod_zvratu)),
        ("Bezpečnostná rezerva tržieb", pct(v.bezpecnostna_rezerva)),
    ]


# ---------------------------------------------------------------- text


def report_text(r: Report) -> str:
    v = r.celkom
    out = [
        "=" * 64,
        f" FINANČNÁ ANALÝZA PREVÁDZKY  {v.od.strftime('%d.%m.%Y')} – {v.do.strftime('%d.%m.%Y')}",
        "=" * 64,
        "",
        "VÝKAZ ZISKOV A STRÁT",
        "-" * 64,
    ]
    for popis, suma, podiel, tucne in _vykaz_riadky(v):
        out.append(f"{popis:<38}{eur(suma):>16}{pct(podiel):>10}")
        if tucne:
            out.append("-" * 64)
    out += ["", "UKAZOVATELE", "-" * 64]
    out += [f"{k:<44}{h:>20}" for k, h in _ukazovatele(v)]

    stav = "ZISK" if v.zisk >= 0 else "STRATA"
    out += ["", f">>> VÝSLEDOK: {stav} {eur(abs(v.zisk))} <<<"]

    upozornenia = v.upozornenia()
    if upozornenia:
        out += ["", "UPOZORNENIA", "-" * 64] + [f" ! {u}" for u in upozornenia]

    if len(r.mesiace) > 1:
        out += ["", "VÝVOJ PO MESIACOCH", "-" * 64]
        out.append(f"{'Mesiac':<10}{'Tržby':>14}{'Suroviny':>13}{'Prev. nákl.':>13}{'Zisk':>14}")
        for m in r.mesiace:
            out.append(
                f"{m.nazov:<10}{eur(m.trzby):>14}{eur(m.suroviny):>13}"
                f"{eur(m.prevadzkove_naklady):>13}{eur(m.zisk):>14}"
            )

    if r.ceny:
        out += ["", "NÁKUP SUROVÍN A VÝVOJ CIEN", "-" * 64]
        for c in r.ceny:
            out.append(
                f"{c['surovina'][:21]:<22}{_mn(c['mnozstvo']):>10} {c['jednotka']:<3}{eur(c['suma']):>13}"
                f"  {eur(c['posledna_cena'])}/{c['jednotka']} ({_zmena(c['zmena'])})"
            )

    f = r.faktury
    out += ["", f"FAKTÚRY ZA SUROVINY (k {r.k_datumu.strftime('%d.%m.%Y')})", "-" * 64]
    out.append(f"Neuhradené: {len(f['neuhradene'])} ks, záväzky spolu {eur(f['zavazky'])} (s DPH)")
    for fa in f["po_splatnosti"]:
        out.append(f" ! PO SPLATNOSTI: {fa['cislo']} ({fa['dodavatel']}) splatná {fa['datum_splatnosti']}")
    for fa in f["nesulad"]:
        out.append(
            f" ! NESÚLAD: faktúra {fa['cislo']} {eur(fa['suma_bez_dph'])} vs. príjemky {eur(fa['suma_prijemok'])}"
        )

    if r.leasingy:
        out += ["", "LEASINGY – ZOSTÁVA ZAPLATIŤ", "-" * 64]
        for l in r.leasingy:
            out.append(
                f"{l['nazov']:<34}{l['zostava_splatok']:>3} x {eur(l['splatka'])} = {eur(l['zostava_suma'])}"
            )

    if r.sklad_pod_minimom:
        out += ["", "SUROVINY POD MINIMÁLNOU ZÁSOBOU", "-" * 64]
        for s in r.sklad_pod_minimom:
            out.append(f" ! {s['nazov']}: {_mn(s['zasoba'])} {s['jednotka']} (minimum {_mn(s['min_zasoba'])})")
    return "\n".join(out)


def _mn(x: float) -> str:
    return f"{x:,.1f}".replace(",", " ").replace(".", ",")


def _zmena(z: float | None) -> str:
    if z is None:
        return "–"
    return ("+" if z > 0 else "") + pct(z)


# ---------------------------------------------------------------- HTML

_CSS = """
:root { --bg:#fffaf3; --fg:#2b2118; --muted:#7a6a5a; --line:#e8dccb; --card:#fff;
        --plus:#2e7d32; --minus:#c62828; --accent:#b5651d; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#1d1814; --fg:#f3e9dc; --muted:#b3a593; --line:#3a3027; --card:#26201a;
          --plus:#81c784; --minus:#ef9a9a; --accent:#e0a060; } }
body { background:var(--bg); color:var(--fg); font:15px/1.5 system-ui,sans-serif; margin:0; padding:16px; }
main { max-width:900px; margin:auto; }
h1 { color:var(--accent); margin-bottom:0; } h2 { margin-top:32px; border-bottom:2px solid var(--line); }
.sub { color:var(--muted); }
.kpi { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; }
.kpi div { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px; }
.kpi b { display:block; font-size:22px; } .kpi span { color:var(--muted); font-size:13px; }
.wrap { overflow-x:auto; }
table { width:100%; border-collapse:collapse; background:var(--card); }
td, th { padding:6px 10px; border-bottom:1px solid var(--line); text-align:right; white-space:nowrap; }
td:first-child, th:first-child { text-align:left; }
tr.sum td { font-weight:700; }
.plus { color:var(--plus); } .minus { color:var(--minus); }
.warn { background:#fff3cd; color:#5c4400; border-radius:8px; padding:8px 12px; margin:6px 0; }
.bar { height:10px; background:var(--accent); border-radius:5px; }
"""


def _e(x) -> str:
    return html.escape(str(x))


def _trieda(x: float) -> str:
    return "plus" if x >= 0 else "minus"


def report_html(r: Report) -> str:
    v = r.celkom
    obdobie = f"{v.od.strftime('%d.%m.%Y')} – {v.do.strftime('%d.%m.%Y')}"
    c = [
        "<!doctype html><html lang='sk'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>Finančná analýza pekárne</title><style>{_CSS}</style></head><body><main>",
        "<h1>Finančná analýza prevádzky</h1>",
        f"<p class='sub'>Obdobie {_e(obdobie)} · vygenerované {date.today().strftime('%d.%m.%Y')}</p>",
        "<div class='kpi'>",
        f"<div><span>Tržby</span><b>{eur(v.trzby)}</b></div>",
        f"<div><span>Náklady spolu</span><b>{eur(v.naklady_spolu)}</b></div>",
        f"<div><span>{'Zisk' if v.zisk >= 0 else 'Strata'}</span>"
        f"<b class='{_trieda(v.zisk)}'>{eur(v.zisk)}</b></div>",
        f"<div><span>Marža zisku</span><b>{pct(v.marza_zisku)}</b></div>",
        f"<div><span>Bod zvratu</span><b>{eur(v.bod_zvratu)}</b></div>",
        "</div>",
    ]
    for u in v.upozornenia():
        c.append(f"<div class='warn'>⚠ {_e(u)}</div>")

    c.append("<h2>Výkaz ziskov a strát</h2><div class='wrap'><table>")
    c.append("<tr><th>Položka</th><th>Suma</th><th>% z tržieb</th></tr>")
    for popis, suma, podiel, tucne in _vykaz_riadky(v):
        c.append(
            f"<tr class='{'sum' if tucne else ''}'><td>{_e(popis)}</td>"
            f"<td class='{_trieda(suma)}'>{eur(suma)}</td><td>{pct(podiel)}</td></tr>"
        )
    c.append("</table></div>")

    c.append("<h2>Ukazovatele</h2><div class='wrap'><table>")
    c += [f"<tr><td>{_e(k)}</td><td>{_e(h)}</td></tr>" for k, h in _ukazovatele(v)]
    c.append("</table></div>")

    # Štruktúra nákladov ako jednoduché pruhy.
    struktura = [("Suroviny", v.suroviny)] + [
        (nazov_kategorie(k), s) for k, s in sorted(v.naklady_podla_kategorii.items(), key=lambda x: -x[1]) if s
    ]
    if v.naklady_spolu:
        c.append("<h2>Štruktúra nákladov</h2><div class='wrap'><table>")
        for nazov, suma in struktura:
            podiel = suma / v.naklady_spolu
            c.append(
                f"<tr><td>{_e(nazov)}</td><td style='width:45%'><div class='bar' "
                f"style='width:{podiel * 100:.1f}%'></div></td><td>{eur(suma)}</td><td>{pct(podiel)}</td></tr>"
            )
        c.append("</table></div>")

    if len(r.mesiace) > 1:
        c.append("<h2>Vývoj po mesiacoch</h2><div class='wrap'><table>")
        c.append("<tr><th>Mesiac</th><th>Tržby</th><th>Suroviny</th><th>Prevádzkové náklady</th>"
                 "<th>Zisk / strata</th><th>Marža</th></tr>")
        for m in r.mesiace:
            c.append(
                f"<tr><td>{_e(m.nazov)}</td><td>{eur(m.trzby)}</td><td>{eur(m.suroviny)}</td>"
                f"<td>{eur(m.prevadzkove_naklady)}</td><td class='{_trieda(m.zisk)}'>{eur(m.zisk)}</td>"
                f"<td>{pct(m.marza_zisku)}</td></tr>"
            )
        c.append("</table></div>")

    if r.ceny:
        c.append("<h2>Nákup surovín a vývoj cien</h2><div class='wrap'><table>")
        c.append("<tr><th>Surovina</th><th>Množstvo</th><th>Nakúpené za</th><th>Cena na začiatku</th>"
                 "<th>Cena na konci</th><th>Zmena</th></tr>")
        for x in r.ceny:
            trieda = "minus" if (x["zmena"] or 0) > 0 else "plus"
            c.append(
                f"<tr><td>{_e(x['surovina'])}</td><td>{_mn(x['mnozstvo'])} {_e(x['jednotka'])}</td>"
                f"<td>{eur(x['suma'])}</td><td>{eur(x['prva_cena'])}</td><td>{eur(x['posledna_cena'])}</td>"
                f"<td class='{trieda}'>{_zmena(x['zmena'])}</td></tr>"
            )
        c.append("</table></div>")

    f = r.faktury
    c.append(f"<h2>Faktúry za suroviny</h2><p>Neuhradené: <b>{len(f['neuhradene'])}</b> ks, "
             f"záväzky spolu <b>{eur(f['zavazky'])}</b> (s DPH, k {r.k_datumu.strftime('%d.%m.%Y')})</p>")
    if f["neuhradene"]:
        c.append("<div class='wrap'><table><tr><th>Číslo</th><th>Dodávateľ</th><th>Splatnosť</th>"
                 "<th>Suma s DPH</th><th>Stav</th></tr>")
        for fa in f["neuhradene"]:
            po = fa in f["po_splatnosti"]
            c.append(
                f"<tr><td>{_e(fa['cislo'])}</td><td>{_e(fa['dodavatel'])}</td><td>{_e(fa['datum_splatnosti'])}</td>"
                f"<td>{eur(fa['suma_bez_dph'] + fa['dph'])}</td>"
                f"<td class='{'minus' if po else ''}'>{'po splatnosti' if po else 'v splatnosti'}</td></tr>"
            )
        c.append("</table></div>")
    for fa in f["nesulad"]:
        c.append(f"<div class='warn'>⚠ Faktúra {_e(fa['cislo'])} ({_e(fa['dodavatel'])}) je na "
                 f"{eur(fa['suma_bez_dph'])}, ale príjemky k nej sú na {eur(fa['suma_prijemok'])}.</div>")

    if r.leasingy:
        c.append("<h2>Leasingy – zostáva zaplatiť</h2><div class='wrap'><table>")
        c.append("<tr><th>Stroj</th><th>Splátka</th><th>Zostáva splátok</th><th>Zostáva spolu</th><th>Koniec</th></tr>")
        for l in r.leasingy:
            c.append(f"<tr><td>{_e(l['nazov'])}</td><td>{eur(l['splatka'])}</td><td>{l['zostava_splatok']}</td>"
                     f"<td>{eur(l['zostava_suma'])}</td><td>{l['koniec'].strftime('%d.%m.%Y')}</td></tr>")
        c.append("</table></div>")

    if r.sklad_pod_minimom:
        c.append("<h2>Suroviny pod minimálnou zásobou</h2>")
        for s in r.sklad_pod_minimom:
            c.append(f"<div class='warn'>⚠ {_e(s['nazov'])}: {_mn(s['zasoba'])} {_e(s['jednotka'])} "
                     f"(minimum {_mn(s['min_zasoba'])})</div>")

    c.append("</main></body></html>")
    return "\n".join(c)
