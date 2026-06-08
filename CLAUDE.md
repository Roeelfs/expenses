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
- Statements live in **`data/`** (gitignored) or wherever `config.py` points.
- Generated reports + the intermediate CSV go to **`output/`** (gitignored).
- `.gitignore` also refuses *any* `.pdf/.xlsx/.csv` outside `sample-data/`.
- Before any `git add`/commit, run `git status` and confirm no statement,
  no `config.py`, no `output/` file, and no real name/amount is staged.
- Never paste a real name, account number, salary, or merchant from someone's
  data into a committed file (code, comment, README, or sample). If you need an
  example, invent a synthetic one.

If you ever notice PII in a tracked file, stop and fix it before anything else.

## Architecture (3 files)

```
config.py            # ALL personal knobs: people, period, split, amounts, name tokens, file globs
engine/analyze.py    # parse statements → normalize → classify → settlement math → calls render
engine/render.py     # build the single-file HTML dashboard (Chart.js, dark theme)
```

Pipeline: `config.py` → `analyze.load_all()` (parse every source) →
`classify()` (tag each transaction) → aggregations + settlement math in
`main()` → `render.build_html(**ctx)` → `output/report.html`.

Run it from the repo root:

```bash
python3 engine/analyze.py        # writes output/report.html + output/transactions.csv
```

Requires `python3`, `openpyxl` (`pip install openpyxl`), and `pdftotext`
(`brew install poppler`) for PDF statements.

## The two people

The engine compares **exactly two** people, with fixed internal ids
**`person_a`** and `person_b` (used as dict keys throughout both files). In
`config.py` you may change each person's `label` (display name) and `color`, but
**not** the `id`. `analyze.py` asserts this on startup.

## Data layout

Each person has a `data_dir` containing their statements, grouped however you
like; `config.py` `sources` point at them with globs:

```
data/person_a/
  bank/   leumi-statement.pdf
  cards/  isracard-2025-10.xlsx ...
data/person_b/
  bank/   discount-export.csv
  cards/  ...
```

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
- **flag** — didn't match a rule; surfaced for a human decision

The rules are plain Python lists/regexes near the top of `analyze.py`
(`UTILITY_RULES`, `FUEL_MERCHANT_RE`, `SHARED_CATEGORIES`, `PERSONAL_CATEGORIES`,
`BUSINESS_MERCHANT_RE`, `SHARED_MERCHANT_PATTERNS`, `AMBIGUOUS_CATEGORIES`, …).
**Tuning these for a new user is expected work** — read their `flag` bucket in
`output/transactions.csv`, decide each, and move merchants/categories into the
right list. Personal names for couple-transfer / landlord / salary detection are
NOT in the engine — they come from `config.py` token lists.

## Adding a bank or card parser

The built-in parsers target Israeli formats (Isracard xlsx/pdf, Leumi pdf,
Discount csv/pdf). To support another bank:

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
up for their own statements. Specialized agents live in `.claude/agents/`
(`statement-onboarder`, `classification-tuner`).

## Coding style

Keep it boring and self-contained: vanilla Python + stdlib + openpyxl; the
report is one HTML file with inlined CSS/JS (only Chart.js from a CDN). No build
step, no framework. Match the immutable-dict style already in `classify()`
(return `{**tx, ...}`, don't mutate).
