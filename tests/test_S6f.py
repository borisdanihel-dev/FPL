"""S6f - S6b and S6c repeated on 2024/25 (tools/xp_v2_2425.py; prereg/S6f.md,
Part F item F-D, RULING 19 Oct evening point 1). Hermetic: S6b/S6c's toy
season (S5/S11 toys) laid out as a 2024-25 / 2023-24 history root in a
temporary folder, with its DEFCON counts zeroed; no network, no real data."""
import csv
import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import odds_lambda as OL                                          # noqa: E402
import rules as R                                                 # noqa: E402
import xp_v2_replay as X                                          # noqa: E402
import xp_v2_2425 as F                                            # noqa: E402
from tests.test_S5 import toy_season                              # noqa: E402
from tests.test_S11 import toy_prior                              # noqa: E402
from tests.test_S6b import toy_rules_root                         # noqa: E402
from tests.test_S6c import add_s6c_inputs                         # noqa: E402

RESCORED_HEAD = ["season", "round", "element", "code", "position_own", "position_2627", "in_2627", "minutes", *R.CATEGORIES,
                 "points_2627_rules", "official", "bonus_flag", "defcon_flag"]


def zero_counts(folder):
    p = os.path.join(folder, "merged_gw.csv")
    with open(p, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        if "defensive_contribution" in r:
            r["defensive_contribution"] = "0"
    with open(p, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)


def rescored_csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(RESCORED_HEAD)
        for el, rnd, dc, flag in rows:
            parts = {c: 0 for c in R.CATEGORIES}
            parts["appearance"], parts["defensive_contribution"] = 2, dc
            w.writerow(["2024-25", rnd, el, 100 + el, "MID", "MID", 1, 90, *(parts[c] for c in R.CATEGORIES),
                        sum(parts.values()), 2, "2024-25 BPS", flag])


class Toy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root, cls.rules = tempfile.mkdtemp(), tempfile.mkdtemp()
        cls.hist, cls.prior = os.path.join(cls.root, "2024-25"), os.path.join(cls.root, "2023-24")
        os.makedirs(cls.hist); os.makedirs(cls.prior)
        cls.odds = toy_season(cls.hist, skip_fixture=13)
        add_s6c_inputs(cls.hist)
        toy_prior(cls.prior)
        toy_rules_root(cls.rules, cls.hist)
        cls.rescored = X.rescore(cls.rules, os.path.join(cls.rules, "rescored.csv"))
        zero_counts(cls.hist)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True); shutil.rmtree(cls.rules, ignore_errors=True)

    def run_tool(self, **kw):
        lines = []
        with mock.patch.object(F, "rescore", return_value=self.rescored):
            res = F.run(self.root, lines.append, odds_file=self.odds, out_csv=os.path.join(self.root, "r.csv"), first=5, last=6,
                        n_squads=3, **kw)
        return res, lines

    def test_the_numbers_are_s6b_and_s6c_unchanged(self):
        res, _ = self.run_tool()
        c = X.test_s6c(self.hist, self.prior, out=lambda s: None, odds_file=self.odds, first=5, last=6, n_squads=3,
                       rescored=self.rescored)
        b = X.test_2526(self.hist, self.prior, self.root, out=lambda s: None, odds_file=self.odds, first=5, last=6, n_squads=3,
                        rescored=self.rescored)
        self.assertEqual(res["s6c"]["per"], c["per"]); self.assertEqual(res["s6c"]["boot"], c["boot"])
        self.assertEqual(res["s6b"]["per"], b["per"]); self.assertEqual(res["s6b"]["boot"], b["boot"])
        self.assertEqual(res["s6c"]["squads"], c["squads"])
        self.assertEqual(res["pass"], c["boot"]["lo"] > 0)                                  # primary: against own_rebuilt
        self.assertEqual(len(res["s6c"]["squads"]), 3)

    def test_the_report_labels_and_the_bar(self):
        res, lines = self.run_tool()
        text = chr(10).join(lines)
        self.assertTrue(lines[0].startswith("S6F TEST  2024/25 GW5-6 (F-D: S6b and S6c repeated)"))
        self.assertIn("priors 2023/24", lines[0]); self.assertIn("2024/25 GW1 ownership", lines[0])
        self.assertIn(X.OWN_REBUILT_LACKS.replace("2024/25", "2023/24"), text)            # S6c's note, the prior season named
        self.assertIn("DEFCON removed on both sides", text); self.assertIn("Limitation: the test says nothing about DEFCON", text)
        self.assertIn(f"xp_v2 - own_rebuilt {res['s6c']['boot']['mean']:+.3f}", text)
        self.assertIn(f"S6b's xp_v2 - own_proxy {res['s6b']['boot']['mean']:+.3f}", text)
        rows = [l for l in lines if l.strip()[:2].strip().isdigit()]
        self.assertEqual([int(l.split()[0]) for l in rows], [5, 6])
        for line, rc, rb in zip(rows, res["s6c"]["per"], res["s6b"]["per"]):
            self.assertEqual(line.split()[3:6], [f"{rc['diff']:+.2f}", f"{rc['prx']:.2f}", f"{rb['diff']:+.2f}"])   # diff, own_proxy, v2-prx
        for want_pass, lo in ((True, 0.01), (False, 0.0), (False, -0.5)):
            with mock.patch.object(X.BT, "bootstrap_mean", return_value={"mean": 0.5, "lo": lo, "hi": 1.0, "n": 2, "p": 0.1}):
                res2, lines2 = self.run_tool()
            self.assertEqual(res2["pass"], want_pass)
            self.assertEqual(lines2[-1].endswith("PASS"), want_pass)
            if not want_pass:
                self.assertIn("does not revert GW8+ by itself", lines2[-1])

    def test_the_bar_is_the_primary_against_own_rebuilt(self):
        c, _ = self.run_tool()
        for lo_c, lo_b, want in ((0.1, -1.0, True), (-0.1, 1.0, False)):
            s6c = dict(c["s6c"], boot=dict(c["s6c"]["boot"], lo=lo_c))
            s6b = dict(c["s6b"], boot=dict(c["s6b"]["boot"], lo=lo_b))
            with mock.patch.object(F.XR, "test_s6c", return_value=s6c), mock.patch.object(F.XR, "test_2526", return_value=s6b):
                res, lines = self.run_tool()
            self.assertEqual(res["pass"], want)                                             # S6c's bound decides, never S6b's
            self.assertIn(f"[{lo_c:+.3f}, ", [l for l in lines if l.startswith("  primary:")][0])
        with mock.patch.object(F.XR, "test_2526", return_value=dict(c["s6b"], squads=[[1]])), self.assertRaises(F.MissingInput):
            self.run_tool()                                                                   # both drivers on the same squads

    def test_defcon_counts_are_refused(self):
        hist = tempfile.mkdtemp()
        try:
            with open(os.path.join(hist, "merged_gw.csv"), "w", encoding="utf-8", newline="") as fh:
                fh.write("element,round,minutes,defensive_contribution\n1,1,90,0\n2,1,90,0\n")
            self.assertEqual(F.check_no_counts(hist), ["defensive_contribution"])
            with open(os.path.join(hist, "merged_gw.csv"), "a", encoding="utf-8", newline="") as fh:
                fh.write("3,2,90,11\n")
            with self.assertRaises(F.MissingInput):
                F.check_no_counts(hist)
            with open(os.path.join(hist, "merged_gw.csv"), "w", encoding="utf-8", newline="") as fh:
                fh.write("element,round,minutes\n1,1,90\n")
            self.assertEqual(F.check_no_counts(hist), [])                                  # no column: no counts
            p = os.path.join(hist, "r.csv")
            rescored_csv(p, [(1, 1, 0, R.DEFCON_MISSING), (2, 1, 0, R.DEFCON_MISSING)])
            self.assertEqual(F.check_rescored(p), 2)
            for bad in ((3, 2, 2, R.DEFCON_MISSING), (3, 2, 0, "")):
                rescored_csv(p, [(1, 1, 0, R.DEFCON_MISSING), bad])
                with self.assertRaises(F.MissingInput):
                    F.check_rescored(p)
            with mock.patch.object(F.R, "normalise_season", side_effect=lambda out, h, s, say: rescored_csv(out, [(1, 5, 2, "")])):
                with self.assertRaises(F.MissingInput):
                    F.rescore(hist, p)                                                    # the re-score is checked before it is read
        finally:
            shutil.rmtree(hist, ignore_errors=True)
        with mock.patch.object(F, "check_no_counts", side_effect=F.MissingInput("counts")), self.assertRaises(F.MissingInput):
            self.run_tool()

    def test_the_alias_is_for_2024_25_and_restored(self):
        before = dict(OL.FD_ALIASES)
        with F.season_names("2024-25") as names:
            self.assertEqual(names["Ipswich"], "Ipswich"); self.assertIs(OL.FD_ALIASES, names)
            self.assertEqual(names["Man United"], before["Man United"])
        self.assertEqual(OL.FD_ALIASES, before); self.assertEqual(OL.FD_ALIASES["Ipswich"], "Ipswich Town")
        with self.assertRaises(RuntimeError):
            with F.season_names("2024-25"):
                raise RuntimeError("boom")
        self.assertEqual(OL.FD_ALIASES, before)                                            # restored after an error too
        with F.season_names("2099-00") as names:
            self.assertEqual(names, before)
        name_to_short = {"Ipswich": "IPS", "Arsenal": "ARS"}
        p = os.path.join(self.root, "fd.csv")
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write("Date,HomeTeam,AwayTeam,AvgH,AvgD,AvgA,Avg>2.5,Avg<2.5\n17/08/2024,Ipswich,Arsenal,4.0,3.5,1.9,1.8,2.0\n")
        with self.assertRaises(OL.MissingInput):
            OL.load_odds(p, name_to_short)                                                  # S5's table alone: 2026/27's name
        with F.season_names("2024-25"):
            self.assertEqual(OL.load_odds(p, name_to_short)[0]["home"], "IPS")

    def test_cli_run_txt_and_isolation(self):
        out = tempfile.mkdtemp()
        try:
            with mock.patch.object(F, "rescore", return_value=self.rescored), redirect_stdout(io.StringIO()):
                rc = F.main(["--test", "--hist", self.root, "--odds", self.odds, "--out", out])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(os.path.join(out, "s6f_2024-25.txt")))
            with open(os.path.join(out, "run.txt"), encoding="utf-8") as fh:
                self.assertIn("tools/xp_v2_2425.py", fh.read())
            with redirect_stdout(io.StringIO()):
                self.assertEqual(F.main(["--test", "--hist", os.path.join(out, "none"), "--out", out]), 2)
        finally:
            shutil.rmtree(out, ignore_errors=True)
        for name in os.listdir(ROOT):
            if name.endswith(".py"):
                with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
                    self.assertNotIn("xp_v2_2425", fh.read(), name)                       # the runner never imports it


if __name__ == "__main__":
    unittest.main()
