"""The LLM reasoning contract: a committed data-free RUBRIC, the output schema,
and runtime builders that inject real config.py amounts/tokens (NEVER committed).
See spec section 5.4. The RUBRIC's hash is the store's rubric_hash invalidation key.
"""
from __future__ import annotations
import hashlib

STATUS_VALUES = ["shared", "personal", "rent", "landlord_rent", "restaurant",
                 "vacation", "business", "loan", "earnings", "rental_income",
                 "transfer", "refund", "flag"]

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
- flag: cannot decide -- surface for a human.
Use the provided name tokens and amount constants to disambiguate landlord_rent vs a
couple transfer (often the same counterparty, differing only by amount). Prefer the
already-decided sibling examples for consistency. If unsure, return status='flag'.
"""


def rubric_hash() -> str:
    return hashlib.sha256(RUBRIC.encode("utf-8")).hexdigest()


def build_context(config) -> dict:
    """Render runtime config (real amounts/tokens) -- never committed, never logged raw."""
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


def build_input(tx: dict, decided_siblings: list) -> dict:
    return {
        "id": tx["id"], "owner": tx.get("owner"),
        "merchant": tx.get("merchant", ""), "extra_info": tx.get("notes", ""),
        "amount": tx.get("amount"), "signed_direction": tx.get("sub_type", ""),
        "moneytor_category": tx.get("moneytor_category", ""), "type": tx.get("type", ""),
        "siblings": decided_siblings[:5],
        "decision_schema": {"status": STATUS_VALUES, "tag": "string", "reason": "string",
                            "category": "string (Hebrew display label)"},
    }
