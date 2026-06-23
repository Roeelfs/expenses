# Moneytor integration — session handoff (2026-06-21)

**Read this first if you're a new session picking up this work.** It's the entry
point; the detail lives in the spec + plan linked below.

## TL;DR

We replaced the expense engine's manual bank/card **file-upload** front end with a
**Moneytor API** ingest + a **reason-once classification store**, all local, with a
plan to later serve the report behind a Supabase login. **PR1 (the local engine) is
built, tested, reviewed, and merged to `main`** (`origin/main` @ `f9adfc4`). The
only thing left needs the user's real Moneytor API tokens.

- ✅ **Done & on main:** Tasks 1–12 — the whole token-free engine. 39 unit tests
  pass; the pipeline builds `output/report.html` from Moneytor-shaped snapshots.
- ⏸️ **Blocked on the user:** Tasks 13–14 — the real-data feasibility gate and the
  file-parser deletion. They need the two Moneytor JWTs in a gitignored `.env`.
  The user said they'll provide the API token later.

## Where the durable detail is

| Artifact | Path |
|---|---|
| **Design spec** (hardened: 9-lane spec-review + vendor research applied) | [docs/superpowers/specs/2026-06-21-moneytor-integration-design.md](specs/2026-06-21-moneytor-integration-design.md) |
| **Implementation plan** (14 tasks, TDD, gated deletion) | [docs/superpowers/plans/2026-06-21-moneytor-pr1-local-pivot.md](plans/2026-06-21-moneytor-pr1-local-pivot.md) |
| Auto-memory (status + vendor decision) | `~/.claude/projects/-Users-roeealfasi-Desktop-expenses/memory/moneytor-integration-plan.md` |

## How to resume (Tasks 13–14) — the exact next steps

Tasks 13–14 require the user's two Moneytor Premium JWTs. Once you have them:

```bash
cp .env.example .env
# edit .env, paste the real tokens (file is gitignored — verified):
#   MONEYTOR_TOKEN_PERSON_A=eyJ...
#   MONEYTOR_TOKEN_PERSON_B=eyJ...
python3 engine/refresh.py --preflight   # Rule-Zero gate; must print "ok" + exit 0
python3 engine/refresh.py --pull        # real pull, all-or-nothing, writes output/snapshot/*.json + residue.json
```

**Task 13 — feasibility gate** (plan §Task 13): implement `refresh.py --gate`, then
run it over an overlap window where BOTH the old file statements and a Moneytor pull
exist. Assert (spec §8): two pulls return identical `id` sets; no cross-person
`owner:id` collision; `bank_credits` non-empty; correct `bank_kind` for every rent +
non-income class (landlord, couple-transfer, salary, rental-income, returned-cheque,
self-transfer); **final settlement delta old-vs-new within ±₪1 / 0.5%** (compare per-tx
status/tag over the *deterministic backbone* only — LLM-residue tx legitimately differ);
period-boundary membership parity; residue rate ≤ ~⅓. **If the user has no overlapping
file statements**, the spec's deferred-deletion path applies: keep the parsers, ship,
delete later once an overlap is captured. HTTPS is already verified working
(`http://`→301→`https://`; `https://app.moneytor.co.il/api/v1/transactions` → JSON 401).

**Task 14 — delete the file parsers** (plan §Task 14): ONLY on a green gate. Delete the
five loaders (`load_xlsx_card`, `load_isracard_pdf`, `load_bank_discount_csv`,
`load_bank_discount`, `load_bank_leumi`), the `LOADERS` map, `_ym_from_name`, the
`glob`/`openpyxl`/`pdftotext`(`subprocess`) machinery, and the `SALARY_MERCHANT_RE` /
other now-dead regexes. They are intentionally retained on main until then (they sit
unused — `load_all` reads snapshots, not files).

**The reason-once loop (`/refresh`)** for normal use once tokens exist: `preflight` →
`refresh.py --pull` (writes `output/residue.json`) → the harness reads `residue.json`,
reasons over each item, records each via `python3 engine/refresh.py --record '<json>'`
→ `python3 engine/analyze.py` builds the report. Large residue can fork the
`classification-reasoner` agent.

## What's built (Tasks 1–12) — module map & commit trail

17 commits, `e2f5a80..f9adfc4`. New `engine/` modules + the `analyze.py` rewrite:

| Module | Responsibility | Task → commit |
|---|---|---|
| `engine/store.py` | `output/decisions.json` — atomic writes (temp+fsync+os.replace), keyed `"owner:id"`, `src_hash` (raw fields only) + `rubric_hash`, **one freeze/drift rule** (llm/human frozen, rule re-runs under `--retune`, drift re-queues + keeps `extra.prior`) | T3 `20b438d` |
| `engine/classify_context.py` | data-free `RUBRIC` + `STATUS_VALUES` + `rubric_hash()` + `build_context(config)` (injects real config amounts/tokens at runtime, never committed) + `build_input(tx, siblings)` | T4 `c3ed70b` |
| `engine/moneytor.py` | stdlib HTTPS client — host-pinned `app.moneytor.co.il`, refuses redirects, maps 401/403→auth, 429→rate-limit, token never logged | T5 `862237d` |
| `engine/analyze.py` (rewrite) | `map_moneytor`/`_account_kind`/`_derive_bank_kind` (sign→magnitude+`sub_type`, float-tolerance, `account_kind` bank/card); `load_all` reads `output/snapshot/<id>.json`; re-grounded `classify_deterministic` (merchant rules + `account_kind=='bank'` gate + refund branch + terminal→`None`); `classify_one`/`classify_all` (store-backed); `TAG_LABELS`/`display_category`; earnings aggregation now gates on `account_kind` | T6 `7a5e055`, T7 `385f65d`+`2f83d70`, T8 `a2aa406`, T9 `93c5451`, fixups `f9adfc4` |
| `engine/refresh.py` | `--preflight` (Rule-Zero hard gate: `.env` gitignored + JWT-shaped grep on tracked files), `--pull` (all-or-nothing both people + truncation guard), `first_pass_residue`, `--record` (reconstructs full tx from snapshot so `src_hash` matches the build — round-trip verified) | T10 `36ed3d1`+`57f297d` |
| `config.example.py` | `Source(kind, token_env, account)` adapter seam; `Person` drops `data_dir`; PEOPLE use one `moneytor` source each | T11 `b37424d` |
| `.claude/skills/refresh/SKILL.md`, `.claude/agents/classification-reasoner.md` | `/refresh` runbook; `classification-tuner` renamed → reads `residue.json`, records via the CLI | T12 `80a5431` |
| Rule Zero | `.gitignore` (`.env*`, un-anchored `decisions*/snapshot*/residue*/report.html/meta.json`, narrowed `sample-data/**`), `.env.example` (names only) | T1 `f3edadd` |
| Tests (39) | synthetic fixtures + `unittest` per module + end-to-end integration smoke (earnings regression guard) | T2 `c8a6070`, etc. |

## Key decisions & gotchas (the non-obvious stuff)

- **Vendor choice is settled: Moneytor + a documented scraper fallback.** A web-verified
  vendor survey found Israel's regulated open-finance channel (Finanda/Feezback/bank
  portals) is excellent but **license-gated to companies** — an individual can't get a
  token. The only individual-accessible options are Moneytor (self-serve, but its API is
  an **undocumented private backend = the single point of failure**) and
  [`israeli-bank-scrapers`](https://github.com/eshaham/israeli-bank-scrapers) (self-hosted).
  Decision: Moneytor only for now, behind the **source-adapter seam** (`Source.kind`,
  spec §4.5); the scraper is a ready `kind='scraper'` second adapter, built only if
  Moneytor breaks. Don't chase regulated vendors.
- **Source-adapter seam:** everything downstream of the snapshot is vendor-agnostic.
  Adding the scraper = one new `fetch_*`/`map_*` pair; nothing else changes.
- **Category loss is the core migration problem:** Moneytor gives no Hebrew spend
  category, so the classifier was **re-grounded on merchant/`description` signals** (the
  category-set rules were converted to merchant patterns or dropped to LLM residue).
  Expect a larger first-run residue — that's by design (reason once, persist).
- **`src_hash`/`build_input` field names must match `map_moneytor`'s keys** (`tx_date`,
  `notes`, `card`) — a mismatch (the `f9adfc4` fixup) silently empties the LLM input and
  weakens drift detection. If you touch the normalized-tx shape, keep these aligned.
- **`record` reconstructs the full tx from the snapshot** before `put_decision`, so its
  `src_hash` matches the build's (else decisions look perpetually "drifted" and re-queue
  forever). Verified round-trip.
- **`analyze.py` imports config with a fallback to `config.example.py`** when no
  `config.py` exists (so tests/CI import cleanly). Tests inject `analyze.C =
  tests.config_example_shim` (Feb-2026 window) + `analyze.OUTDIR = <tmp>`.
- **Deployment (PR2) is designed but NOT built:** Supabase Storage private bucket + RLS
  on `auth.uid()` (a `viewer_users` allowlist) + short-TTL signed URL, publish only
  `report.html`, no service-role key. Chart.js/font inlining + the no-CDN assertion live
  in PR2 (deliberately deferred — spec §9). See spec §9.
- **Rule Zero is load-bearing on a PUBLIC repo** (`github.com/Roeelfs/expenses`): never
  commit a token / `config.py` / `.env` / real merchant/amount. `refresh.py --preflight`
  is the automated gate; the committed `sample-data/` + `tests/fixtures/` are synthetic
  (tokens "Doe"/"Landlord"). Run the preflight before any push.

## Run / test

```bash
python3 -m unittest discover -t . -s tests   # full suite (39 tests, expect OK)
python3 engine/refresh.py --preflight         # expect "ok", exit 0
# end-to-end smoke (no token): copy tests/fixtures/moneytor_person_*.json to a tmp
#   OUTDIR/snapshot/person_*.json, set analyze.C/OUTDIR, run analyze.main() → report.html
```

Requires `python3`. `openpyxl`/`pdftotext` are only used by the legacy parsers (deleted
in Task 14); the Moneytor path is pure stdlib.

## Status of the task tracker

Tasks 1–12 = completed. Task 13 (feasibility gate) and Task 14 (parser deletion) =
pending, blocked on the user's Moneytor tokens. The plan file has the full step text.
