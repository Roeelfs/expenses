import unittest, json, shutil, pathlib, tempfile
import tests.config_example_shim as C
from engine import analyze

class BuildTest(unittest.TestCase):
    def setUp(self):
        analyze.C = C
        self.out = pathlib.Path(tempfile.mkdtemp())
        (self.out / "snapshot").mkdir()
        for p in ("person_a", "person_b"):
            shutil.copy(f"tests/fixtures/moneytor_{p}.json", self.out / "snapshot" / f"{p}.json")
        analyze.OUTDIR = self.out

    def test_load_all_reads_snapshots_owner_tagged(self):
        txs = analyze.load_all()
        owners = {t["owner"] for t in txs}
        self.assertEqual(owners, {"person_a", "person_b"})

    def test_owner_id_keeps_colliding_ids_separate(self):
        txs = [t for t in analyze.load_all() if t["id"].endswith("GROCERY")]
        keys = {f"{t['owner']}:{t['id']}" for t in txs}
        self.assertEqual(len(keys), len(txs))
        self.assertEqual(len(txs), 2)

if __name__ == "__main__":
    unittest.main()
