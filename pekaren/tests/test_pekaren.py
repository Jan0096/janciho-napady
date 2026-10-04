import unittest
from datetime import date

from pekaren import evidencia as ev
from pekaren.analyza import analyzuj, analyzuj_mesiac, stav_faktur, zostatok_leasingov
from pekaren.cli import main
from pekaren.db import pripoj
from pekaren.demo import napln_demo
from pekaren.report import report_html, report_text, zostav_report


class ZakladTest(unittest.TestCase):
    def setUp(self):
        self.conn = pripoj(":memory:")
        self.muka = ev.pridaj_surovinu(self.conn, "Múka", "kg", 100)
        self.mlyn = ev.pridaj_dodavatela(self.conn, "Mlyn")


class TestEvidencia(ZakladTest):
    def test_prijem_a_sklad(self):
        ev.prijmi_suroviny(self.conn, "2026-01-05", self.mlyn, [ev.Polozka(self.muka, 100, 0.40)])
        ev.prijmi_suroviny(self.conn, "2026-01-12", self.mlyn, [ev.Polozka(self.muka, 100, 0.50)])
        ev.zapis_spotrebu(self.conn, "2026-01-20", self.muka, 150)
        s = ev.stav_skladu(self.conn)[0]
        self.assertAlmostEqual(s["zasoba"], 50)
        self.assertAlmostEqual(s["priemerna_cena"], 0.45)

    def test_neplatne_vstupy(self):
        with self.assertRaises(ev.ChybaEvidencie):
            ev.prijmi_suroviny(self.conn, "2026-01-05", self.mlyn, [ev.Polozka(self.muka, 0, 1)])
        with self.assertRaises(ev.ChybaEvidencie):
            ev.prijmi_suroviny(self.conn, "5.1.2026", self.mlyn, [ev.Polozka(self.muka, 1, 1)])
        with self.assertRaises(ev.ChybaEvidencie):
            ev.pridaj_dodavatela(self.conn, "Mlyn")
        with self.assertRaises(ev.ChybaEvidencie):
            ev.pridaj_naklad(self.conn, "2026-01-01", "x", "neexistuje", 10)
        with self.assertRaises(ev.ChybaEvidencie):
            ev.pridaj_fakturu(self.conn, "F1", self.mlyn, "2026-02-01", "2026-01-01", 10)

    def test_leasing_konci_po_poslednej_splatke(self):
        nid = ev.pridaj_leasing(self.conn, "Pec", 500, "2026-01-31", 3)
        n = self.conn.execute("SELECT * FROM naklad_pravidelny WHERE id=?", (nid,)).fetchone()
        self.assertEqual(n["platny_do"], "2026-04-29")


class TestAnalyza(ZakladTest):
    def test_zisk_a_bod_zvratu(self):
        ev.pridaj_trzbu(self.conn, "2026-03-10", 10_000)
        ev.prijmi_suroviny(self.conn, "2026-03-02", self.mlyn, [ev.Polozka(self.muka, 1000, 2.0)])
        ev.pridaj_pravidelny_naklad(self.conn, "Nájom", "najom", 1500, "2026-01-01")
        ev.pridaj_pravidelny_naklad(self.conn, "Mzdy", "mzdy", 3000, "2026-01-01")
        ev.pridaj_naklad(self.conn, "2026-03-15", "Obaly", "pohyblive", 1000)
        ev.pridaj_naklad(self.conn, "2026-04-15", "Mimo obdobia", "ostatne", 999)
        v = analyzuj_mesiac(self.conn, 2026, 3)
        self.assertAlmostEqual(v.suroviny, 2000)
        self.assertAlmostEqual(v.fixne, 4500)
        self.assertAlmostEqual(v.variabilne_prevadzkove, 1000)
        self.assertAlmostEqual(v.zisk, 2500)
        self.assertAlmostEqual(v.marza_zisku, 0.25)
        # príspevok na úhradu = 70 % → bod zvratu = 4500 / 0.7
        self.assertAlmostEqual(v.bod_zvratu, 4500 / 0.7)

    def test_pravidelny_naklad_platnost_a_kratenie(self):
        ev.pridaj_pravidelny_naklad(self.conn, "Nájom", "najom", 3100, "2026-01-16", "2026-02-28")
        self.assertAlmostEqual(analyzuj_mesiac(self.conn, 2026, 1).fixne, 1600)  # 16 z 31 dní
        self.assertAlmostEqual(analyzuj_mesiac(self.conn, 2026, 2).fixne, 3100)
        self.assertAlmostEqual(analyzuj_mesiac(self.conn, 2026, 3).fixne, 0)
        self.assertAlmostEqual(analyzuj(self.conn, date(2026, 1, 1), date(2026, 12, 31)).fixne, 4700)

    def test_strata_a_upozornenia(self):
        ev.pridaj_trzbu(self.conn, "2026-03-10", 1000)
        ev.prijmi_suroviny(self.conn, "2026-03-02", self.mlyn, [ev.Polozka(self.muka, 1000, 0.6)])
        ev.pridaj_pravidelny_naklad(self.conn, "Nájom", "najom", 800, "2026-01-01")
        v = analyzuj_mesiac(self.conn, 2026, 3)
        self.assertAlmostEqual(v.zisk, -400)
        text = " ".join(v.upozornenia())
        self.assertIn("STRATE", text)
        self.assertIn("Suroviny", text)
        self.assertIn("Nájom", text)

    def test_faktury_po_splatnosti_a_nesulad(self):
        fid = ev.pridaj_fakturu(self.conn, "F1", self.mlyn, "2026-01-01", "2026-01-15", 120, 24)
        ev.prijmi_suroviny(self.conn, "2026-01-01", self.mlyn, [ev.Polozka(self.muka, 100, 1.0)], fid)
        stav = stav_faktur(self.conn, date(2026, 2, 1))
        self.assertEqual(len(stav["po_splatnosti"]), 1)
        self.assertEqual(len(stav["nesulad"]), 1)
        self.assertAlmostEqual(stav["zavazky"], 144)
        ev.uhrad_fakturu(self.conn, fid, "2026-01-14")
        self.assertEqual(stav_faktur(self.conn, date(2026, 2, 1))["neuhradene"], [])

    def test_zostatok_leasingu(self):
        ev.pridaj_leasing(self.conn, "Pec", 500, "2026-01-01", 12)
        l = zostatok_leasingov(self.conn, date(2026, 3, 15))[0]
        self.assertEqual(l["zostava_splatok"], 9)  # apríl–december
        self.assertAlmostEqual(l["zostava_suma"], 4500)
        self.assertEqual(zostatok_leasingov(self.conn, date(2027, 1, 1)), [])


class TestDemoAReport(unittest.TestCase):
    def test_demo_report(self):
        conn = pripoj(":memory:")
        napln_demo(conn)
        r = zostav_report(conn, date(2026, 1, 1), date(2026, 6, 30), date(2026, 7, 20))
        self.assertEqual(len(r.mesiace), 6)
        self.assertAlmostEqual(sum(m.zisk for m in r.mesiace), r.celkom.zisk, places=6)
        self.assertGreater(r.celkom.trzby, 0)
        self.assertEqual(len(r.faktury["nesulad"]), 1)
        self.assertIn("VÝKAZ ZISKOV A STRÁT", report_text(r))
        self.assertIn("<table>", report_html(r))

    def test_prikazovy_riadok(self):
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            db, html = os.path.join(d, "p.db"), os.path.join(d, "r.html")
            self.assertEqual(main(["--db", db, "demo"]), 0)
            self.assertEqual(main(["--db", db, "demo"]), 1)  # neprepíše bez --prepisat
            self.assertEqual(main(["--db", db, "report", "--od", "2026-01", "--do", "2026-03", "--html", html]), 0)
            self.assertTrue(os.path.getsize(html) > 1000)


if __name__ == "__main__":
    unittest.main()
