"""
Generate SYNTHETIC sample statements so the repo runs out-of-the-box.

Everything here is fake — invented people ("J. Doe"), invented amounts, and
public brand names used only so the demo exercises the categorization rules.
Run from the repo root:

    python3 sample-data/generate.py

It writes Isracard-style .xlsx card exports and Discount-style .csv bank
exports under sample-data/person_a and sample-data/person_b. These match the
formats config.example.py points at.
"""
from __future__ import annotations
from pathlib import Path
import openpyxl

HERE = Path(__file__).resolve().parent

# Isracard .xlsx export: header sits on the 4th row; these are the column names
# the parser looks up.
XLSX_HEADER = [
    'תאריך עסקה', 'שם בית העסק', 'קטגוריה',
    '4 ספרות אחרונות של כרטיס האשראי', 'סוג עסקה', 'סכום חיוב',
    'מטבע חיוב', 'סכום עסקה מקורי', 'מטבע עסקה מקורי', 'תאריך חיוב', 'הערות',
]

# (tx_date, merchant, category, amount)  → bill_date is set per file
PERSON_A_CARD = [
    ('05/11/2025', 'שופרסל דיל',  'מכולת/סופר',          452.30),  # shared grocery
    ('07/11/2025', 'פז יילו',     'דלק',                 300.00),  # personal fuel
    ('12/11/2025', 'קפה גרג',     'מסעדות, קפה וברים',    88.00),  # restaurant
    ('15/11/2025', 'NETFLIX.COM', 'פנאי',                 54.90),  # personal subscription
    ('18/11/2025', 'CLAUDE.AI',   'שונות',                72.00),  # business / SaaS
    ('20/11/2025', 'איקאה',       'בית וגן',             640.00),  # shared furniture
    ('22/11/2025', 'חנות אקראית', 'שונות',               210.00),  # ambiguous → flagged
]
PERSON_B_CARD = [
    ('04/11/2025', 'רמי לוי',     'מכולת/סופר',          388.10),  # shared grocery
    ('09/11/2025', 'סונול',       'דלק',                 260.00),  # personal fuel
    ('14/11/2025', 'מסעדת מזרח',  'מסעדות, קפה וברים',   142.00),  # restaurant
    ('16/11/2025', 'SPOTIFY',     'פנאי',                 19.90),  # personal subscription
    ('21/11/2025', 'סופר פארם',   'פארמה',               95.50),  # personal pharmacy
    ('24/11/2025', 'בוטיק כלשהו', 'אופנה',               320.00),  # personal fashion
]


def write_xlsx(path: Path, rows, card4: str, bill_date: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'עסקאות בארץ'
    ws.append(['Synthetic sample — not real data'])   # row 1
    ws.append([])                                      # row 2
    ws.append([])                                      # row 3
    ws.append(XLSX_HEADER)                             # row 4 (header)
    for tx_date, merchant, category, amount in rows:
        ws.append([tx_date, merchant, category, card4, 'רגילה',
                   amount, '₪', amount, '₪', bill_date, ''])
    wb.save(path)


def write_discount_csv(path: Path, rows):
    """rows: list of (date, desc, signed_amount). UTF-16-LE, tab-delimited."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ['תאריך\tיום ערך\tתיאור התנועה\tזכות/חובה\tיתרה']
    bal = 20000.0
    for d, desc, amt in rows:
        bal += amt
        lines.append(f'{d}\t{d}\t{desc}\t{amt:.2f}\t{bal:.2f}')
    path.write_text('\n'.join(lines), encoding='utf-16')


def main():
    # Cards — two bill months so the monthly trend has shape.
    write_xlsx(HERE / 'person_a/cards/isracard-2025-11.xlsx', PERSON_A_CARD, '1234', '10/11/2025')
    write_xlsx(HERE / 'person_a/cards/isracard-2025-12.xlsx',
               [(d.replace('/11/', '/12/'), m, c, round(a * 0.9, 2)) for d, m, c, a in PERSON_A_CARD],
               '1234', '10/12/2025')
    write_xlsx(HERE / 'person_b/cards/isracard-2025-11.xlsx', PERSON_B_CARD, '5678', '10/11/2025')
    write_xlsx(HERE / 'person_b/cards/isracard-2025-12.xlsx',
               [(d.replace('/11/', '/12/'), m, c, round(a * 1.1, 2)) for d, m, c, a in PERSON_B_CARD],
               '5678', '10/12/2025')

    # Bank — salary in, rent to landlord, a settlement transfer, ordinary debits.
    write_discount_csv(HERE / 'person_a/bank/discount.csv', [
        ('01/11/2025', 'Monthly salary',        12000.00),
        ('03/11/2025', 'Rent cheque Landlord',  -5400.00),
        ('10/11/2025', 'Rent settlement Doe',   -2700.00),
        ('15/11/2025', 'Supermarket POS',        -250.00),
        ('01/12/2025', 'Monthly salary',        12000.00),
        ('15/12/2025', 'Supermarket POS',        -240.00),
    ])
    write_discount_csv(HERE / 'person_b/bank/discount.csv', [
        ('01/11/2025', 'Monthly salary',         9000.00),
        ('10/11/2025', 'Transfer from Doe',      2700.00),
        ('18/11/2025', 'Pharmacy POS',           -120.00),
        ('01/12/2025', 'Monthly salary',         9000.00),
    ])
    print('Wrote synthetic sample statements under', HERE)


if __name__ == '__main__':
    main()
