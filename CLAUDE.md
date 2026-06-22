# CLAUDE.md — working in this repo

This project turns two people's raw bank/credit-card statements into a single
self-contained **HTML expense dashboard** that answers: *what did we spend, who
owes whom, and can we afford it?* It is built to be driven by you (Claude) — the
heavy lifting of reading a new person's statements and tuning rules is your job.

## 🔒 Rule zero: never commit financial data

This is the most important rule in the repo. **Only logic is committed; data
never is.**

- Real values live in **`config.py`** (gitignored). The committed template is
  `config.example.py` — it must stay free of real names, amounts, and tokens.
- Moneytor JWTs live in **`.env`** (gitignored). Never echo, paste, or commit them.
- Snapshots, decisions, and residue go to **`output/`** (gitignored).
- `.gitignore` also refuses *any* `.pdf/.xlsx/.csv` outside `sample-data/`.
- `python3 engine/refresh.py --preflight` is the automated Rule Zero gate — it
  checks `.env` is gitignored and scans tracked files for JWT-shaped tokens.
  Always run it before `--pull`.
- Before any `git add`/commit, run `git status` and confirm no snapshot,
  no `config.py`, no `.env`, no `output/` file, and no real name/amount is staged.
- Never paste a real name, account number, salary, or merchant from someone's
  data into a committed file (code, comment, README, or sample). If you need an
  example, invent a synthetic one.

If you ever notice PII in a tracked file, stop and fix it before anything else.

## Architecture

```
config.py                    # ALL personal knobs: people, period, split, amounts, name tokens, token_env refs
engine/moneytor.py           # Moneytor API client — fetch_transactions(); the ONLY networked code besides refresh
engine/store.py              # decisions store: load/save/put_decision; src_hash drift detection
engine/classify_context.py   # committed RUBRIC + STATUS_VALUES + build_input/build_context
engine/refresh.py            # local refresh CLI: --preflight, --pull [--from/--to], --record '<json>'
engine/analyze.py            # load_all (snapshot) → classify_all (regex + store) → settlement math → render
engine/render.py             # build the single-file HTML dashboard (Chart.js, dark theme)
```

Key data files (all gitignored — never commit):
```
.env                         # Moneytor JWTs: MONEYTOR_TOKEN_A / MONEYTOR_TOKEN_B
output/snapshot/<person>.json  # raw API pull per person
output/decisions.json        # source of truth: LLM + rule verdicts keyed by owner:id
output/residue.json          # ambiguous queue after regex first-pass
output/report.html           # generated dashboard
```

Pipeline — **pull path** (networked, run via `/refresh`):
`config.py + .env` → `refresh.py --pull` (Moneytor API → snapshot) →
regex first-pass → `residue.json` → LLM reasoning → `--record` each verdict →
`python3 engine/analyze.py` → `output/report.html`.

**Build path** (offline, deterministic): `python3 engine/analyze.py` — reads
snapshot + decisions store, no network, no re-reasoning.

```bash
python3 engine/refresh.py --preflight   # Rule Zero gate — must exit 0
python3 engine/refresh.py --pull        # fetch snapshot + write residue.json
python3 engine/analyze.py               # build output/report.html from store
```

Requires `python3` and `openpyxl` (`pip install openpyxl`).

## The two people

The engine compares **exactly two** people, with fixed internal ids
**`person_a`** and `person_b` (used as dict keys throughout both files). In
`config.py` you may change each person's `label` (display name) and `color`, but
**not** the `id`. `analyze.py` asserts this on startup.

## Classification taxonomy

`classify()` assigns every transaction a **status** (drives settlement) and a
**tag** (drives the category views):

- **shared** — split by `SPLIT` (groceries, utilities, furniture, household)
- **personal** — stays with whoever paid (fuel, phone, gym, subscriptions, vehicle, insurance, fashion, pharmacy…)
- **rent** / **landlord_rent** — rent settlement transfers / cheques to landlord
- **restaurant**, **vacation** — pooled & shown, *not* split into the settlement
- **business** — one person's work tools (SaaS/dev/AI), not split
- **loan** — loan setups & repayments (tracked, not spend)
- **earnings**, **rental_income** — bank credits (income side)
- **transfer** — Bit/PayBox/ATM/fees/inter-account moves (excluded from spend)
- **refund** — card credit reversing prior spend (excluded from spend)
- **flag** — didn't match a rule; surfaced for a human decision

The regex rules are plain Python lists/regexes near the top of `analyze.py`
(`UTILITY_RULES`, `FUEL_MERCHANT_RE`, `SHARED_CATEGORIES`, `PERSONAL_CATEGORIES`,
`BUSINESS_MERCHANT_RE`, `SHARED_MERCHANT_PATTERNS`, `AMBIGUOUS_CATEGORIES`, …).
Ambiguous transactions that escape the regex pass go into `output/residue.json`
for one-time LLM reasoning; verdicts are persisted in `output/decisions.json`.
Personal names for couple-transfer / landlord / salary detection are NOT in the
engine — they come from `config.py` token lists and `.env`.

## Adding a bank or card parser

The primary data path is now Moneytor (`engine/moneytor.py` + `analyze.py:map_moneytor`).
Raw file parsers are still supported for banks not covered by Moneytor. The
built-in parsers target Israeli formats (Isracard xlsx/pdf, Leumi pdf,
Discount csv/pdf). To add another:

1. Write `load_<bank>(path, owner, account='bank') -> list[dict]` in
   `analyze.py`, returning the normalized tx dict (see an existing loader for
   the exact keys: `owner, card, source, tx_date, bill_date, merchant,
   category, amount, currency, orig_amount, orig_currency, sub_type, notes,
   foreign`, plus `bank_kind` for bank statements).
2. Register it in the `LOADERS` map with a new `kind` string.
3. Reference that `kind` from a `Source(...)` in `config.py`.

Inspect a raw statement first: `pdftotext -layout file.pdf - | less`, or open
the xlsx, to learn the column layout before writing the parser.

## Onboarding a new user

There's a skill for the full interview + setup flow:
`.claude/skills/expense-report/SKILL.md`. Use it when someone wants to set this
up for their own Moneytor account. The `/refresh` skill (`.claude/skills/refresh/SKILL.md`)
orchestrates pull → reason → build. Specialized agents live in `.claude/agents/`
(`statement-onboarder` for raw file formats, `classification-reasoner` for
reasoning over large residue batches).

## Coding style

Keep it boring and self-contained: vanilla Python + stdlib + openpyxl; the
report is one HTML file with inlined CSS/JS (only Chart.js from a CDN). No build
step, no framework. Match the immutable-dict style already in `classify()`
(return `{**tx, ...}`, don't mutate).
