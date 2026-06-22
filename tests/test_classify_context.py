import unittest, hashlib
from engine import classify_context as cc

class FakeConfig:
    COUPLE_NAME_TOKENS = ["Doe"]; LANDLORD_TOKENS = ["Landlord"]; SALARY_KEYWORDS = ["salary"]
    SELF_TRANSFER_TOKENS = []
    RENT_PER_MONTH_TOTAL = 5400.0; RENT_SETTLEMENT_AMOUNT = 2700.0
    RENTAL_INCOME_AMOUNT = 0.0; SALARY_MIN_AMOUNT = 5000.0

class CtxTest(unittest.TestCase):
    def test_rubric_hash_is_sha256_of_rubric(self):
        self.assertEqual(cc.rubric_hash(), hashlib.sha256(cc.RUBRIC.encode("utf-8")).hexdigest())

    def test_rubric_is_data_free(self):
        for token in ("Doe", "Landlord", "5400"):
            self.assertNotIn(token, cc.RUBRIC)

    def test_build_context_injects_runtime_config(self):
        ctx = cc.build_context(FakeConfig)
        self.assertEqual(ctx["amount_constants"]["rent_total"], 5400.0)
        self.assertIn("Landlord", ctx["name_tokens"]["landlord"])

    def test_build_input_shape(self):
        tx = {"id": "X", "owner": "person_a", "merchant": "m", "amount": 10.0,
              "sub_type": "debit", "moneytor_category": "C", "type": "CREDIT", "extra_info": ""}
        item = cc.build_input(tx, decided_siblings=[])
        for field in ("id", "merchant", "signed_direction", "decision_schema"):
            self.assertIn(field, item)
        self.assertEqual(set(item["decision_schema"]["status"]), set(cc.STATUS_VALUES))

if __name__ == "__main__":
    unittest.main()
