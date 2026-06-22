import json, os, unittest, tempfile, pathlib
from engine import store

SAMPLE_TX = {
    "id": "01AAAA000000000000000GROCERY", "owner": "person_a", "date": "2026-02-01",
    "amount": 250.50, "currency": "ILS", "merchant": "סופרמרקט הדוגמה", "extra_info": "",
    "moneytor_category": "CREDIT_CARD_CHECKING", "type": "CREDIT", "accountId": "CARD-A1",
    "bank_kind": "",
}

class StoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = pathlib.Path(self.dir) / "decisions.json"

    def test_key_is_owner_id(self):
        self.assertEqual(store.key(SAMPLE_TX), "person_a:01AAAA000000000000000GROCERY")

    def test_src_hash_ignores_post_classification_fields(self):
        h1 = store.src_hash(SAMPLE_TX)
        h2 = store.src_hash({**SAMPLE_TX, "tag": "grocery", "status": "shared", "category": "מכולת"})
        self.assertEqual(h1, h2)

    def test_src_hash_changes_on_amount(self):
        self.assertNotEqual(store.src_hash(SAMPLE_TX), store.src_hash({**SAMPLE_TX, "amount": 251.0}))

    def test_atomic_write_then_load_roundtrip(self):
        s = store.load(self.path)
        store.put_decision(s, SAMPLE_TX, status="shared", tag="grocery", reason="r", decided_by="rule", rubric_hash="RH")
        store.save(self.path, s)
        self.assertEqual(store.load(self.path)["person_a:01AAAA000000000000000GROCERY"]["status"], "shared")
        self.assertEqual([p.name for p in pathlib.Path(self.dir).glob("*.tmp*")], [])

    def test_lookup_frozen_human_returned_on_hash_match(self):
        s = {}
        store.put_decision(s, SAMPLE_TX, status="personal", tag="x", reason="r", decided_by="human", rubric_hash="RH")
        d = store.lookup(s, SAMPLE_TX, rubric_hash="RH", retune=True)
        self.assertEqual((d["status"], d["decided_by"]), ("personal", "human"))

    def test_lookup_requeues_on_src_drift(self):
        s = {}
        store.put_decision(s, SAMPLE_TX, status="personal", tag="x", reason="r", decided_by="human", rubric_hash="RH")
        drifted = {**SAMPLE_TX, "amount": 999.0}
        self.assertIsNone(store.lookup(s, drifted, rubric_hash="RH", retune=False))
        self.assertEqual(s[store.key(drifted)]["extra"]["prior"]["status"], "personal")

    def test_lookup_requeues_on_rubric_change(self):
        s = {}
        store.put_decision(s, SAMPLE_TX, status="personal", tag="x", reason="r", decided_by="llm", rubric_hash="OLD")
        self.assertIsNone(store.lookup(s, SAMPLE_TX, rubric_hash="NEW", retune=False))

    def test_rule_record_reused_unless_retune(self):
        s = {}
        store.put_decision(s, SAMPLE_TX, status="shared", tag="grocery", reason="r", decided_by="rule", rubric_hash="RH")
        self.assertIsNotNone(store.lookup(s, SAMPLE_TX, rubric_hash="RH", retune=False))
        self.assertIsNone(store.lookup(s, SAMPLE_TX, rubric_hash="RH", retune=True))

if __name__ == "__main__":
    unittest.main()
