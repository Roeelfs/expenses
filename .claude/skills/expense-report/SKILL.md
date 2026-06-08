---
name: expense-report
description: Use when setting up or generating the two-person expense dashboard in this repo — onboarding a new user's bank/credit-card statements, configuring config.py, tuning categorization, or (re)building output/report.html. Triggers include "set up expenses", "analyze our spending", "who owes whom", "build the expense report", "add my statements".
---

# Expense report onboarding & generation

Goal: get a new user from "a pile of statements" to "an accurate
`output/report.html`" with minimum friction. You do the parsing/config/tuning;
the user just answers questions and drops files.

## 🔒 Carry Rule Zero through every step

Never write a real name, amount, account number, or merchant into a committed
file. All personal values go in `config.py` (gitignored). Statements go in
`data/` (gitignored). If the repo isn't a fresh clone, confirm `.gitignore` is
present before anything else. Read [`CLAUDE.md`](../../../CLAUDE.md) if you
haven't this session.

## Checklist (make a TodoWrite from this)

1. **Prereqs** — confirm `python3`, `openpyxl` (`pip install openpyxl`), and
   `pdftotext` (`brew install poppler`) if any statements are PDFs.
2. **Interview** — ask the questions below. Don't assume; people split money in
   very different ways.
3. **Collect statements** — have the user place exports under `data/<person>/`.
   Inspect each format before trusting it.
4. **Write `config.py`** — from `config.example.py`, filled with their answers
   and file globs.
5. **Parsers** — if a statement format isn't supported, add a parser (delegate
   to the `statement-onboarder` agent or do it inline).
6. **First run** — `python3 engine/analyze.py`; sanity-check totals.
7. **Tune** — work the `flag` bucket and fix misclassifications (delegate to the
   `classification-tuner` agent for big batches).
8. **Deliver** — open `output/report.html`, walk the user through it, iterate.

## The interview

Ask these up front (batch them; offer sensible defaults):

- **The two people** — names (become `label`), and a color each if they care.
- **Currency** and the **date window** (which whole months to analyze).
- **Split** — 50/50? Income-proportional? Some other ratio? (`SPLIT`)
- **Rent/housing** — Is there shared rent? How much/month? How is it paid (one
  person pays the landlord and the other reimburses? both pay directly?)? What's
  the reimbursement amount? (→ `RENT_PER_MONTH_TOTAL`, `RENT_SETTLEMENT_AMOUNT`;
  set to `0` if N/A.)
- **What's shared vs. personal** — the big philosophy question. Common splits:
  groceries/utilities/household = shared; fuel/phone/gym/subscriptions/insurance/
  vehicle = personal. Confirm their version. Ask about pets, furniture, dining
  out, travel.
- **Income** — where do salaries land (which account)? Any other recurring
  income (rental, dividends)? Salary keyword/employer on the statement?
- **Inter-person transfers** — do they Bit/PayBox/Venmo each other? What name or
  note shows up? (→ `*_TOKENS`, used to net settlements and avoid
  double-counting.)

## Collecting & identifying statements

For each person, create `data/<person_a>/{bank,cards}` etc. and have them drop
exports there. For every distinct format, look before you parse:

```bash
pdftotext -layout "data/person_a/bank/example.pdf" - | head -50   # PDF layout
python3 -c "import openpyxl,sys; wb=openpyxl.load_workbook(sys.argv[1]); ws=wb.active; [print(r) for r in list(ws.iter_rows(values_only=True))[:8]]" "data/.../file.xlsx"
```

Match each file to a `Source(kind=..., glob=...)`. Supported `kind`s are listed
in `config.example.py`. Unsupported → add a parser (step 5).

## Writing config.py

`cp config.example.py config.py`, then fill in `PEOPLE` (ids MUST stay
`person_a`/`person_b` — change `label`, not `id`), the period/split/amounts, and
the name-token lists from the interview. Point each `Source.glob` at the files
the user actually provided.

## Running & tuning

```bash
python3 engine/analyze.py          # → output/report.html, output/transactions.csv
```

Then open `output/transactions.csv` and filter `status == flag` — these are the
transactions no rule matched. For each, decide shared/personal/etc. and edit the
rule lists in `engine/analyze.py` (see CLAUDE.md → taxonomy). Re-run. Repeat
until the flagged bucket is small and the totals look right. Spot-check a few
known transactions against the source statements — the parsing is heuristic.

## Delivering

Open the report, walk the "Bottom line" / settlement, and ask the user to verify
the rent reconciliation and any large flagged items. Iterate on rules or config
as they react. Remind them the report and their config are local-only.
