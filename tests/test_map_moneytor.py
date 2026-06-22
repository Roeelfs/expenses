import json, unittest, pathlib
import tests.config_example_shim as C
from engine import analyze

FIX = pathlib.Path("tests/fixtures/moneytor_person_a.json")

class MapTest(unittest.TestCase):
    def setUp(self):
        analyze.C = C
        self.raw = json.loads(FIX.read_text(encoding="utf-8"))["transactions"]

    def _by_id(self, suffix):
        for r in self.raw:
            if r["id"].endswith(suffix):
                return analyze.map_moneytor(r, "person_a")
        raise KeyError(suffix)

    def test_zero_amount_dropped(self):
        self.assertIsNone(self._by_id("ZERO"))

    def test_expense_amount_is_positive_magnitude_and_debit(self):
        g = self._by_id("GROCERY")
        self.assertEqual(g["amount"], 250.50)
        self.assertEqual(g["sub_type"], "debit")

    def test_income_is_credit(self):
        self.assertEqual(self._by_id("SALARY")["sub_type"], "credit")

    def test_card_refund_is_credit_on_card(self):
        r = self._by_id("REFUND")
        self.assertEqual((r["account_kind"], r["sub_type"]), ("card", "credit"))

    def test_bank_row_gets_account_kind_bank_and_bank_kind(self):
        rent = self._by_id("RENT")
        self.assertEqual(rent["account_kind"], "bank")
        self.assertEqual(rent["bank_kind"], "landlord_rent")

    def test_couple_transfer_bank_kind(self):
        self.assertEqual(self._by_id("COUPLE")["bank_kind"], "couple_transfer")

    def test_salary_bank_kind(self):
        self.assertEqual(self._by_id("SALARY")["bank_kind"], "salary")

    def test_foreign_flagged(self):
        self.assertTrue(self._by_id("FOREIGN")["foreign"])

    def test_contract_keys_present(self):
        g = self._by_id("GROCERY")
        for k in ("owner","card","source","tx_date","bill_date","merchant","category",
                  "amount","currency","orig_amount","orig_currency","sub_type","notes","foreign","id"):
            self.assertIn(k, g)

if __name__ == "__main__":
    unittest.main()
