import unittest, json, pathlib
import tests.config_example_shim as C
from engine import analyze, classify_context as cc

class ClassifyTest(unittest.TestCase):
    def setUp(self):
        analyze.C = C
        raw = json.loads(pathlib.Path("tests/fixtures/moneytor_person_a.json").read_text("utf-8"))["transactions"]
        self.txs = [t for t in (analyze.map_moneytor(r, "person_a") for r in raw) if t]

    def _m(self, suffix): return next(t for t in self.txs if t["id"].endswith(suffix))

    def test_bank_gate_routes_on_bank_kind_not_source(self):
        self.assertEqual(analyze.classify_deterministic(self._m("SALARY"))["status"], "earnings")

    def test_landlord_rent_classified(self):
        self.assertEqual(analyze.classify_deterministic(self._m("RENT"))["status"], "landlord_rent")

    def test_grocery_by_merchant_regex(self):
        self.assertEqual(analyze.classify_deterministic(self._m("GROCERY"))["status"], "shared")

    def test_card_refund_excluded_from_spend(self):
        self.assertEqual(analyze.classify_deterministic(self._m("REFUND"))["status"], "refund")

    def test_foreign_escalates_to_residue(self):
        self.assertIsNone(analyze.classify_deterministic(self._m("FOREIGN")))

    def test_classify_all_two_sweeps_and_residue(self):
        store = {}; queue = []
        cls = analyze.classify_all(self.txs, store, queue, rubric_hash=cc.rubric_hash())
        self.assertIn("01AAAA0000000000000FOREIGN", [t["id"] for t in queue])
        statuses = {t["id"][-6:]: t["status"] for t in cls}
        self.assertEqual(statuses["ROCERY"], "shared")

if __name__ == "__main__":
    unittest.main()
