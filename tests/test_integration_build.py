import unittest, shutil, pathlib, tempfile
import tests.config_example_shim as C
from engine import analyze

class IntegrationBuildTest(unittest.TestCase):
    def setUp(self):
        analyze.C = C
        self.out = pathlib.Path(tempfile.mkdtemp())
        (self.out / "snapshot").mkdir()
        for p in ("person_a", "person_b"):
            shutil.copy(f"tests/fixtures/moneytor_{p}.json", self.out / "snapshot" / f"{p}.json")
        analyze.OUTDIR = self.out

    def test_full_pipeline_builds_a_report(self):
        analyze.main()
        report = self.out / C.REPORT_NAME
        self.assertTrue(report.exists(), "report.html was not written")
        html = report.read_text(encoding="utf-8")
        self.assertGreater(len(html), 1000)
        self.assertIn("<html", html.lower())
        # the store was written and is the source of truth
        self.assertTrue((self.out / "decisions.json").exists())

    def test_report_has_no_none_crash_and_classifies(self):
        analyze.main()
        # decisions.json should hold rule decisions for the deterministic backbone
        import json
        store = json.loads((self.out / "decisions.json").read_text("utf-8"))
        # person_a salary -> earnings (bank), grocery -> shared (card)
        self.assertTrue(any(d["status"] == "earnings" for d in store.values()))
        self.assertTrue(any(d["status"] == "shared" for d in store.values()))

    def test_earnings_section_is_not_zeroed(self):
        analyze.main()
        html = (self.out / C.REPORT_NAME).read_text(encoding="utf-8")
        # the person_a salary credit (12000) must reach the rendered earnings section
        self.assertTrue(("12,000" in html) or ("12000" in html),
                        "earnings section appears zeroed — bank credits not aggregated")

if __name__ == "__main__":
    unittest.main()
