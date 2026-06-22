# Moneytor integration + hosted viewer — design

**Date:** 2026-06-21
**Status:** approved design, pending implementation plan
**Scope:** Replace the manual file-upload front end with a local Moneytor API
ingest, persist LLM-assisted classification once per transaction, and publish the
rendered dashboard behind a two-user login. Everything downstream of
classification (settlement math, `render.py`) is reused unchanged except the
small category-derived views noted below.

---

## 1. Goal & the pivot

Today: `python3 engine/analyze.py` globs local bank/card files, parses them,
classifies with regex rules, and writes a self-contained `output/report.html`.

Target:

1. **Ingest, don't parse live.** Pull each person's transactions from Moneytor
   *occasionally* (manual refresh), snapshot them locally. A normal report build
   never calls the API.
2. **Reason once, persist by id.** The expensive step is semantic classification.
   A deterministic regex first-pass decides the obvious backbone; the **ambiguous
   residue is reasoned over once by the Claude Code local harness** (not a
   programmatic API call) and the decision is persisted, keyed by the stable
   Moneytor transaction `id`. Rebuilds and incremental refreshes reuse persisted
   decisions; only new/changed transactions are re-reasoned.
3. **Publish only the artifact.** Because reasoning needs the local harness, the
   cloud never reasons. The deployed app is a **read-only, auth-gated viewer of
   the locally-built `report.html`**; refresh stays local; the server holds no
   Moneytor token and never calls Moneytor.

The persisted store (`output/decisions.json`) **replaces `output/transactions.csv`**
as the source of truth.

## 2. Locked decisions

| Decision | Choice |
|---|---|
| Audience | Private — exactly two fixed users (the couple). No signup/billing/tenancy. |
| Sources | Replace the file parsers **entirely** with Moneytor (after a hard feasibility gate). |
| Hosting | Keep the Python engine local; publish only `report.html` to a Supabase-gated viewer. |
| Moneytor access | Both users have Premium and can mint API tokens. |
| Classification | **Regex-first hybrid** — rules decide the backbone, LLM reasons over the residue, each tx once, persisted by id. |
| Store format | Plain `output/decisions.json` (`{"owner:id": decision}`, atomic writes), stdlib `json`. **Not** SQLite. |
| Deployment | Supabase Storage (private bucket) + RLS gated to **two verified identities** (a `viewer_users` allowlist keyed on `auth.uid()`, server-verified — not a client-side or `email` check) + short-TTL signed URL into a sandboxed iframe. **No service-role key** (a local authenticated publisher session uploads; §9). |
| Reasoning mechanism | Local Claude Code `/refresh` skill (manual); the harness reasons over the residue. Remote MCP / custom API+DB **rejected** — tokens-on-server inverts Rule Zero, and remote MCP is tools-only. See §3.1. |
| Data source(s) | **Moneytor only for now, behind a one-method source-adapter seam** (§4.5). A vendor survey confirmed the regulated open-finance channel (Finanda, Feezback, bank-direct) is excellent but **license-gated to companies** — an individual can't get a token; the only individual-accessible peer is the self-hosted [`israeli-bank-scrapers`](https://github.com/eshaham/israeli-bank-scrapers), documented as a **ready second adapter**, not built now. |

## 3. Architecture

```
LOCAL refresh  (occasional, the ONLY networked code)
  engine/refresh.py
    per person: GET https://app.moneytor.co.il/api/v1/transactions?from&to&limit
        host-pinned · HTTPS-only · refuse all redirects · strip Authorization on redirect
    → output/snapshot/<person>.json        (latest only, overwrite, gitignored)
    → upsert output/decisions.json:
          new id        → needs_reasoning
          unchanged hash→ keep decision
          drifted hash  → re-queue (rule/pending re-runnable; llm/human frozen)

LLM reasoning  (once per residue tx — Claude Code harness via the /refresh skill)
    regex first-pass decides the backbone
    → residue (new/changed/ambiguous) handed to the LLM with the taxonomy,
      config name tokens, and the rent/landlord/salary AMOUNT constants
    → decisions written back to output/decisions.json, decided_by='llm'
      (human corrections decided_by='human' — both FROZEN, never re-flipped)

BUILD  (frequent · free · offline · deterministic)
  engine/analyze.py main()
    read latest snapshot → map_moneytor() → join decisions by id
        (build strictly from the CURRENT snapshot's id set → no double-count)
    → existing aggregation + settlement math (unchanged)
    → render.build_html() → output/report.html

PUBLISH  (occasional, local → cloud)   [Phase 2]
  engine/publish.py: upload report.html (+ a footer 'last updated' stamp) to a
    PRIVATE Supabase Storage bucket. Nothing else leaves the machine.
```

A rebuild on an unchanged snapshot performs **zero** API calls and **zero** LLM
work — "reason once" is structural, not best-effort.

## 3.1 Mechanism: the local `/refresh` skill (decided)

An architecture-research pass (local skill vs remote MCP vs custom API+DB),
ranked adversarially on Rule Zero, YAGNI, and June-2026 feasibility, put the
**local Claude Code `/refresh` skill first on all three lenses**. Remote MCP and
a custom API+DB were rejected:

- **The Anthropic Messages API MCP connector is tools-only** (MCP *resources* and
  *prompts* — the intended channel for "the context the LLM needs" — are
  unsupported there; Claude Code itself *does* support MCP resources/prompts over
  HTTP, so this is narrower than "every client"). Its unattended path is also
  blocked by open scheduled-task bugs. **But the load-bearing reason to reject
  remote MCP is not the connector limitation — it is that the server would hold
  the two Moneytor tokens (next bullet).**
- **MCP and a custom API both park the two 30-day Moneytor tokens** (and, for the
  API, real financial rows) **on an always-on internet host** — inverting Rule
  Zero on a public-template repo — and are high-complexity for a two-person tool.
  Their only unique benefit, *server-off unattended refresh*, is not required
  (refresh is manual/occasional).

**Skill surface** — `.claude/skills/refresh/SKILL.md`: `disable-model-invocation:
true` (side-effecting, user-invoked only), `argument-hint: [--from YYYY-MM-DD]
[--no-llm] [--retune] [--publish]`, `allowed-tools` scoped to
`Bash(python3 engine/*.py *)`. The SKILL.md body is the runbook; all deterministic
work is Python, the only non-deterministic step (residue reasoning) is the harness.

**Flow the skill drives:** preflight (Rule-Zero asserts; abort on fail) →
`refresh.py --pull` (network + snapshot + store upsert + regex first-pass →
`output/residue.json`) → **the harness reasons over the residue** and records each
verdict via `python3 engine/refresh.py --record '<json>'` (schema-validated,
`decided_by='llm'`, stamped) → `analyze.py` build → optional `--publish`. A large
residue can fork to the renamed `classification-reasoner` subagent to keep the
main context lean; a normal incremental refresh (a few new tx) reasons inline.

The reasoning context is delivered by the `engine/classify_context.py` artifact
(§5.4), isolated for Rule-Zero auditability of the real `config.py` amounts.

## 4. Data contracts

### 4.1 Moneytor `/transactions` (source)
Per tx: `id` (stable ULID), `date` (ISO), `amount` (signed; **− = expense,
+ = income**), `currency` (`"ILS"`), `description` (Hebrew merchant/counterparty
string), `extra_info` (string|null), `category` (**coarse flow enum** —
`BANK_TRANSFER`, `CREDIT_CARD_CHECKING` — *not* a Hebrew spend category),
`accountId`, `type` (e.g. `CHECKING`). Query: `from`, `to` (ISO), `limit`
(default 500, cap 2000). Auth: `Authorization: Bearer <jwt>` (Premium, 30-day).
Rate: documented as ~30/hr, 300/day per user — a private-UI claim **not in the
public OpenAPI**; treat as unverified and back off on HTTP 429 (`Retry-After`).
**HTTPS confirmed reachable** (review web-probe: `http://`→301→`https://`;
`https://app.moneytor.co.il/api/v1/transactions` returns JSON 401/405 without a
token) — so the integration is not http-blocked; code still pins `https://` + the
host and refuses redirects (§7). **`id` is unique only within one user/token**
(the OpenAPI gives no cross-user uniqueness guarantee) — so the store keys on
`owner:id`, never `id` alone (§4.3).

### 4.2 `map_moneytor(raw, owner) -> dict | None`
The **Moneytor source adapter** — the first (and, for PR1, only) adapter behind
the seam in §4.5. Maps one Moneytor tx to the engine's existing normalized dict so
`render.py`'s contract holds. Key rules:

- `id` — **new key**; the store + dedupe key.
- `amount = abs(signed)` (engine sums magnitudes); `sub_type = 'credit' if
  signed > 0 else 'debit'` — Moneytor's sign cleanly supplies the credit/debit
  direction the old bank loaders derived from balance heuristics.
- `merchant = strip_rtl(description)` — feeds every surviving merchant regex.
- `category = ''` initially; a usable display category is **derived from the
  engine `tag` after classification** (see §5.3).
- `account_kind ∈ {bank, card}` derived from Moneytor `type`/`category`/`accountId`
  (an explicit mapping table built from the real pull, not a guess); it replaces
  the deleted `source`-string allowlist as the bank-vs-card discriminator (§6 #1).
  Every `account_kind=='bank'` row must get a non-empty `bank_kind` via the
  consolidated `_derive_bank_kind` — asserted at the gate.
- period filter (`PERIOD_START..PERIOD_END`, inclusive, after normalizing `date`
  to a fixed timezone) applied here; `amount == 0` dropped.
- `bill_date = tx_date` (Moneytor exposes one date). This collapses the
  tx-date/bill-date split the engine relied on (cards bill ~10th of next month),
  so a card tx near a month boundary can change which month — and even whether it
  is in-window — versus the old parser. The monthly view uses posting date and
  the `UTIL_TX_RE` bi-monthly-arrears exception (`analyze.py:103`) is **removed**
  (utilities judged on the single Moneytor date). Period-boundary membership is a
  hard gate check (§8).

### 4.3 `output/decisions.json` (store — source of truth)
A flat `{key: decision}` map, `json.loads`/`json.dumps`, gitignored. **The key is
`"<owner>:<id>"`** — Moneytor `id` is unique only within one user/token, so keying
on `id` alone would let one person's decision shadow the other's; the composite
key prevents cross-person collisions (gate-asserted, §8).

```json
{
  "person_a:01KQRZXN78ZD6DZ8NM8YC1YSCY": {
    "status": "shared",
    "tag": "grocery_or_household",
    "reason": "shared merchant",
    "decided_by": "rule",
    "decided_at": "2026-06-21",
    "src_hash": "<sha256 of RAW source fields>",
    "rubric_hash": "<sha256 of classify_context RUBRIC>",
    "extra": {}
  }
}
```

- **Atomic writes are mandatory.** Both `refresh.py --record` and the build mutate
  this single file; a crash mid-`json.dump` would destroy *every* persisted
  decision. All writes go through `write_json_atomic(path, data)` (same-dir temp
  file → `flush`+`fsync` → `os.replace` → fsync the dir). Never write in place.
- `decided_by ∈ {rule, llm, human}`. `pending` is **not** a valid stored decision
  (§5.2).
- **One freeze/drift rule** (resolves the earlier self-contradiction): a stored
  decision is valid only while its `src_hash` matches the current raw tx. On a
  hash **match**, `llm`/`human` are returned verbatim and `rule` is reused unless
  `--retune`. On a hash **mismatch** (upstream tx changed — amount, merchant, …),
  the tx is re-queued as `state='needs_reasoning'` *regardless of `decided_by`*,
  and the prior decision is retained in `extra.prior` as evidence. No decision is
  ever silently re-flipped or silently kept stale.
- `src_hash` is computed over **raw/normalized source inputs only** — `id`,
  `owner`, `date`, signed `amount`, `currency`, `description`, `extra_info`,
  Moneytor `category`, `type`, `accountId`, `bank_kind`. It must **not** include
  any post-classification field (e.g. the tag-derived display `category`), which
  would make invalidation circular.
- `rubric_hash` — the SHA-256 of the committed `RUBRIC` in
  `engine/classify_context.py`; the one cheap taxonomy-invalidation key. A
  mismatched `rubric_hash` re-queues affected decisions when the taxonomy changes.
  This is the *only* versioning the store carries (no `rules_version`/model/
  confidence).
- `extra` carries only the optional keys `classify()` emits (`loan_id`,
  `earnings_kind`, `is_likely_salary`, card-rent `sub_type` override) plus `prior`
  on a re-queue. No confidence floats, model, or extra timestamps.

### 4.4 `output/snapshot/<person>.json` (+ `snapshot/meta.json`)
The verbatim latest Moneytor response per person, gitignored. The build re-runs
`map_moneytor` over it each time (microseconds for ~739 rows), so the normalized
tx is **not** also cached in the store.

**The pull is all-or-nothing across both people.** A partial pull (one token
valid, the other expired) would build the settlement on incomplete data → wrong
who-owes-whom. So `refresh.py --pull` fetches *both* people into temp files,
validates both succeeded, then atomically promotes both snapshots + a sidecar
`snapshot/meta.json` (`pulled_at`, per-person `window`, `limit`, `fetched_count`)
as one generation. If **either** person's pull fails (expired token, 429,
network), the previous complete generation is left intact and the build/publish
does not run. The build refuses to run unless both snapshots share one `meta.json`
generation (no fresh-A/stale-B mix).

**Truncation guard.** Recursive pagination is out of scope, but a silently
truncated pull would corrupt every total — so a pull **hard-fails** when
`fetched_count == limit` for any window (more rows may exist), never snapshotting
a truncated set.

### 4.5 Source-adapter seam (the only vendor-coupled layer)
Everything downstream of the snapshot — the store, classifier, settlement math,
gate, and viewer — is **source-agnostic**: it only sees the normalized tx dict.
The one vendor-coupled surface is the ingest adapter. So `Source` carries a
`kind` (which adapter) + `token_env`; `refresh.py` dispatches per `kind` to a
`fetch_<kind>()` + `map_<kind>()` pair. PR1 ships exactly one: `kind='moneytor'`
(`engine/moneytor.py` + `map_moneytor`). This is a real seam (two tiny functions),
**not** a speculative framework — it exists because the vendor survey found
Moneytor's API is the app's **undocumented private backend** (a genuine
single-point-of-failure, §11), and the only individual-accessible fallback is the
self-hosted [`israeli-bank-scrapers`](https://github.com/eshaham/israeli-bank-scrapers)
(MIT; covers all banks + Isracard/Max/Visa-Cal/Amex). That scraper is a
**documented, ready second adapter** (`kind='scraper'`: a Node subprocess emitting
the same normalized dict) — built **only if** Moneytor's endpoint breaks or a
coverage gap appears. Its credentials are bank usernames/passwords (more sensitive
than a token), so adding it extends the Rule-Zero preflight (§7) to those
credentials; not in scope for PR1.

## 5. Classification (hybrid, reason-once)

### 5.1 Three layers behind one driver
`classify_one(tx, store, queue, retune=False)`:
1. **Store lookup** — `tx['id'] in store` and not stale → return the persisted
   decision verbatim (freezing `llm`/`human`).
2. **Deterministic first-pass** — `classify_deterministic`, the current cascade
   **re-grounded on Moneytor-available signals** (this is *not* the rule body
   unchanged). Most of the cascade today decides via Hebrew **category-set**
   membership (`SHARED/PERSONAL/RESTAURANT/VACATION/FURNITURE/TRANSFER/
   AMBIGUOUS_CATEGORIES`, `analyze.py:609,614,642,649-658`), and Moneytor supplies
   no Hebrew spend category — so those rules would all go no-op and dump the
   backbone into the LLM. Fix: derive a `normalized_merchant` from `description`
   (raw → normalized merchant *before* matching), keep/extend the
   **merchant-regex** rules (which survive — they key on `description`→merchant),
   and **convert each category-set rule into a merchant/`description`-keyword
   rule or delete it**. The spec enumerates, per `*_CATEGORIES` set, whether it is
   converted (to a merchant pattern) or dropped (escalated to the LLM). Backbone
   hits persist as `decided_by='rule'`.
3. **Residue** — whatever the re-grounded cascade can't decide (former
   `AMBIGUOUS_CATEGORIES`, `foreign`, uncategorized, and any dropped-category tx)
   returns `None` → appended to the LLM queue. First-run residue is expected to
   grow vs today; it is **budgeted** at the gate (§8) and each tx is reasoned once
   and persisted, so it is a one-time cost.

`classify_all()` runs a first sweep (builds the residue queue), the harness fills
the store, then a second sweep returns the complete classified list.

### 5.2 No silent freeze
If the LLM step is skipped (e.g. `--no-llm` build), still-undecided ids are
treated as **`state='needs_reasoning'`**, *not* written as a decided
`pending` record. The requeue predicate is `state=='needs_reasoning'`, so a
transiently-skipped reasoning step never permanently freezes a tx as flagged.

### 5.3 Category-loss fix (touches `render.py` — small, deliberate)
Moneytor drops the Hebrew spend category that `render.py` reads for the
transactions-table column, the search index, the top-categories donut, and the
per-car breakdown (`CAR_CATEGORIES`). Fix:
- After classification, set `tx['category']` to a **label derived from the engine
  `tag`** (a `TAG_LABELS` map) so table/search/donut have data.
- Re-key the top-categories donut and the car breakdown off **`tag`** (engine-
  controlled, stable) instead of the now-absent Moneytor Hebrew category.

The "render untouched" claim from the first draft was false; these are the
targeted edits required.

### 5.4 The LLM residue contract
Each queued item gives the model: the normalized tx (incl. `description`,
`extra_info`, signed direction, Moneytor `type`/`category`), the status/tag
taxonomy, the config name tokens, **and the rent/landlord/rental-income/salary
amount constants** (so it can disambiguate `landlord_rent` vs `couple_transfer`,
which can be the same person differing only by amount). The model emits
`status, tag, reason` (and a spend category for `extra`/display). Anything it
cannot decide it writes as `status='flag', decided_by='llm'` — surfaced, never
re-queued forever.

This contract lives in one module, **`engine/classify_context.py`**, justified by
Rule Zero (not portability): it is the single place that touches the real
`config.py` amount constants + name tokens, so isolating it keeps that sensitive
surface auditable. It holds a committed, data-free `RUBRIC` (the status/tag
taxonomy), the output JSON schema, `build_context(config)` (renders the name
tokens + rent/landlord/salary amount constants from `config.py` **at runtime —
never committed**), and `build_input(tx, store)` (one residue tx + signed
direction + Moneytor `type`/`category` + N already-decided sibling examples,
human-decided first). The committed `RUBRIC`'s hash is the store's `rubric_hash`
invalidation key (§4.3). Determinism: low temperature + structured output +
freeze-after-first-decision. (If `RUBRIC` + schema + the two builders land under
~80 lines, inline them into `analyze.py` rather than a 5th engine module — decide
by line count.)

### 5.5 Rules stay; promotion is optional
Decisions accumulate in the store as the default. Editing regex lists in
`analyze.py` is an **optional periodic optimization** (promote a merchant that
recurs in the residue across ≥2 refreshes) — never part of the per-refresh loop.
The store, not the regex, is the source of truth.

## 6. Must-fix wiring (verified against the code)

| # | Problem | Fix |
|---|---|---|
| 1 | Bank routing + earnings gate on `source in ('leumi-bank','discount-bank')` ([analyze.py:569,701,703](../../../engine/analyze.py)); `moneytor-*` matches neither → bank block + income section silently zero. | Route on **`bank_kind` presence** (or an `account=='bank'` field), not a source allowlist. Converge on one `source` value. Hard-assert `bank_credits` non-empty on the real pull. |
| 2 | `category=''` breaks 4 render views. | §5.3 — derive display category from `tag`; re-key donut + car breakdown off `tag`. |
| 3 | Landlord/returned-cheque/non-income `bank_kind` keys off cheque-memo strings (`שיק`, `עבר זמ`) absent from Moneytor `description` → rent-settlement corruption. | Re-tune detection against **real Moneytor strings**; give the LLM the amount constants (§5.4); the gate hard-blocks on **all** rent + non-income-credit classes — landlord, couple-transfer, salary, rental-income, **returned-cheque, self-transfer** (§8). |
| 4 | Card refund (positive Moneytor amount on a card) `abs()`-ed into spend (summed into `by_status['shared']` at `analyze.py:713,737`) → settlement flips the *wrong way*. | `account_kind=='card'` + `sub_type=='credit'` → a `refund` status **excluded from `by_status` before the settlement delta** (or a signed-negative adjustment to its bucket) — never summed as positive spend. Ships with a regression fixture. |
| 5 | `decided_by='pending'` treated as a cache hit → frozen flag forever. | §5.2 — pending is `needs_reasoning`, always re-queued. |
| 6 | `bill_date=tx_date` shifts the monthly view (cards bill ~10th next month), drops the `UTIL_TX_RE` arrears exception (`analyze.py:103`), and changes **period-boundary membership** (which tx are in-window → moves the settlement total). | Monthly view uses posting date; `UTIL_TX_RE` removed (§4.2); the gate hard-checks **period-boundary membership parity**, not just `by_month` (§8). |
| 7 | `config.Source` deleted by one area but repurposed by another. | Keep a **minimal `Source`** carrying `kind` (`'moneytor'`; the adapter seam, §4.5) + `token_env` + account label per person; `Person` keeps `id/label/color`; retain the `person_a/person_b` id assertion. |
| 8 | Rent/landlord/salary amounts matched by exact float `==` in some loaders (`analyze.py:244,329`) but `abs(...)<0.01` in others — exact `==` on a Moneytor-precision float silently misses → wrong settlement. | Converge **all** rent/landlord/rental/salary amount comparisons on one tolerance (`abs(a-K) < 0.01`). |
| 9 | Store keyed on Moneytor `id` alone, but `id` is unique only per user/token → one person's decision could shadow the other's. | Key the store on `"<owner>:<id>"` (§4.3); gate-assert no cross-person `id` collision. |

## 7. Rule Zero hardening (same change as each surface)

Verified with `git check-ignore` on a **public** template repo: the existing
`/output/*` rule already covers `decisions.json`, `snapshot/`, `report.html`,
`meta.json`, `residue.json` **as long as they live under `output/`** — the first
draft's "protects none" overstated it. But real gaps remain:

- Add `/.env` + `.env*` (then `!/.env.example`) **before any token is written**
  (`git check-ignore .env` is currently **not ignored**). `refresh.py` preflight
  hard-aborts (no network) if `git check-ignore .env` fails.
- `.env.example` and `config.example.py`: placeholder names only, a loud
  "NEVER put a real token/secret here" header, and a refresh/pre-commit grep that
  hard-fails on a `eyJ…` JWT or a populated secret value.
- Extend the defense-in-depth net with **un-anchored** ignores for every new
  financial format so a stray path outside `output/` is still caught:
  `decisions*.json`, `snapshot*.json`, `residue*.json`, `report.html`,
  `meta.json` (and `deploy/**` data files — keep `deploy/` to code + RLS SQL
  only). Ground all store/snapshot/residue paths under a single `OUTPUT_DIR`
  constant in code — never under `engine/`.
- **Narrow the `sample-data/**` whitelist** — it currently `!`-re-includes *any*
  `.json` (a real snapshot dropped there is force-committed). Whitelist named
  synthetic files only; forbid deriving any fixture (incl. `classify_context`
  sibling examples, reasoner fixtures) from a real snapshot; pre-commit scan for
  real `COUPLE/LANDLORD/SALARY` tokens and ₪ amounts in committed paths.
- The token is never written into a snapshot or log; assert snapshots contain no
  `eyJ…`. The store contains zero token material.
- **Layered secret scanning** beyond the bespoke grep: add `gitleaks` as a
  pre-commit + CI check (custom Moneytor-JWT rule), and rely on GitHub
  push-protection. The bespoke `eyJ…` grep stays as the fast local preflight.
- HTTPS (**verified reachable**, §4.1): hardcode `https://`, **pin host
  `app.moneytor.co.il`**, refuse **all** redirects, strip `Authorization` on any
  redirect, run the reachability probe with **no** real token, keep TLS on.

## 8. Feasibility gate (hard — must pass before deleting parsers, in PR1)

Coverage + sign parity is **not** sufficient. The gate needs a **captured overlap
window** — one final file-statement pull kept solely for this check, covering the
same period as a real Moneytor pull. **If no overlap exists, parser deletion is
deferred:** PR1 adds the Moneytor path and *keeps* the parsers; a follow-up
deletes them once an overlap window has been captured and the gate is green (this
is the one case where the two architectures briefly coexist, gated by necessity).
Require:

1. HTTPS reachability over `https://` (verified, §4.1; hard stop if it regresses
   to http-only).
2. Field fidelity: documented fields present; **two pulls of the same window
   return the identical `id` set** (ids stable, not merely ULID-shaped); **no
   cross-person `id` collision** (the `owner:id` invariant, §4.3); and a *later*
   pull that modifies an existing id is detected by `src_hash` drift (§4.3).
3. Sign correctness: known income `+`, known expense `−` (spot-check).
4. `bank_kind` correctness on real data for **every** rent + non-income-credit
   class — landlord, couple-transfer, salary, rental-income, **returned-cheque,
   self-transfer** — **hard blocker** (these drive the settlement).
5. **Settlement parity, quantified**: the final who-owes-whom delta old-vs-new
   matches within **±₪1 (or 0.5%, whichever is larger)**. The per-tx `status`/`tag`
   diff is asserted **only over the deterministic backbone** (rule-decided tx) —
   LLM-residue tx are excluded (the LLM path legitimately differs from old regex).
6. `bank_credits` non-empty; **period-boundary membership parity** (count of
   in-window tx old-vs-new within tolerance — `bill_date` collapse changes
   in/out-of-window, §4.2); sane shared/personal/earnings sections. `by_month`
   bucket boundaries are **exempt** (the posting-date shift is accepted, §4.2).
7. First-run **residue rate within budget** (e.g. ≤ ~⅓ of tx) — confirms the
   re-grounded cascade (§5.1) still classifies the backbone deterministically.

Only on green do the five loaders + `LOADERS` + glob + `openpyxl` + `pdftotext`
dependency + `config.Source` globs get deleted. The parity run executes against
**pre-deletion** code, so the gate runs before the delete hunk in the PR.

## 9. Phasing

**PR1 — the local pivot (one PR, deletes its legacy in the same change):**
Moneytor client + `refresh.py` + snapshot + `output/decisions.json` store +
`classify_one`/`classify_all` wiring + the must-fix items (§6) + Rule Zero
hardening (§7) + the `/refresh` skill orchestration + the feasibility gate (§8)
+ deletion of all file parsers. Updates the `expense-report` skill,
`statement-onboarder`, and `classification-tuner` docs to describe
snapshot+store, not globs+CSV. Result: identical `report.html`, sourced from
Moneytor, no files.

**PR2 — the hosted viewer (optional, after PR1 is verified):** `engine/publish.py`
uploads `report.html` to a **private** Supabase Storage bucket using a **local
authenticated Supabase session** for one allowlisted publisher (still **no
service-role key anywhere** — the rejected "Form A" is not built). Access is
enforced by **RLS, not client-side checks**: a `private.viewer_users(user_id,
enabled)` table is seeded after email confirmation, and the `storage.objects`
policies scope `INSERT/UPDATE/SELECT` to `bucket_id` + `name='report.html'` +
`auth.uid() ∈ viewer_users`. The viewer page **server-verifies identity**
(`getUser()`/`getClaims()`, never a cookie-derived session or a mutable `email`
string), then mints a **short-TTL** signed URL and embeds the object in a
sandboxed iframe with `Cache-Control: private, no-store`. Note the **residual
bearer-URL risk**: a signed URL works for anyone holding it until expiry, so TTL
is seconds-to-minutes and URLs never land in history/referer. A **build/publish
assertion** verifies `report.html` has **no external `https://` script/font
`src`** before upload — Chart.js + fonts are inlined (`render.py:472,475`
currently load them from a CDN), so no third-party fetch on a financial page.
30-day token expiry is a local-only concern, surfaced at refresh.

## 10. Files

**PR1 — new:** `engine/moneytor.py` (stdlib HTTP client), `engine/refresh.py`
(network entry point + preflight + feasibility gate + `--pull`/`--record`),
`engine/classify_context.py` (reasoning contract: `RUBRIC` + output schema +
`build_context`/`build_input`; §5.4), `engine/store.py` (the plain-JSON store:
`load`/`save` via `write_json_atomic`, `owner:id` keying, `src_hash`/`rubric_hash`,
the one freeze/drift rule — **not** the cut SQLite module; extracted because
`analyze.py` already exceeds the 800-line max), `.claude/skills/refresh/SKILL.md`
(the `/refresh` orchestration, `disable-model-invocation: true`) +
`classification-reasoner` (a **rename of** the existing `classification-tuner`
agent — old file deleted in the same change). Transient `output/residue.json` (the
`needs_reasoning` queue handed to the harness) is gitignored, overwritten each
pull. **PR1 — edit:** `engine/analyze.py` (delete loaders +
glob; rewrite `load_all` to read snapshot; add `map_moneytor`,
`_derive_bank_kind`, `classify_one`/`classify_deterministic`/`classify_all`,
store load/save; fix the three source-string gates; CSV → optional debug export),
`engine/render.py` (category-from-tag + donut/car-breakdown re-key + inline
Chart.js/fonts), `config.example.py` (minimal `Source` with `token_env`; remove
file-glob fields; add `STORE_PATH`/snapshot path), `.gitignore` (§7),
`.claude/skills/expense-report/SKILL.md`, `.claude/agents/*`. **PR1 — delete:**
the five file loaders + `LOADERS` + `_ym_from_name` + glob/openpyxl/pdftotext
machinery; `transactions.csv` as source of truth. **PR2 — new:**
`engine/publish.py`, `deploy/` (viewer page + RLS SQL, code only — no data files).

## 11. Risks & open questions

- **Moneytor's "API" is an undocumented private backend (single point of failure).**
  A vendor survey confirmed Moneytor sells no documented developer API — the
  per-user JWT is the app's own private endpoint. It works and is individually
  self-serve (Premium ~₪490/yr, two-user plan), but it is unsupported, carries no
  ToS permission, and can change/lock-down without notice. Mitigation: the
  source-adapter seam (§4.5) makes the documented fallback
  (`israeli-bank-scrapers`, self-hosted, all banks + Isracard/Max/Visa-Cal/Amex) a
  cheap drop-in if that happens. The regulated channel (Finanda/Feezback/bank
  portals) is better but **license-gated to companies** — not an individual option.
- **Moneytor `description` fidelity** vs the strings the regex lists were tuned
  against — merchant regexes may under-match; every miss escalates to the LLM
  (more reasoning, not a wrong silent bucket). Audit hit-rate on the first real
  run; tune against actual descriptions.
- **First-run residue grows** (category-loss): more tx reach the LLM once. Bounded
  by the gate's flag-rate check; persisted forever after.
- **`bill_date`/monthly semantics** (#6): confirm whether Moneytor ever exposes a
  separate billing date for installments; otherwise posting-date months are the
  documented behavior change.
- **Card refunds** (#4): minimal cut routes them out of spend; a richer
  refund-netting view is out of scope.
- **Residue dedupe across pulls**: build joins on the *current* snapshot's
  `owner:id` set, so retained-but-absent store entries can't double-count; ULID
  stability + no cross-person collision are gate-verified.
- **Posted transactions can change** (aggregators recategorize/refund posted rows;
  pending→posted can change amount): the `src_hash` drift rule (§4.3) re-queues a
  changed tx, and the gate tests "same window pulled later yields modified existing
  ids," not just identical id sets.
- **HTTPS resolved (not a risk):** the review web-verified the API answers over
  HTTPS (§4.1); the http→https redirect is refused in code (token never sent over
  a redirect).

## 12. Deliberately out of scope (cut as over-engineering)

SQLite store + `engine/store.py` module + WAL/indexes/CHECK/`schema_version` +
`store_cli.py`; audit-grade provenance (confidence floats, model, rules_version,
four timestamps, `merchant_seen`/`amount_seen`); snapshot history /
`--keep-last` / archive-rollback; the redundant normalized-tx copy inside the
store; JWT-expiry decoder / `token_days_left`; assets/asset-worth fetchers;
recursive pagination; the staleness state machine / empty-state UI (a footer
"last updated" line suffices); the service-role "Form A" publish path; the
classification-tuner auto-promotion loop (optimize only if the residue rate
proves it necessary).

Also rejected by the architecture-research pass (§3.1): a **remote MCP server**
(the Anthropic Messages API MCP connector is tools-only, and — the load-bearing
reason — it would park both Moneytor tokens on an always-on host) and a **custom API + Supabase-Postgres
store + scheduled agent** (heaviest option; stands a permanently queryable copy of
the couple's finances plus live tokens on internet infra to buy an unattended
refresh that isn't required). The chosen mechanism is the local `/refresh` skill.
