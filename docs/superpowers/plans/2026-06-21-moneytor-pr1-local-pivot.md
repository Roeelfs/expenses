# Moneytor PR1 — Local Pivot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the file-glob/parser front end of the expense engine with a local Moneytor API ingest + a reason-once classification store, keeping `render.py`'s output identical, and deleting the file parsers only after a real-data feasibility gate.

**Architecture:** `refresh.py` (the only networked code) pulls both people from Moneytor → atomic per-person snapshots → upserts a local `output/decisions.json` (keyed `owner:id`) → regex first-pass → residue handed to the Claude Code harness → `analyze.py` builds the report offline from the snapshot joined to the store. A one-method source-adapter seam (`Source.kind`) keeps everything downstream vendor-agnostic.

**Tech Stack:** Python 3 + stdlib only (`urllib`, `json`, `hashlib`, `os`, `tempfile`, `unittest`) + the existing `openpyxl` (deleted at the end with the parsers). No new runtime dependency, no build step. Tests use stdlib `unittest`; fixtures are **synthetic** (invented merchants/amounts — never real data, per Rule Zero).

**Spec:** [docs/superpowers/specs/2026-06-21-moneytor-integration-design.md](../specs/2026-06-21-moneytor-integration-design.md). Section refs (§N) below point there.

---

## Conventions for every task

- **Commit messages:** `<type>(expenses): <desc>` and append the session trailer:
  `git commit -m "..." --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"`
- **Run tests:** `python3 -m unittest discover -s tests -v` (or a single module: `python3 -m unittest tests.test_store -v`).
- **Rule Zero before every commit:** `git status` must show no `config.py`, no `.env`, no `output/`, no real name/amount/token. Task 1 lands the `.gitignore` rules that make this safe — **do Task 1 first**.
- **Never** put a real Moneytor token, bank credential, or real merchant/amount in any committed file (code, test, fixture, doc). Fixtures use the synthetic tokens already in `config.example.py` (`COUPLE_NAME_TOKENS=["Doe"]`, `LANDLORD_TOKENS=["Landlord"]`, `SALARY_KEYWORDS=["salary"]`).

## File structure (what each file owns)

| File | New/Mod | Responsibility |
|---|---|---|
| `.gitignore` | Mod | Ignore `.env*`, un-anchored financial formats, narrow `sample-data/**` (§7) |
| `.env.example` | New | Placeholder token var NAMES only (committed, never real values) |
| `tests/` + `tests/fixtures/` | New | stdlib `unittest` suite + synthetic Moneytor-shaped JSON |
| `engine/store.py` | New | `decisions.json` store: atomic write, `owner:id` key, `src_hash`, `rubric_hash`, freeze/drift (§4.3) |
| `engine/classify_context.py` | New | `RUBRIC`, output JSON schema, `build_context`, `build_input` (§5.4) |
| `engine/moneytor.py` | New | stdlib HTTP client: host-pinned HTTPS, no-redirect, error mapping (§4.1, §7) |
| `engine/refresh.py` | New | `--preflight`, `--pull` (all-or-nothing + truncation guard), regex first-pass→`residue.json`, `--record`, `--gate` (§3.1, §4.4, §8) |
| `engine/analyze.py` | Mod | `map_moneytor`/`_derive_bank_kind`/`account_kind`; `load_all` from snapshot; `classify_deterministic` re-grounded; `classify_one`/`classify_all`; refund branch; bank gate on `bank_kind`; CSV→debug; **delete parsers (Task 14)** |
| `engine/render.py` | Mod | category-from-`tag`, re-key donut + car breakdown off `tag`, inline Chart.js+fonts (§5.3, §9) |
| `config.example.py` | Mod | `Source(kind, token_env, account)`; remove globs; add `STORE_PATH`/snapshot dir |
| `.claude/skills/refresh/SKILL.md` | New | `/refresh` orchestration runbook |
| `.claude/agents/classification-reasoner.md` | New (rename) | Renamed from `classification-tuner`; reasons over `residue.json` |

---

## Task 1: Rule Zero hardening — land `.gitignore` + `.env.example` FIRST

**Files:**
- Modify: `.gitignore`
- Create: `.env.example`

- [ ] **Step 1: Add the ignore rules.** Append to `.gitignore`:

```gitignore
# ── Moneytor pivot: secrets + new financial formats (Rule Zero) ──
/.env
.env*
!/.env.example
# un-anchored: catch the new financial artifacts ANYWHERE, not just under output/
decisions*.json
snapshot*.json
residue*.json
report.html
meta.json
/deploy/**/*.html
/deploy/**/*.json
```

- [ ] **Step 2: Narrow the `sample-data/**` whitelist.** In `.gitignore`, find the line `!sample-data/**` and replace it with an explicit synthetic-only allowlist:

```gitignore
# sample-data holds ONLY synthetic fixtures — never a real snapshot/export
!/sample-data/generate.py
!/sample-data/person_a/
!/sample-data/person_b/
!/sample-data/person_a/**
!/sample-data/person_b/**
```

- [ ] **Step 3: Create `.env.example`** with NAMES only and a loud header:

```bash
# .env.example — COMMITTED TEMPLATE. NEVER put a real token here.
# Copy to .env (gitignored) and fill real per-person Moneytor JWTs there.
#   cp .env.example .env
MONEYTOR_TOKEN_PERSON_A=
MONEYTOR_TOKEN_PERSON_B=
```

- [ ] **Step 4: Verify the rules work.**

Run: `touch .env && git check-ignore .env .env.example decisions.json output/snapshot/x.json engine/residue.json 2>&1; rm .env`
Expected: `.env`, `decisions.json`, `output/snapshot/x.json`, `engine/residue.json` are listed (ignored); `.env.example` is NOT listed (tracked).

- [ ] **Step 5 (optional, defense-in-depth, §7):** add a `gitleaks` pre-commit hook with a custom Moneytor-JWT rule (the bespoke `eyJ…` grep in Task 10's preflight is the primary local guard; gitleaks + GitHub push-protection are belt-and-suspenders). Skip if `gitleaks` isn't installed — not a blocker for PR1.

- [ ] **Step 6: Commit.**

```bash
git add .gitignore .env.example
git commit -m "chore(expenses): rule-zero gitignore for tokens + new financial formats" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Test harness + synthetic Moneytor fixtures

**Files:**
- Create: `tests/__init__.py` (empty)
- Create: `tests/fixtures/moneytor_person_a.json`
- Create: `tests/fixtures/moneytor_person_b.json`

- [ ] **Step 1: Create `tests/__init__.py`** (empty file, makes `tests` a package).

- [ ] **Step 2: Create `tests/fixtures/moneytor_person_a.json`** — synthetic, covers every branch the engine must handle (grocery, fuel, salary credit, rent debit to landlord, couple-transfer, card refund, foreign, ambiguous):

```json
{
  "ok": true,
  "asOf": "2026-02-10T00:00:00.000Z",
  "baseCurrency": "ILS",
  "transactions": [
    {"id": "01AAAA000000000000000GROCERY", "date": "2026-02-01", "amount": -250.50, "currency": "ILS", "description": "סופרמרקט הדוגמה", "extra_info": null, "category": "CREDIT_CARD_CHECKING", "accountId": "CARD-A1", "type": "CREDIT"},
    {"id": "01AAAA000000000000000000FUEL", "date": "2026-02-02", "amount": -300.00, "currency": "ILS", "description": "פז דוגמה", "extra_info": null, "category": "CREDIT_CARD_CHECKING", "accountId": "CARD-A1", "type": "CREDIT"},
    {"id": "01AAAA0000000000000000SALARY", "date": "2026-02-05", "amount": 12000.00, "currency": "ILS", "description": "salary example-employer", "extra_info": null, "category": "BANK_TRANSFER", "accountId": "BANK-A1", "type": "CHECKING"},
    {"id": "01AAAA00000000000000000RENT", "date": "2026-02-03", "amount": -5400.00, "currency": "ILS", "description": "Landlord", "extra_info": "שיק", "category": "BANK_TRANSFER", "accountId": "BANK-A1", "type": "CHECKING"},
    {"id": "01AAAA000000000000000COUPLE", "date": "2026-02-06", "amount": -2700.00, "currency": "ILS", "description": "Doe", "extra_info": "BIT", "category": "BANK_TRANSFER", "accountId": "BANK-A1", "type": "CHECKING"},
    {"id": "01AAAA00000000000000REFUND", "date": "2026-02-07", "amount": 80.00, "currency": "ILS", "description": "סופרמרקט הדוגמה זיכוי", "extra_info": null, "category": "CREDIT_CARD_CHECKING", "accountId": "CARD-A1", "type": "CREDIT"},
    {"id": "01AAAA0000000000000FOREIGN", "date": "2026-02-08", "amount": -40.00, "currency": "USD", "description": "EXAMPLE SAAS", "extra_info": null, "category": "CREDIT_CARD_CHECKING", "accountId": "CARD-A1", "type": "CREDIT"},
    {"id": "01AAAA00000000000000ZERO", "date": "2026-02-09", "amount": 0.0, "currency": "ILS", "description": "ignore me", "extra_info": null, "category": "CREDIT_CARD_CHECKING", "accountId": "CARD-A1", "type": "CREDIT"}
  ]
}
```

- [ ] **Step 3: Create `tests/fixtures/moneytor_person_b.json`** — same shape, `id` prefix `01BBBB…`, a couple of synthetic rows (one grocery `-120.00 "מכולת דוגמה"`, one salary `+9000 "salary other-employer"`). Use distinct ids from person_a but **deliberately reuse one suffix** to test the `owner:id` collision guard: include `{"id": "01AAAA000000000000000GROCERY", ...}` with a DIFFERENT amount `-99.00` so Task 3's test proves `owner:id` keeps them separate.

- [ ] **Step 4: Commit.**

```bash
git add tests/__init__.py tests/fixtures/
git commit -m "test(expenses): synthetic moneytor fixtures + test package" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: `engine/store.py` — atomic decisions store (§4.3)

**Files:**
- Create: `engine/store.py`
- Test: `tests/test_store.py`

- [ ] **Step 1: Write the failing test** (`tests/test_store.py`):

```python
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
        self.assertEqual(h1, h2)  # tag/status/derived-category must NOT change the hash

    def test_src_hash_changes_on_amount(self):
        self.assertNotEqual(store.src_hash(SAMPLE_TX), store.src_hash({**SAMPLE_TX, "amount": 251.0}))

    def test_atomic_write_then_load_roundtrip(self):
        s = store.load(self.path)
        store.put_decision(s, SAMPLE_TX, status="shared", tag="grocery", reason="r", decided_by="rule", rubric_hash="RH")
        store.save(self.path, s)
        self.assertEqual(store.load(self.path)["person_a:01AAAA000000000000000GROCERY"]["status"], "shared")
        # atomic: no leftover temp files in the dir
        self.assertEqual([p.name for p in pathlib.Path(self.dir).glob("*.tmp*")], [])

    def test_lookup_frozen_human_returned_on_hash_match(self):
        s = {}
        store.put_decision(s, SAMPLE_TX, status="personal", tag="x", reason="r", decided_by="human", rubric_hash="RH")
        d = store.lookup(s, SAMPLE_TX, rubric_hash="RH", retune=True)  # retune must NOT touch human
        self.assertEqual((d["status"], d["decided_by"]), ("personal", "human"))

    def test_lookup_requeues_on_src_drift(self):
        s = {}
        store.put_decision(s, SAMPLE_TX, status="personal", tag="x", reason="r", decided_by="human", rubric_hash="RH")
        drifted = {**SAMPLE_TX, "amount": 999.0}
        self.assertIsNone(store.lookup(s, drifted, rubric_hash="RH", retune=False))  # drift -> re-queue
        # prior decision retained as evidence
        self.assertEqual(s[store.key(drifted)]["extra"]["prior"]["status"], "personal")

    def test_lookup_requeues_on_rubric_change(self):
        s = {}
        store.put_decision(s, SAMPLE_TX, status="personal", tag="x", reason="r", decided_by="llm", rubric_hash="OLD")
        self.assertIsNone(store.lookup(s, SAMPLE_TX, rubric_hash="NEW", retune=False))

    def test_rule_record_reused_unless_retune(self):
        s = {}
        store.put_decision(s, SAMPLE_TX, status="shared", tag="grocery", reason="r", decided_by="rule", rubric_hash="RH")
        self.assertIsNotNone(store.lookup(s, SAMPLE_TX, rubric_hash="RH", retune=False))  # reused
        self.assertIsNone(store.lookup(s, SAMPLE_TX, rubric_hash="RH", retune=True))      # re-run on retune

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it, verify it fails.** Run: `python3 -m unittest tests.test_store -v` → Expected: FAIL (`No module named 'engine.store'`).

- [ ] **Step 3: Implement `engine/store.py`:**

```python
"""Persisted classification store (decisions.json). Source of truth, keyed owner:id.

Atomic writes only; one freeze/drift rule; src_hash over RAW source fields only.
See spec §4.3.
"""
from __future__ import annotations
import json, os, hashlib, tempfile
from datetime import date
from pathlib import Path

# RAW source fields only — NEVER post-classification fields (tag/status/derived category).
_HASH_FIELDS = ("id", "owner", "date", "amount", "currency", "merchant",
                "extra_info", "moneytor_category", "type", "accountId", "bank_kind")


def key(tx: dict) -> str:
    return f"{tx['owner']}:{tx['id']}"


def src_hash(tx: dict) -> str:
    sub = {k: tx.get(k, "") for k in _HASH_FIELDS}
    blob = json.dumps(sub, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load(path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def save(path, store: dict) -> None:
    """Atomic: write a same-dir temp file, fsync, os.replace. Never write in place."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=p.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=0)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
        dirfd = os.open(str(p.parent), os.O_RDONLY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def put_decision(store: dict, tx: dict, *, status, tag, reason, decided_by,
                 rubric_hash, extra=None) -> None:
    rec = {
        "status": status, "tag": tag, "reason": reason, "decided_by": decided_by,
        "decided_at": date.today().isoformat(),
        "src_hash": src_hash(tx), "rubric_hash": rubric_hash,
        "extra": dict(extra or {}),
    }
    store[key(tx)] = rec


def lookup(store: dict, tx: dict, *, rubric_hash, retune=False):
    """Return the stored decision if valid, else None (caller re-queues).

    Valid iff src_hash AND rubric_hash match. On drift, the prior decision is
    retained in extra.prior as evidence and None is returned. rule records are
    re-run (None) under retune; llm/human are never re-run by retune.
    """
    rec = store.get(key(tx))
    if rec is None:
        return None
    drift = rec["src_hash"] != src_hash(tx) or rec.get("rubric_hash") != rubric_hash
    if drift:
        rec.setdefault("extra", {}).setdefault("prior", {
            "status": rec["status"], "tag": rec["tag"], "reason": rec["reason"],
            "decided_by": rec["decided_by"],
        })
        return None  # re-queue
    if rec["decided_by"] == "rule" and retune:
        return None  # re-run rules
    return rec
```

- [ ] **Step 4: Run tests, verify pass.** Run: `python3 -m unittest tests.test_store -v` → Expected: PASS (8 tests).

- [ ] **Step 5: Commit.**

```bash
git add engine/store.py tests/test_store.py
git commit -m "feat(expenses): atomic decisions store keyed owner:id with freeze/drift rule" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: `engine/classify_context.py` — reasoning contract + `rubric_hash` (§5.4)

**Files:**
- Create: `engine/classify_context.py`
- Test: `tests/test_classify_context.py`

- [ ] **Step 1: Write the failing test:**

```python
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
        for token in ("Doe", "Landlord", "5400"):  # no real config values baked into the committed rubric
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
        self.assertEqual(set(item["decision_schema"]["status"]),
                         set(cc.STATUS_VALUES))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it, verify it fails.** Run: `python3 -m unittest tests.test_classify_context -v` → Expected: FAIL (import error).

- [ ] **Step 3: Implement `engine/classify_context.py`:**

```python
"""The LLM reasoning contract: a committed data-free RUBRIC, the output schema,
and runtime builders that inject real config.py amounts/tokens (NEVER committed).
See spec §5.4. The RUBRIC's hash is the store's rubric_hash invalidation key.
"""
from __future__ import annotations
import hashlib

STATUS_VALUES = ["shared", "personal", "rent", "landlord_rent", "restaurant",
                 "vacation", "business", "loan", "earnings", "rental_income",
                 "transfer", "refund", "flag"]

# Data-free taxonomy. Contains NO real names/amounts. Edit deliberately — its hash
# invalidates frozen decisions (rubric_hash).
RUBRIC = """\
You classify ONE Israeli household transaction into {status, tag, reason, category}.
status is one of: shared, personal, rent, landlord_rent, restaurant, vacation,
business, loan, earnings, rental_income, transfer, refund, flag.
- shared: split 50/50 (groceries, utilities, household, furniture).
- personal: stays with the payer (fuel, phone, gym, subscriptions, vehicle, fashion, pharmacy).
- landlord_rent / rent: rent paid to the landlord / a settlement transfer between the couple.
- restaurant, vacation: pooled and shown, not split.
- business: one person's work tools (SaaS/dev/AI).
- earnings / rental_income: bank credits (income side).
- transfer: Bit/PayBox/ATM/fees/inter-account moves (excluded from spend).
- refund: a credit on a card account that reverses prior spend (excluded from spend).
- flag: cannot decide — surface for a human.
Use the provided name tokens and amount constants to disambiguate landlord_rent vs a
couple transfer (often the same counterparty, differing only by amount). Prefer the
already-decided sibling examples for consistency. If unsure, return status='flag'.
"""


def rubric_hash() -> str:
    return hashlib.sha256(RUBRIC.encode("utf-8")).hexdigest()


def build_context(config) -> dict:
    """Render runtime config (real amounts/tokens) — never committed, never logged raw."""
    return {
        "name_tokens": {
            "couple": list(config.COUPLE_NAME_TOKENS),
            "landlord": list(config.LANDLORD_TOKENS),
            "salary": list(config.SALARY_KEYWORDS),
            "self_transfer": list(getattr(config, "SELF_TRANSFER_TOKENS", [])),
        },
        "amount_constants": {
            "rent_total": config.RENT_PER_MONTH_TOTAL,
            "rent_settlement": config.RENT_SETTLEMENT_AMOUNT,
            "rental_income": config.RENTAL_INCOME_AMOUNT,
            "salary_min": config.SALARY_MIN_AMOUNT,
        },
    }


def build_input(tx: dict, decided_siblings: list[dict]) -> dict:
    return {
        "id": tx["id"], "owner": tx.get("owner"),
        "merchant": tx.get("merchant", ""), "extra_info": tx.get("extra_info", ""),
        "amount": tx.get("amount"), "signed_direction": tx.get("sub_type", ""),
        "moneytor_category": tx.get("moneytor_category", ""), "type": tx.get("type", ""),
        "siblings": decided_siblings[:5],
        "decision_schema": {"status": STATUS_VALUES, "tag": "string", "reason": "string",
                            "category": "string (Hebrew display label)"},
    }
```

- [ ] **Step 4: Run tests, verify pass.** Run: `python3 -m unittest tests.test_classify_context -v` → Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add engine/classify_context.py tests/test_classify_context.py
git commit -m "feat(expenses): classify_context rubric + runtime builders + rubric_hash" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: `engine/moneytor.py` — HTTP client (§4.1, §7)

**Files:**
- Create: `engine/moneytor.py`
- Test: `tests/test_moneytor.py`

- [ ] **Step 1: Write the failing test** (uses a stdlib `http.server` on localhost — no real network/token):

```python
import unittest, threading, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from engine import moneytor

class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "Authorization" not in self.headers:
            self.send_response(401); self.end_headers(); self.wfile.write(b'{"ok":false}'); return
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "transactions": [{"id": "X", "amount": -5, "date": "2026-02-01"}]}).encode())
    def log_message(self, *a): pass

class MoneytorTest(unittest.TestCase):
    def test_rejects_non_https_base(self):
        with self.assertRaises(moneytor.MoneytorError):
            moneytor.fetch_transactions("http://app.moneytor.co.il/api/v1", "tok", "2026-02-01", "2026-02-28")

    def test_rejects_wrong_host(self):
        with self.assertRaises(moneytor.MoneytorError):
            moneytor.fetch_transactions("https://evil.example.com/api/v1", "tok", "2026-02-01", "2026-02-28")

    def test_parses_transactions_from_a_local_server(self):
        srv = HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}/api/v1"  # localhost test bypasses host/https pin
        rows = moneytor._fetch_raw(base, "tok", "2026-02-01", "2026-02-28", limit=2000)
        srv.shutdown()
        self.assertEqual(rows[0]["id"], "X")

    def test_maps_401_to_expired_error(self):
        srv = HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}/api/v1"
        with self.assertRaises(moneytor.MoneytorAuthError):
            moneytor._fetch_raw(base, None, "2026-02-01", "2026-02-28", limit=2000)
        srv.shutdown()

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it, verify it fails.** Run: `python3 -m unittest tests.test_moneytor -v` → Expected: FAIL (import error).

- [ ] **Step 3: Implement `engine/moneytor.py`:**

```python
"""Moneytor HTTP client (stdlib only). Host-pinned HTTPS, no redirects, token never
logged. fetch_transactions() enforces the security pins; _fetch_raw() is the inner
call (localhost-testable). See spec §4.1, §7.
"""
from __future__ import annotations
import json, urllib.request, urllib.error
from urllib.parse import urlencode, urlsplit

ALLOWED_HOST = "app.moneytor.co.il"


class MoneytorError(Exception): pass
class MoneytorAuthError(MoneytorError): pass          # 401/403
class MoneytorRateLimit(MoneytorError): pass          # 429


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        raise MoneytorError("refusing to follow a redirect (token must not cross origins)")


def _fetch_raw(base_url: str, token, frm: str, to: str, limit: int) -> list[dict]:
    qs = urlencode({"from": frm, "to": to, "limit": limit})
    url = f"{base_url}/transactions?{qs}"
    req = urllib.request.Request(url, method="GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise MoneytorAuthError(f"Moneytor auth failed ({e.code}); token expired or not Premium")
        if e.code == 429:
            raise MoneytorRateLimit(f"rate limited; Retry-After={e.headers.get('Retry-After')}")
        raise MoneytorError(f"HTTP {e.code}")
    if not body.get("ok", True):
        raise MoneytorAuthError("Moneytor returned ok=false")
    return body.get("transactions", [])


def fetch_transactions(base_url: str, token: str, frm: str, to: str, limit: int = 2000) -> list[dict]:
    parts = urlsplit(base_url)
    if parts.scheme != "https":
        raise MoneytorError(f"refusing non-HTTPS base URL: {base_url}")
    if parts.hostname != ALLOWED_HOST:
        raise MoneytorError(f"refusing unexpected host: {parts.hostname}")
    return _fetch_raw(base_url, token, frm, to, limit)
```

- [ ] **Step 4: Run tests, verify pass.** Run: `python3 -m unittest tests.test_moneytor -v` → Expected: PASS (4 tests).

- [ ] **Step 5: Commit.**

```bash
git add engine/moneytor.py tests/test_moneytor.py
git commit -m "feat(expenses): host-pinned https moneytor client, no redirects" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: `map_moneytor` + `account_kind` + `_derive_bank_kind` in `analyze.py` (§4.2, §6 #1/#8/#9)

**Files:**
- Modify: `engine/analyze.py` (add functions near the existing helpers; do NOT touch the loaders yet)
- Test: `tests/test_map_moneytor.py`

- [ ] **Step 1: Write the failing test:**

```python
import json, unittest, pathlib, importlib
import config_example_shim as C  # see Step 3 note; or import the real config in CI
from engine import analyze

FIX = pathlib.Path("tests/fixtures/moneytor_person_a.json")

class MapTest(unittest.TestCase):
    def setUp(self):
        analyze.C = C  # inject synthetic config (PERIOD covers 2026-02)
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
        self.assertEqual(rent["bank_kind"], "landlord_rent")  # Landlord token + exact rent amount

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
```

> Note for Step 1: create `tests/config_example_shim.py` that imports everything from `config.example.py` but overrides `PERIOD_START=date(2026,2,1)`, `PERIOD_END=date(2026,2,28)` so the synthetic Feb fixtures fall in-window. (Tests must never import a real `config.py`.)

- [ ] **Step 2: Run it, verify it fails.** Run: `python3 -m unittest tests.test_map_moneytor -v` → Expected: FAIL (`map_moneytor` missing).

- [ ] **Step 3: Implement in `engine/analyze.py`** (add after `parse_amount`/`strip_rtl`, reuse the existing `_has_token`):

```python
import json as _json
from datetime import date as _date

# Moneytor account-kind discriminator (replaces the source-string allowlist).
_BANK_TYPES = {"CHECKING", "SAVINGS", "BANK"}
_BANK_CATEGORIES = {"BANK_TRANSFER"}

def _account_kind(raw: dict) -> str:
    if raw.get("type", "").upper() in _BANK_TYPES or raw.get("category", "") in _BANK_CATEGORIES:
        return "bank"
    return "card"

def _derive_bank_kind(merchant: str, signed: float, raw: dict) -> str:
    """Consolidated bank_kind logic (formerly duplicated across 3 loaders). Tolerance
    on all amount comparisons. Re-tune the cheque tokens against REAL Moneytor strings
    at the feasibility gate (§6 #3)."""
    desc = f"{merchant} {raw.get('extra_info') or ''}"
    is_debit = signed < 0
    amt = abs(signed)
    rent_total = getattr(C, "RENT_PER_MONTH_TOTAL", 0.0)
    rent_settle = getattr(C, "RENT_SETTLEMENT_AMOUNT", 0.0)
    rental_income = getattr(C, "RENTAL_INCOME_AMOUNT", 0.0)
    def near(a, b): return b and abs(a - b) < 0.01
    if is_debit and _has_token(desc, C.LANDLORD_TOKENS) and (near(amt, rent_total) or "שיק" in desc):
        return "landlord_rent"
    if "שיק" in desc and "עבר זמ" in desc:
        return "non_income_credit"
    if not is_debit and _has_token(desc, C.SALARY_KEYWORDS) and amt >= getattr(C, "SALARY_MIN_AMOUNT", 0):
        return "salary"
    if not is_debit and rental_income and near(amt, rental_income):
        return "rental_income"
    if _has_token(desc, C.COUPLE_NAME_TOKENS):
        return "couple_transfer"
    if _has_token(desc, getattr(C, "SELF_TRANSFER_TOKENS", [])):
        return "non_income_credit"
    return "other"

def map_moneytor(raw: dict, owner: str) -> dict | None:
    d = parse_date_he(raw["date"]) if not raw["date"][:4].isdigit() else _date.fromisoformat(raw["date"][:10])
    if d is None or not (C.PERIOD_START <= d <= C.PERIOD_END):
        return None
    signed = float(raw["amount"])
    if signed == 0:
        return None
    merchant = strip_rtl(raw.get("description") or "")
    acct = _account_kind(raw)
    currency = raw.get("currency", "ILS")
    tx = {
        "id": raw["id"], "owner": owner,
        "card": raw.get("accountId", ""),
        "source": "moneytor", "account_kind": acct,
        "tx_date": d.isoformat(), "bill_date": d.isoformat(),
        "merchant": merchant, "category": "",        # display category derived from tag post-classify
        "moneytor_category": raw.get("category", ""), "type": raw.get("type", ""),
        "amount": abs(signed),
        "currency": "₪" if currency == "ILS" else currency,
        "orig_amount": abs(signed), "orig_currency": currency,
        "sub_type": "credit" if signed > 0 else "debit",
        "notes": raw.get("extra_info") or "",
        "foreign": currency != "ILS",
    }
    if acct == "bank":
        tx["bank_kind"] = _derive_bank_kind(merchant, signed, raw)
    return tx
```

- [ ] **Step 4: Run tests, verify pass.** Run: `python3 -m unittest tests.test_map_moneytor -v` → Expected: PASS (9 tests).

- [ ] **Step 5: Commit.**

```bash
git add engine/analyze.py tests/test_map_moneytor.py tests/config_example_shim.py
git commit -m "feat(expenses): map_moneytor adapter + account_kind + consolidated bank_kind" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Re-ground `classify_deterministic` + bank gate + refund branch + `classify_one`/`classify_all` (§5.1, §6 #1/#2/#4)

**Files:**
- Modify: `engine/analyze.py`
- Test: `tests/test_classify.py`

- [ ] **Step 1: Write the failing test:**

```python
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
        # salary credit must reach the bank block -> status 'earnings' (NOT card cascade)
        d = analyze.classify_deterministic(self._m("SALARY"))
        self.assertEqual(d["status"], "earnings")

    def test_landlord_rent_classified(self):
        self.assertEqual(analyze.classify_deterministic(self._m("RENT"))["status"], "landlord_rent")

    def test_grocery_by_merchant_regex(self):
        # category='' — must still classify via merchant regex (re-grounded backbone)
        self.assertEqual(analyze.classify_deterministic(self._m("GROCERY"))["status"], "shared")

    def test_card_refund_excluded_from_spend(self):
        d = analyze.classify_deterministic(self._m("REFUND"))
        self.assertEqual(d["status"], "refund")

    def test_foreign_escalates_to_residue(self):
        self.assertIsNone(analyze.classify_deterministic(self._m("FOREIGN")))

    def test_classify_all_two_sweeps_and_residue(self):
        store = {}
        queue = []
        cls = analyze.classify_all(self.txs, store, queue, rubric_hash=cc.rubric_hash())
        # every decided tx is in cls; foreign went to queue
        self.assertIn("01AAAA0000000000000FOREIGN", [t["id"] for t in queue])
        statuses = {t["id"][-6:]: t["status"] for t in cls}
        self.assertEqual(statuses["ROCERY"], "shared")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it, verify it fails.** Run: `python3 -m unittest tests.test_classify -v` → Expected: FAIL.

- [ ] **Step 3: Implement the changes in `engine/analyze.py`:**

  3a. **Rename** the current `def classify(tx)` to `def classify_deterministic(tx)`. Keep its body, then make these edits inside it:

  - **Bank gate** — replace the opening guard `if tx.get('source') in ('leumi-bank','discount-bank'):` with `if tx.get('account_kind') == 'bank':`.
  - **Card refund branch** — at the very top of the function (before the bank gate), add:

```python
    if tx.get('account_kind') == 'card' and tx.get('sub_type') == 'credit':
        return {**tx, 'tag': 'refund', 'status': 'refund', 'reason': 'card credit / refund — excluded from spend'}
```

  - **Re-grounded category rules** — every clause of the form `if category in SHARED_CATEGORIES:` / `PERSONAL_CATEGORIES` / `RESTAURANT_CATEGORIES` / `VACATION_CATEGORIES` / `FURNITURE_CATEGORIES` no longer fires (category is `''`). For each, EITHER fold its members into the corresponding merchant regex (preferred for groceries/pharma/furniture — extend `SHARED_MERCHANT_PATTERNS`, `FURNITURE_MERCHANT_RE`, etc.) OR delete the clause so the tx escalates. Concretely: delete the `category in SHARED_CATEGORIES` clause (groceries now caught by `SHARED_MERCHANT_PATTERNS` which already matches שופרסל/רמי לוי/… and the synthetic `סופרמרקט`), delete `PERSONAL_CATEGORIES`/`RESTAURANT`/`VACATION`/`FURNITURE` category clauses (merchant regexes + LLM residue cover them). Add `סופרמרקט|מכולת` to `SHARED_MERCHANT_PATTERNS` so the synthetic + real grocery strings match by merchant.
  - **Terminal clauses → None** — change the three "give up" returns (`AMBIGUOUS_CATEGORIES`, `tx.get('foreign')`, final uncategorized) to `return None`.

  3b. **Add the dispatcher + driver** at the end of the classify section:

```python
def classify_one(tx: dict, store: dict, queue: list, *, rubric_hash, retune=False):
    from engine import store as _store
    rec = _store.lookup(store, tx, rubric_hash=rubric_hash, retune=retune)
    if rec is not None:
        return {**tx, 'tag': rec['tag'], 'status': rec['status'],
                'reason': rec['reason'], 'decided_by': rec['decided_by'], **rec.get('extra', {})}
    decided = classify_deterministic(tx)
    if decided is not None:
        _store.put_decision(store, tx, status=decided['status'], tag=decided['tag'],
                            reason=decided['reason'], decided_by='rule', rubric_hash=rubric_hash)
        return {**decided, 'decided_by': 'rule'}
    queue.append(tx)
    return None

def classify_all(txs: list, store: dict, queue: list, *, rubric_hash, retune=False, allow_llm=True):
    cls = []
    for tx in txs:
        out = classify_one(tx, store, queue, rubric_hash=rubric_hash, retune=retune)
        if out is not None:
            cls.append(out)
    return cls  # second sweep (post-harness) is the SAME call again; queue is empty then
```

  3c. **`category`-from-`tag`** — add a `TAG_LABELS` dict mapping each engine `tag` → a Hebrew display label, and a helper `display_category(tag)`; the build (Task 8) sets `tx['category'] = display_category(tx['tag'])` after classification so render has data.

- [ ] **Step 4: Run tests, verify pass.** Run: `python3 -m unittest tests.test_classify -v` → Expected: PASS (6 tests).

- [ ] **Step 5: Commit.**

```bash
git add engine/analyze.py tests/test_classify.py
git commit -m "feat(expenses): re-ground classifier on merchant signals, bank_kind gate, refund branch, store-backed driver" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: `load_all` from snapshot + `main()` store integration + CSV demotion (§3, §4.4)

**Files:**
- Modify: `engine/analyze.py` (`load_all`, `main`)
- Test: `tests/test_build.py`

- [ ] **Step 1: Write the failing test:**

```python
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
        analyze.OUTDIR = self.out  # redirect outputs

    def test_load_all_reads_snapshots_owner_tagged(self):
        txs = analyze.load_all()
        owners = {t["owner"] for t in txs}
        self.assertEqual(owners, {"person_a", "person_b"})

    def test_owner_id_keeps_colliding_ids_separate(self):
        # both fixtures share suffix GROCERY with different amounts -> two distinct store keys
        txs = [t for t in analyze.load_all() if t["id"].endswith("GROCERY")]
        keys = {f"{t['owner']}:{t['id']}" for t in txs}
        self.assertEqual(len(keys), len(txs))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it, verify it fails.** Run: `python3 -m unittest tests.test_build -v` → Expected: FAIL.

- [ ] **Step 3: Implement.** In `engine/analyze.py`:

  3a. Replace `load_all()` body with snapshot-reading (delete the glob/dedupe machinery body but keep the function name):

```python
SNAPSHOT_DIR = OUTDIR / 'snapshot'

def load_all() -> list[dict]:
    txs = []
    for person in C.PEOPLE:
        path = (OUTDIR / 'snapshot' / f'{person.id}.json')
        if not path.exists():
            print(f'WARN: no snapshot for {person.id} at {path}', file=sys.stderr); continue
        raw = json.loads(path.read_text(encoding='utf-8')).get('transactions', [])
        for r in raw:
            tx = map_moneytor(r, person.id)
            if tx is not None:
                txs.append(tx)
    return txs
```

  3b. In `main()`: after `load_all()`, build the store-backed classified list:

```python
from engine import store as _store, classify_context as _cc
store_path = OUTDIR / 'decisions.json'
decisions = _store.load(store_path)
queue = []
rh = _cc.rubric_hash()
cls = classify_all(txs, decisions, queue, rubric_hash=rh, allow_llm=False)  # build is offline
_store.save(store_path, decisions)
for t in cls:
    t['category'] = display_category(t.get('tag', ''))   # category-from-tag (§5.3)
```

  3c. **Demote the CSV**: change the `output/transactions.csv` write so it is a derived debug dump emitted at the END of the build (keep the DictWriter, but add the provenance columns and a header comment `# debug export — decisions.json is the source of truth`). Nothing reads it back.

- [ ] **Step 4: Run tests, verify pass.** Run: `python3 -m unittest tests.test_build -v` → Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add engine/analyze.py tests/test_build.py
git commit -m "feat(expenses): build from snapshot + store-backed classification, csv demoted to debug" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9: `render.py` — category-from-tag, donut/car re-key, inline assets (§5.3, §9)

**Files:**
- Modify: `engine/render.py`

- [ ] **Step 1: Re-key the top-categories donut + car breakdown off `tag`.** In `main()` (analyze.py around line 894/831) the `top_cats` aggregation and `CAR_CATEGORIES` filter currently use `t['category']` (Hebrew). Change both to key off `t['tag']`: build a `CAR_TAGS = {'fuel','vehicle','parking',...}` set and aggregate the donut on `display_category(t['tag'])`. (These aggregations live in analyze.py `main()`; render just consumes the passed dicts — confirm render reads the passed `top_cats`/`cars`, not raw category.)

- [ ] **Step 2: Inline Chart.js + fonts.** In `render.py` (the external `<script src>` for Chart.js and the Google-Fonts `<link>` near lines 472/475) replace the CDN references with inlined content: vendor a pinned `Chart.min.js` into `engine/assets/chart.min.js` and read+inline it; replace the Google-Fonts link with a local `@font-face` or a system-font stack. No `https://` may remain in the emitted HTML.

- [ ] **Step 3: Add a guard test** (`tests/test_render_no_cdn.py`): build the report from the fixtures (reuse Task 8 harness), then assert `'https://' not in report_html` and `'cdn' not in report_html.lower()`.

- [ ] **Step 4: Run it.** Run: `python3 -m unittest tests.test_render_no_cdn -v` → Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add engine/render.py engine/assets/ tests/test_render_no_cdn.py
git commit -m "feat(expenses): category-from-tag, tag-keyed donut/car, inline chart.js+fonts (no cdn)" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 10: `engine/refresh.py` — preflight, all-or-nothing pull, record (§3.1, §4.4, §7)

**Files:**
- Create: `engine/refresh.py`
- Test: `tests/test_refresh.py`

- [ ] **Step 1: Write the failing test** (preflight + all-or-nothing + truncation, no real network):

```python
import unittest, pathlib, tempfile, json
from engine import refresh

class RefreshTest(unittest.TestCase):
    def test_preflight_fails_when_env_not_ignored(self):
        # in a temp dir that is NOT a git repo / has no .gitignore, preflight must abort
        d = pathlib.Path(tempfile.mkdtemp())
        ok, msg = refresh.preflight(repo_root=d)
        self.assertFalse(ok)

    def test_promote_is_all_or_nothing(self):
        out = pathlib.Path(tempfile.mkdtemp())
        snaps = {"person_a": {"transactions": [{"id": "X", "amount": -1, "date": "2026-02-01"}]},
                 "person_b": None}  # person_b failed
        with self.assertRaises(refresh.PartialPullError):
            refresh.promote(out, snaps, meta={"limit": 2000})
        self.assertFalse((out / "snapshot" / "person_a.json").exists())  # nothing promoted

    def test_truncation_guard(self):
        rows = [{"id": str(i), "amount": -1, "date": "2026-02-01"} for i in range(2000)]
        with self.assertRaises(refresh.TruncationError):
            refresh.check_truncation(rows, limit=2000)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it, verify it fails.** Run: `python3 -m unittest tests.test_refresh -v` → Expected: FAIL.

- [ ] **Step 3: Implement `engine/refresh.py`** with: `preflight(repo_root)` (runs `git check-ignore .env`, greps `git ls-files` for `eyJ`, returns `(ok, msg)`, aborts before any network); `check_truncation(rows, limit)` (raises `TruncationError` if `len(rows) >= limit`); `pull()` (fetch both people via `moneytor.fetch_transactions` reading tokens from env vars named in `Source.token_env`, into a temp dict, then `promote`); `promote(out, snaps, meta)` (raises `PartialPullError` if any person is None, else atomically writes both `snapshot/<person>.json` + `snapshot/meta.json` via `store.save`); a regex first-pass that writes the residue to `output/residue.json`; `record(json_str)` (validates against `classify_context.STATUS_VALUES`, calls `store.put_decision` with `decided_by='llm'`); and a `__main__` argparse for `--preflight/--pull/--record/--gate`. Reuse `engine.store.save` for atomic writes. Token is read from `os.environ` only — never a CLI arg, never logged.

- [ ] **Step 4: Run tests, verify pass.** Run: `python3 -m unittest tests.test_refresh -v` → Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add engine/refresh.py tests/test_refresh.py
git commit -m "feat(expenses): refresh preflight + all-or-nothing pull + truncation guard + record" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 11: `config.example.py` Source seam + `STORE_PATH` (§4.5, §6 #7)

**Files:**
- Modify: `config.example.py`

- [ ] **Step 1: Replace the `Source` dataclass** with the adapter-seam version:

```python
@dataclass
class Source:
    """One ingest feed for a person. kind selects the adapter (§4.5)."""
    kind: str = "moneytor"            # adapter: 'moneytor' (PR1). 'scraper' later.
    token_env: str = ""               # NAME of the env var holding this person's token
    account: str = ""                 # optional display label
```

- [ ] **Step 2: Update `PEOPLE`** so each person has `sources=[Source(kind="moneytor", token_env="MONEYTOR_TOKEN_PERSON_A")]` (and `_B`), and **remove** `data_dir` glob usage from the comments. Keep `id`/`label`/`color`. Keep the `person_a`/`person_b` ids.

- [ ] **Step 3: Add to section 5 (OUTPUT):**

```python
STORE_PATH   = "output/decisions.json"   # source of truth (gitignored, atomic writes)
SNAPSHOT_DIR = "output/snapshot"         # raw Moneytor pulls (gitignored)
```

- [ ] **Step 4: Verify the engine still imports** with the example config (sanity, no real config.py needed): `python3 -c "import importlib.util,sys; spec=importlib.util.spec_from_file_location('c','config.example.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print(m.PEOPLE[0].sources[0].kind)"` → Expected: `moneytor`.

- [ ] **Step 5: Commit.**

```bash
git add config.example.py
git commit -m "feat(expenses): config source-adapter seam (kind+token_env) + store/snapshot paths" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 12: `/refresh` skill + `classification-reasoner` rename + doc updates

**Files:**
- Create: `.claude/skills/refresh/SKILL.md`
- Rename: `.claude/agents/classification-tuner.md` → `.claude/agents/classification-reasoner.md`
- Modify: `.claude/skills/expense-report/SKILL.md`, `.claude/agents/statement-onboarder.md`, `CLAUDE.md`

- [ ] **Step 1: Create `.claude/skills/refresh/SKILL.md`** — frontmatter `disable-model-invocation: true`, `argument-hint: [--from YYYY-MM-DD] [--no-llm] [--retune] [--publish]`, `allowed-tools: Bash(python3 engine/*.py *)`. Body = the runbook: preflight → `python3 engine/refresh.py --pull` → read `output/residue.json` and reason over each item (write each verdict via `python3 engine/refresh.py --record '<json>'`, large residue → fork the `classification-reasoner` subagent) → `python3 engine/analyze.py` → optional `--publish`.

- [ ] **Step 2: `git mv .claude/agents/classification-tuner.md .claude/agents/classification-reasoner.md`** and rewrite its body to: read `output/residue.json`, classify each tx against the rubric + the `build_context` tokens/amounts, record via `engine/refresh.py --record`. Remove the old "edit transactions.csv / tune regex" framing.

- [ ] **Step 3: Update `.claude/skills/expense-report/SKILL.md` + `statement-onboarder.md` + `CLAUDE.md`** to describe the snapshot+store+`/refresh` flow, not globs+CSV. (CLAUDE.md "Architecture (3 files)" → note the new `engine/` modules + the store; "Classification taxonomy" → note the `refund` status + the store.)

- [ ] **Step 4: Verify** `git status` shows the rename (not delete+add) and no data files. Commit:

```bash
git add -A .claude CLAUDE.md
git commit -m "docs(expenses): /refresh skill, rename tuner->reasoner, snapshot+store docs" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 13: Feasibility gate against REAL data (manual checkpoint — §8) — STOP before Task 14

**Files:**
- Modify: `engine/refresh.py` (`--gate`)
- This task requires real Moneytor tokens + a captured overlap file-statement set. **Do NOT delete parsers until this is green.**

- [ ] **Step 1: Local secrets.** `cp .env.example .env`; fill the two real Moneytor JWTs in `.env` (gitignored). Confirm `git check-ignore .env` prints `.env`.

- [ ] **Step 2: Implement `refresh.py --gate`** to: (a) assert HTTPS reachability; (b) pull the same window twice and assert identical `id` sets + no cross-person `owner:id` collision; (c) run the OLD parser path (still present) and the NEW Moneytor path over the overlap window; (d) diff the final settlement delta — assert within **±₪1 or 0.5%**; (e) assert per-tx `status`/`tag` parity over rule-decided tx only; (f) assert `bank_credits` non-empty and correct `bank_kind` for {landlord, couple-transfer, salary, rental-income, returned-cheque, self-transfer}; (g) assert period-boundary membership parity; (h) assert first-run residue rate ≤ ~⅓.

- [ ] **Step 3: Run the gate.** Run: `python3 engine/refresh.py --gate --from <overlap-start> --to <overlap-end>`
Expected: all assertions PASS and it prints `GATE: GREEN`. **If RED, fix the mapping/rules and re-run — do not proceed.** If no overlap window exists, STOP here: ship PR1 with parsers retained and defer Task 14 to a follow-up (§8).

- [ ] **Step 4: Commit the gate code** (no data):

```bash
git add engine/refresh.py
git commit -m "feat(expenses): feasibility gate — old-vs-new settlement parity before parser deletion" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 14: Delete the file parsers (ONLY on a green gate — §8, §9)

**Files:**
- Modify: `engine/analyze.py` (delete loaders), `requirements`/imports

- [ ] **Step 1: Delete** `load_xlsx_card`, `load_isracard_pdf`, `load_bank_discount_csv`, `load_bank_discount`, `load_bank_leumi`, `_ym_from_name`, the `LOADERS` map, the discount CSV/PDF dedupe, and the now-unused regexes/constants (`TX_LINE_RE`, `EXTRA_LINE_RE`, `XLSX_HEADER_ROW`, `BANK_SKIP_PATTERNS`, `HE_MONTHS`, `UTIL_TX_RE`). Remove `import openpyxl`, the `subprocess`/`pdftotext` calls, and the `glob` import if now unused.

- [ ] **Step 2: Remove the `UTIL_TX_RE` arrears exception** (its removal was decided in §4.2 — utilities judged on the single Moneytor date).

- [ ] **Step 3: Run the full suite + a real build** to confirm nothing references the deleted code: `python3 -m unittest discover -s tests -v` then `python3 engine/analyze.py` (against a real snapshot) → Expected: tests PASS, report builds, no `ImportError`/`NameError`.

- [ ] **Step 4: Rule Zero final scan.** `git status` (no data/config/.env staged); `git grep -nE 'eyJ[A-Za-z0-9_-]{10,}' -- ':!*.example*'` returns nothing.

- [ ] **Step 5: Commit.**

```bash
git add engine/analyze.py
git commit -m "refactor(expenses): delete file parsers — moneytor is the only source (gate green)" --trailer "Session-Id: $CLAUDE_SESSION_ID" --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Done-when (PR1 acceptance)

- `python3 engine/analyze.py` builds `output/report.html` from a Moneytor snapshot joined to `output/decisions.json`, with **zero** parsers and **zero** network on a normal build.
- `/refresh` pulls both people (all-or-nothing), regex-decides the backbone, hands the residue to the harness, persists each decision once by `owner:id`, and rebuilds.
- The feasibility gate was green before any parser was deleted (or parsers retained + deletion deferred if no overlap window).
- No token, credential, or real merchant/amount is in any committed file; `.env`/store/snapshot/residue/report are all gitignored.
