"""
Expense-report configuration — TEMPLATE.

   cp config.example.py config.py     # then edit config.py with your real values

`config.py` is gitignored. Your names, amounts, and API tokens live ONLY in
config.py (and the gitignored .env) and never get committed. This file
(config.example.py) ships with the repo and must stay free of personal data.

Everything the engine needs to know about *you* is in this one file:
  • who the two people are and which Moneytor token env-var to use for each
  • the date window and how you split joint costs
  • a few household amounts (rent, etc.)
  • personal-name tokens used to recognise transfers between you, rent
    payments to a landlord, and salary credits

Data is fetched from the Moneytor API (not local statement files). Each person
has one Source entry whose token_env names the env var (in your .env file)
that holds that person's Moneytor JWT. The engine reads the snapshot written to
output/snapshot/<person.id>.json — that folder is gitignored.

The classification *rules* (which merchants are groceries, fuel, utilities,
subscriptions, …) live in engine/analyze.py — Claude tunes those for you
during onboarding. See the SKILL and CLAUDE.md.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date


# ─────────────────────────────────────────────────────────────────────────
# 1. PERIOD & SPLIT
# ─────────────────────────────────────────────────────────────────────────
PERIOD_START = date(2025, 10, 1)
PERIOD_END   = date(2026, 3, 31)   # inclusive
MONTHS_COUNT = 6                   # number of whole months in the window
SPLIT        = 0.5                 # each person's share of JOINT costs (0.5 = 50/50)
CURRENCY     = "₪"                 # symbol shown in the report


# ─────────────────────────────────────────────────────────────────────────
# 2. THE TWO PEOPLE  (this engine compares exactly two people)
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class Source:
    """One ingest feed for a person (the source-adapter seam, §4.5).

    kind      — which adapter. PR1 ships 'moneytor' (the Moneytor API).
                A future 'scraper' adapter (israeli-bank-scrapers) can be added
                without touching anything downstream of the snapshot.
    token_env — the NAME of the environment variable holding this person's
                Moneytor JWT (the real token lives ONLY in the gitignored .env;
                NEVER put the token here).
    account   — optional label shown in the report.
    """
    kind: str = "moneytor"
    token_env: str = ""
    account: str = ""


@dataclass
class Person:
    id: str                          # internal, stable, no spaces (e.g. "person_a")
    label: str                       # display name in the report (e.g. "Alex")
    color: str                       # hex accent colour for this person
    sources: list[Source] = field(default_factory=list)


PEOPLE = [
    Person(
        id="person_a",
        label="Person A",
        color="#5ea2ff",
        sources=[Source(kind="moneytor", token_env="MONEYTOR_TOKEN_PERSON_A", account="Moneytor")],
    ),
    Person(
        id="person_b",
        label="Person B",
        color="#ff7ea8",
        sources=[Source(kind="moneytor", token_env="MONEYTOR_TOKEN_PERSON_B", account="Moneytor")],
    ),
]


# ─────────────────────────────────────────────────────────────────────────
# 3. HOUSEHOLD AMOUNTS
#    Set an amount to 0 to disable that piece of logic entirely.
# ─────────────────────────────────────────────────────────────────────────
RENT_PER_MONTH_TOTAL   = 5400.0    # total monthly rent for the home (0 = no rent logic)
RENT_SETTLEMENT_AMOUNT = 2700.0    # one person's share, transferred to settle a month
RENTAL_INCOME_AMOUNT   = 0.0       # a recurring rental-income credit to detect (0 = none)
SALARY_MIN_AMOUNT      = 5000.0    # bank credits >= this may be salary


# ─────────────────────────────────────────────────────────────────────────
# 4. PERSONAL-NAME TOKENS  (the only place real names belong)
#    Substrings matched (case-insensitive) inside transaction descriptions.
#    Leave a list empty to skip that detection. Add as many spellings /
#    spacings as appear on your statements (banks mangle spacing).
# ─────────────────────────────────────────────────────────────────────────
# Names/phrases that mean "a transfer between the two of you" — e.g. a shared
# surname on a Bit/PayBox transfer. Used to net same-person settlements.
COUPLE_NAME_TOKENS   = ["Doe"]     # sample-data uses "Doe" — replace with your shared surname

# Your own full name as it appears when YOU move money between your OWN
# accounts. These credits are not income and not a couple transfer.
SELF_TRANSFER_TOKENS = []

# Landlord name(s) as written on a rent cheque / standing order.
LANDLORD_TOKENS      = ["Landlord"]  # sample-data uses "Landlord" — replace with your landlord's name

# Employer name or the literal word for "salary" on payslip credits.
SALARY_KEYWORDS      = ["salary"]


# ─────────────────────────────────────────────────────────────────────────
# 5. OUTPUT
# ─────────────────────────────────────────────────────────────────────────
OUTPUT_DIR  = "output"             # generated files go here (gitignored)
REPORT_NAME = "report.html"
