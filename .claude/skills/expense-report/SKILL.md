---
name: expense-report
description: Use when setting up or generating the two-person expense dashboard in this repo — onboarding a new user's Moneytor account, configuring config.py, reasoning over ambiguous transactions, or (re)building output/report.html. Triggers include "set up expenses", "analyze our spending", "who owes whom", "build the expense report", "refresh expenses".
---

# Expense report onboarding & generation

Goal: get a new user from "a Moneytor account" to "an accurate
`output/report.html`" with minimum friction. You do the config/reasoning/tuning;
the user just answers questions and provides their Moneytor credentials.

## 🔒 Carry Rule Zero through every step

Never write a real name, amount, account number, or token into a committed
file. All personal values go in `config.py` and `.env` (both gitignored).
If the repo isn't a fresh clone, confirm `.gitignore` is present and run
`python3 engine/refresh.py --preflight` before anything else.
Read [`CLAUDE.md`](../../../CLAUDE.md) if you haven't this session.

## Checklist (make a TodoWrite from this)

1. **Prereqs** — confirm `python3` and `openpyxl` (`pip install openpyxl`).
2. **Interview** — ask the questions below. Don't assume; people split money in
   very different ways.
3. **Write `config.py`** — from `config.example.py`, filled with their answers.
   Set each `Source(kind="moneytor", token_env="MONEYTOR_TOKEN_A")` entry.
4. **Write `.env`** — add each person's Moneytor JWT:
   `MONEYTOR_TOKEN_A=<token>` / `MONEYTOR_TOKEN_B=<token>` (gitignored; never
   commit or echo these).
5. **Run `/refresh`** — this pulls data, runs the regex first-pass, lets you
   reason over the ambiguous residue, and builds the report. See the
   `.claude/skills/refresh/SKILL.md` runbook. Delegate to the
   `classification-reasoner` agent for large residue batches.
6. **Deliver** — open `output/report.html`, walk the user through it, iterate.

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
- **Income** — salary keyword or employer name that appears in Moneytor? Any
  other recurring income (rental, dividends)? (→ `SALARY_KEYWORDS`,
  `RENTAL_INCOME_AMOUNT`)
- **Inter-person transfers** — do they Bit/PayBox/Venmo each other? What name or
  note shows up in their transactions? (→ `COUPLE_NAME_TOKENS`, used to net
  settlements and avoid double-counting.)

## Writing config.py

`cp config.example.py config.py`, then fill in `PEOPLE` (ids MUST stay
`person_a`/`person_b` — change `label`, not `id`), the period/split/amounts, and
the name-token lists from the interview. Set each `Source(kind="moneytor",
token_env="MONEYTOR_TOKEN_<X>")` where `token_env` names the env var in `.env`.

## Writing .env

Create `.env` (gitignored) in the repo root:
```
MONEYTOR_TOKEN_A=<person_a's JWT>
MONEYTOR_TOKEN_B=<person_b's JWT>
```
Never echo or paste these in chat. Run `python3 engine/refresh.py --preflight`
to confirm `.env` is not tracked before running anything else.

## Running & tuning

```bash
python3 engine/refresh.py --preflight   # Rule Zero gate — must exit 0
python3 engine/refresh.py --pull        # fetch both people → output/snapshot/
# reason over output/residue.json (you, or fork classification-reasoner)
python3 engine/analyze.py               # → output/report.html
```

For subsequent refreshes, `/refresh` (the skill) orchestrates these steps.
A plain `python3 engine/analyze.py` rebuild is offline and reuses `output/decisions.json`
— no network, no re-reasoning.

## Delivering

Open the report, walk the "Bottom line" / settlement, and ask the user to verify
the rent reconciliation and any large flagged items. Iterate on config or residue
decisions as they react. Remind them the report, snapshot, and `.env` are local-only.
