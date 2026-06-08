# 💸 expenses — a two-person expense dashboard

Turn a pile of bank and credit-card statements into one beautiful, self-contained
HTML dashboard that answers the questions couples and housemates actually argue
about:

- **Where did the money go?** — every transaction parsed, categorized, charted.
- **Who owes whom?** — shared costs split your way, rent reconciled, net settlement.
- **Can we afford it?** — income vs. spend, per-month burn, survival estimate.

The report is a single `output/report.html` file — open it in any browser, no
server, no account, nothing uploaded.

> ### 🔒 Your money stays yours
> This repo contains **logic only**. Your statements, your names, your numbers,
> and the generated report are all **gitignored** and never leave your machine.
> The committed code has no personal data in it — see [`CLAUDE.md`](CLAUDE.md)
> "Rule zero". Everything personal lives in `config.py`, which is gitignored.

---

## The fastest way: let Claude set it up

This project is designed to be driven by [Claude Code](https://claude.com/claude-code).
Open the repo and just say:

> **"Set up the expense report for my statements."**

Claude will run the onboarding skill — interview you about the two people, your
split, rent, and what counts as shared; help you drop your statements in the
right folders; wire up `config.py`; tune the categorization rules to your
merchants; and generate the dashboard. If your bank isn't supported yet, Claude
writes a parser for it.

(Skill: [`.claude/skills/expense-report/SKILL.md`](.claude/skills/expense-report/SKILL.md).)

## The manual way

```bash
# 1. Prereqs
pip install openpyxl
brew install poppler          # provides `pdftotext`, for PDF statements

# 2. Configure
cp config.example.py config.py
$EDITOR config.py             # set the two people, period, split, amounts, paths

# 3. Add your statements (paths are whatever config.py points at)
data/person_a/bank/...        data/person_a/cards/...
data/person_b/bank/...        data/person_b/cards/...

# 4. Generate
python3 engine/analyze.py     # → output/report.html  (+ output/transactions.csv)

# 5. Open output/report.html
```

Want to see it work first? It runs out-of-the-box against the synthetic
`sample-data/` — just `cp config.example.py config.py` and run step 4.

## What you configure

Everything personal is in **one file**, `config.py` (copied from
[`config.example.py`](config.example.py)):

| Setting | What it controls |
|---|---|
| `PEOPLE` | the two people, their labels/colors, and where each one's statements live |
| `PERIOD_START / END`, `MONTHS_COUNT` | the window to analyze |
| `SPLIT` | how joint costs divide (`0.5` = 50/50) |
| `RENT_*`, `RENTAL_INCOME_AMOUNT`, `SALARY_MIN_AMOUNT` | household amounts (set to `0` to disable) |
| `*_TOKENS`, `SALARY_KEYWORDS` | personal-name snippets that identify transfers, rent, and salary |

The *categorization rules* (which merchants are groceries vs. fuel vs.
subscriptions) live in `engine/analyze.py` and are meant to be tuned — ask Claude,
or edit the labeled lists yourself.

## Supported statement formats

Built-in parsers (Israeli banks, since that's where this started):

- **Isracard** credit-card `.xlsx` export
- **Isracard** monthly `.pdf` statement (`YYYY-MM.pdf`)
- **Bank Leumi** account `.pdf`
- **Bank Discount** `.csv` export and account `.pdf`

Another bank? Each parser is ~40 lines that normalize one format into a common
transaction shape. See [`CLAUDE.md`](CLAUDE.md) → "Adding a bank or card parser",
or just ask Claude to add one from a sample of your statement.

## How it splits money (the model)

- **Shared** costs (groceries, utilities, household, furniture) are split by `SPLIT`.
- **Personal** costs (fuel, phone, gym, subscriptions, vehicle, insurance,
  fashion, pharmacy…) stay with whoever paid.
- **Rent** is reconciled separately: it detects who paid the landlord each month
  and nets the settlement transfers between you.
- **Restaurants & vacations** are pooled and shown, but not forced into the split.
- **Income, loans, and transfers** (Bit/PayBox/ATM/fees) are tracked but kept out
  of the spending totals.
- Anything that doesn't match a rule is **flagged** for you to decide.

You can change any of this — it's your definition of "fair".

## ⚠️ Disclaimer

This is a personal-finance helper built on heuristics (especially the Hebrew/PDF
parsing and the auto-categorization). **Check the numbers before you settle up.**
The `Flagged` section and `output/transactions.csv` exist precisely so you can
audit every classification. Not financial advice.
