import unittest, pathlib, tempfile, json
from engine import refresh

class RefreshTest(unittest.TestCase):
    def test_preflight_fails_when_env_not_ignored(self):
        d = pathlib.Path(tempfile.mkdtemp())
        ok, msg = refresh.preflight(repo_root=d)
        self.assertFalse(ok)

    def test_promote_is_all_or_nothing(self):
        out = pathlib.Path(tempfile.mkdtemp())
        snaps = {"person_a": {"transactions": [{"id": "X", "amount": -1, "date": "2026-02-01"}]},
                 "person_b": None}
        with self.assertRaises(refresh.PartialPullError):
            refresh.promote(out, snaps, meta={"limit": 2000})
        self.assertFalse((out / "snapshot" / "person_a.json").exists())

    def test_truncation_guard(self):
        rows = [{"id": str(i), "amount": -1, "date": "2026-02-01"} for i in range(2000)]
        with self.assertRaises(refresh.TruncationError):
            refresh.check_truncation(rows, limit=2000)

if __name__ == "__main__":
    unittest.main()
