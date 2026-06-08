"""Premium dark-mode expense dashboard renderer.
Single HTML file. Vanilla JS + Chart.js. Inter font. OLED dark theme.
Person labels, accent colours, and currency all come from config.py."""
from __future__ import annotations
import html, json, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `import config` works
import config as C

CUR = C.CURRENCY
LA  = C.PEOPLE[0].label     # person_a display name
LB  = C.PEOPLE[1].label     # person_b display name
CA  = C.PEOPLE[0].color     # person_a accent colour
CB  = C.PEOPLE[1].color     # person_b accent colour

def nis(v: float) -> str:
    return f'{CUR}{v:,.0f}'

def nis2(v: float) -> str:
    return f'{CUR}{v:,.2f}'

OWNER_COLOR = {'person_a': CA, 'person_b': CB}

# ─── Inline SVG icons (Lucide-style) ────────────────────────────────────────

ICONS = {
    'overview':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>',
    'split':      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3v18M18 3v18M3 12h18"/></svg>',
    'income':     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    'home':       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    'car':        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M14 16H9m10 0h3v-3.15a1 1 0 0 0-.84-.99L16 11l-2.7-3.6a1 1 0 0 0-.8-.4H5.24a2 2 0 0 0-1.8 1.1L2 11v5h3"/><circle cx="6.5" cy="16.5" r="2.5"/><circle cx="16.5" cy="16.5" r="2.5"/></svg>',
    'business':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    'loan':       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>',
    'sofa':       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M20 9V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v2M4 13h16M4 13v5a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5M4 13a3 3 0 0 0-3 3v2h2M20 13a3 3 0 0 1 3 3v2h-2"/></svg>',
    'plane':      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M17.8 19.2L16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/></svg>',
    'utensils':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2M7 2v20M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3zm0 0v7"/></svg>',
    'flag':       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>',
    'transfer':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M17 1l4 4-4 4M3 11V9a4 4 0 0 1 4-4h14M7 23l-4-4 4-4M21 13v2a4 4 0 0 1-4 4H3"/></svg>',
    'info':       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    'check':      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    'arrow_right':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
    'electric':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    'water':      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>',
    'fire':       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>',
    'wifi':       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a11 11 0 0 1 14.08 0M1.42 9a16 16 0 0 1 21.16 0M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01"/></svg>',
    'building':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M16 6h.01M8 10h.01M16 10h.01M8 14h.01M16 14h.01"/></svg>',
    'cart':       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>',
}

def icon(name: str, cls: str = '') -> str:
    svg = ICONS.get(name, '')
    if cls:
        svg = svg.replace('<svg ', f'<svg class="{cls}" ')
    return svg

# ─── Helpers ─────────────────────────────────────────────────────────────────

def pill(text: str, kind: str) -> str:
    return f'<span class="pill pill-{kind}">{html.escape(text)}</span>'

def kpi_card(label, value, delta='', color=None, sparkline_data=None, icon_name=None):
    color_style = f'color:{color}' if color else ''
    spark = ''
    if sparkline_data:
        spark = f'<canvas class="sparkline" data-spark=\'{json.dumps(sparkline_data)}\' data-color="{color or "var(--ink-2)"}"></canvas>'
    ic = f'<div class="kpi-icon">{icon(icon_name)}</div>' if icon_name else ''
    return f'''<div class="card kpi-card">
      {ic}
      <div class="kpi-label">{label}</div>
      <div class="kpi-value counter" data-target="{value if isinstance(value,(int,float)) else 0}" style="{color_style}">{value if isinstance(value,str) else nis(value)}</div>
      {f'<div class="kpi-delta">{delta}</div>' if delta else ''}
      {spark}
    </div>'''

_table_counter = [0]

def tx_row(t, show_owner=True, show_reason=False, idx=0):
    own_td = f"<td data-owner='{t['owner']}'>{pill(t['owner'], t['owner'])}</td>" if show_owner else ''
    reason_td = f"<td class='muted small reason'>{html.escape(t.get('reason',''))}</td>" if show_reason else ''
    amount = t.get('amount', 0)
    return f"""<tr style="--row-i:{idx}" data-owner="{t.get('owner','')}" data-search="{html.escape((t.get('merchant','')+' '+t.get('category','')+' '+t.get('reason','')).lower())}">
      <td class='small mono'>{t.get('bill_date','')}</td>
      {own_td}
      <td class='he merchant'>{html.escape(t.get('merchant',''))}</td>
      <td class='he muted small cat'>{html.escape(t.get('category',''))}</td>
      <td class='num mono' data-amount="{amount}">{nis2(amount)}</td>
      {reason_td}
    </tr>"""

def table_card(headers, body_rows, max_h=520, sortable=True, filterable=True, amount_col=None):
    """Render a table with built-in filter bar + sum total + sortable headers.
    amount_col: 0-indexed column to sum (default: auto-detect the numeric column)."""
    _table_counter[0] += 1
    tid = f't{_table_counter[0]}'
    # Auto-detect amount column = last column with ₪ or 'num' style — default to last data column
    if amount_col is None:
        for i, h in enumerate(headers):
            if '₪' in h or 'amount' in h.lower() or h.strip() in ('₪',):
                amount_col = i; break
        if amount_col is None: amount_col = len(headers) - 1
    head_cells = ''.join(f'<th data-col="{i}">{h}</th>' for i,h in enumerate(headers))
    style = f'max-height:{max_h}px' if max_h else ''
    sort_attr = ' data-sortable="1"' if sortable else ''
    filter_bar = ''
    if filterable:
        filter_bar = f'''<div class="table-filter">
          <div class="filter-input-wrap">
            <svg class="filter-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="search" class="filter-input" placeholder="Filter merchant, category…" aria-label="Filter table" data-table="{tid}">
            <button class="filter-clear" data-table="{tid}" aria-label="Clear filter" type="button">×</button>
          </div>
          <div class="filter-stats" data-table="{tid}">
            <span class="stat-chip"><span class="stat-label">items</span> <span class="stat-val" data-stat="count">0</span></span>
            <span class="stat-chip primary"><span class="stat-label">sum</span> <span class="stat-val mono" data-stat="sum">₪0</span></span>
          </div>
        </div>'''
    return f'''<div class="table-card" data-table-id="{tid}" data-amount-col="{amount_col}">
      {filter_bar}
      <div class="scroll" style="{style}">
        <table{sort_attr}>
          <thead><tr>{head_cells}</tr></thead>
          <tbody>{body_rows}</tbody>
        </table>
      </div>
    </div>'''

# ─── Build the entire HTML ───────────────────────────────────────────────────

def build_html(**ctx) -> str:
    # Extract ALL context (keep compatible with analyze.py)
    totals = ctx['totals']
    by_status = ctx['by_status']
    by_tag = ctx['by_tag']
    by_month = ctx['by_month']
    utilities = ctx['utilities']
    flagged = ctx['flagged']
    shared_items = ctx['shared_items']
    personal_items = ctx['personal_items']
    transfers = ctx['transfers']
    rent_settlements = ctx['rent_settlements']
    rent_r2a = ctx['rent_person_a_to_person_b']
    rent_a2r = ctx['rent_person_b_to_person_a']
    final_delta = ctx['final_delta']
    delta = ctx['delta']
    assumed_rent_total = ctx['assumed_rent_total']
    assumed_rent_each = ctx['assumed_rent_each']
    landlord_payments = ctx['landlord_payments']
    person_a_landlord_months = ctx['person_a_landlord_months']
    person_b_landlord_months = ctx.get('person_b_landlord_months', [])
    person_a_landlord_count = ctx['person_a_landlord_count']
    person_b_landlord_count = ctx['person_b_landlord_count']
    person_a_landlord_paid = ctx['person_a_landlord_paid']
    person_b_landlord_paid_inferred = ctx['person_b_landlord_paid_inferred']
    rent_remaining_owed_to_person_a = ctx['rent_remaining_owed_to_person_a']
    rent_strict_owed_to_person_a = ctx.get('rent_strict_owed_to_person_a', 0)
    person_a_rent_contribution = ctx.get('person_a_rent_contribution', 0)
    shared_cards_person_a = ctx['shared_cards_person_a']
    shared_cards_person_b = ctx['shared_cards_person_b']
    shared_cards_total = ctx['shared_cards_total']
    bank_credits = ctx['bank_credits']
    earnings_person_a_total = ctx['earnings_person_a_total']
    earnings_person_a_salary = ctx['earnings_person_a_salary']
    earnings_person_a_rental = ctx['earnings_person_a_rental']
    earnings_person_a_other = ctx['earnings_person_a_other']
    earnings_person_b_total = ctx.get('earnings_person_b_total', 0)
    earnings_person_b_salary = ctx.get('earnings_person_b_salary', 0)
    earnings_person_b_other = ctx.get('earnings_person_b_other', 0)
    person_b_credits = ctx.get('person_b_credits', [])
    restaurants = ctx['restaurants']
    vacations = ctx['vacations']
    rest_total = ctx['rest_total']
    rest_by_owner = ctx['rest_by_owner']
    vac_total = ctx['vac_total']
    vac_by_owner = ctx['vac_by_owner']
    cars = ctx['cars']
    car_totals = ctx['car_totals']
    car_breakdown_r = ctx['car_breakdown_r']
    car_breakdown_a = ctx['car_breakdown_a']
    subs = ctx['subs']
    gyms = ctx['gyms']
    subs_total = ctx['subs_total']
    gyms_total = ctx['gyms_total']
    top_cats = ctx['top_cats']
    months_count = ctx['months_count']
    shared_total = ctx['shared_total']
    each_should_pay = ctx['each_should_pay']
    avg_shared = ctx['avg_shared_per_month']
    avg_personal = ctx['avg_personal']
    furniture = ctx.get('furniture', [])
    furniture_total = ctx.get('furniture_total', 0)
    furniture_by_owner = ctx.get('furniture_by_owner', {'person_a':0,'person_b':0})
    business = ctx.get('business', [])
    business_total = ctx.get('business_total', 0)
    business_by_owner = ctx.get('business_by_owner', {'person_a':0,'person_b':0})
    loans_summary = ctx.get('loans_summary', [])
    loans_raw = ctx.get('loans_raw', [])
    loans_total_repaid = ctx.get('loans_total_repaid', 0)
    loans_total_received = ctx.get('loans_total_received', 0)
    baseline = ctx.get('baseline', {})

    flag_total = sum(t['amount'] for t in flagged)
    transfers_total = sum(t['amount'] for t in transfers)
    total_burn = totals['person_a'] + totals['person_b'] + assumed_rent_total
    monthly_burn = total_burn / months_count
    total_income = earnings_person_a_total + earnings_person_b_total

    # Settlement direction text
    if final_delta > 0:
        settle_who, settle_to, settle_amt = LB, LA, abs(final_delta)
    elif final_delta < 0:
        settle_who, settle_to, settle_amt = LA, LB, abs(final_delta)
    else:
        settle_who, settle_to, settle_amt = None, None, 0

    # Monthly chart data
    months = sorted(by_month.keys())
    month_labels = [datetime.strptime(m, '%Y-%m').strftime('%b %y') for m in months]
    shared_pm = [by_month[m]['shared']['person_a'] + by_month[m]['shared']['person_b'] for m in months]
    personal_pm = [by_month[m]['personal']['person_a'] + by_month[m]['personal']['person_b'] for m in months]
    rest_pm = [by_month[m].get('restaurant',{}).get('person_a',0) + by_month[m].get('restaurant',{}).get('person_b',0) for m in months]
    vac_pm = [by_month[m].get('vacation',{}).get('person_a',0) + by_month[m].get('vacation',{}).get('person_b',0) for m in months]
    flag_pm = [by_month[m].get('flag',{}).get('person_a',0) + by_month[m].get('flag',{}).get('person_b',0) for m in months]
    person_a_pm = [sum(by_month[m].get(s,{}).get('person_a',0) for s in ('shared','personal','restaurant','vacation','flag')) for m in months]
    person_b_pm = [sum(by_month[m].get(s,{}).get('person_b',0) for s in ('shared','personal','restaurant','vacation','flag')) for m in months]
    earnings_pm = []
    for m in months:
        amt = 0
        for t in bank_credits:
            if t['bill_date'].startswith(m): amt += t['amount']
        earnings_pm.append(amt)

    cat_labels = [c for c,_ in top_cats]
    cat_data = [v for _,v in top_cats]

    # ─── Build section content ───────────────────────────────────────────

    # Settlement breakdown
    settle_pieces = []
    if delta != 0:
        d_who = LA if delta<0 else LB
        d_to = LB if delta<0 else LA
        settle_pieces.append(f'<div class="settle-piece"><div class="piece-label">Cards shared spending</div><div class="piece-amt {("danger" if delta<0 else "income")}">{d_who} → {d_to} <strong>{nis(abs(delta))}</strong></div></div>')
    if rent_remaining_owed_to_person_a != 0:
        r_who = LB if rent_remaining_owed_to_person_a>0 else LA
        r_to = LA if rent_remaining_owed_to_person_a>0 else LB
        settle_pieces.append(f'<div class="settle-piece"><div class="piece-label">Rent debt remaining</div><div class="piece-amt">{r_who} → {r_to} <strong>{nis(abs(rent_remaining_owed_to_person_a))}</strong></div></div>')
    else:
        settle_pieces.append(f'<div class="settle-piece"><div class="piece-label">Rent settlement</div><div class="piece-amt muted">Net 0 (assumed self-balancing)</div></div>')

    settlement_arrow_html = ''
    if settle_who:
        settlement_arrow_html = f'''<div class="settle-arrow">
          <div class="settle-from {settle_who.lower()}">
            <span class="settle-name">{settle_who}</span>
            <span class="settle-role">owes</span>
          </div>
          <div class="settle-mid">{icon('arrow_right')}<div class="settle-mid-amt">{nis(settle_amt)}</div></div>
          <div class="settle-to {settle_to.lower()}">
            <span class="settle-name">{settle_to}</span>
            <span class="settle-role">receives</span>
          </div>
        </div>'''
    else:
        settlement_arrow_html = '<div class="settle-even"><div class="settle-mid-amt">Even — no settlement needed</div></div>'

    # Top category rows
    cat_rows_html = ''.join(
        f'<tr><td class="he">{html.escape(c)}</td><td class="num mono">{nis(v)}</td><td class="num small muted">{round(100*v/sum(cat_data))}%</td></tr>'
        for c,v in top_cats[:10]
    )

    # Build per-section row strings
    shared_rows = ''.join(tx_row(t, show_owner=True, show_reason=True, idx=i) for i,t in enumerate(sorted(shared_items, key=lambda x:-x['amount'])))
    flag_rows = ''.join(tx_row(t, show_owner=True, show_reason=True, idx=i) for i,t in enumerate(flagged[:100]))
    vac_rows = ''.join(tx_row(t, idx=i) for i,t in enumerate(sorted(vacations, key=lambda x:-x['amount'])))
    rest_rows = ''.join(tx_row(t, idx=i) for i,t in enumerate(sorted(restaurants, key=lambda x:-x['amount'])))
    furniture_rows = ''.join(tx_row(t, idx=i) for i,t in enumerate(sorted(furniture, key=lambda x:-x['amount'])))
    business_rows = ''.join(tx_row(t, idx=i) for i,t in enumerate(sorted(business, key=lambda x:-x['amount'])))
    transfer_rows = ''.join(tx_row(t, idx=i) for i,t in enumerate(sorted(transfers, key=lambda x:-x['amount'])))

    # Earnings rows
    earnings_rows_list = []
    kind_pill = {'salary':'shared','rental':'income','other':'flag'}
    kind_label = {'salary':'salary','rental':'rental income','other':'review'}
    for i,t in enumerate(sorted(bank_credits, key=lambda x: -x['amount'])):
        k = t.get('earnings_kind','other')
        earnings_rows_list.append(
            f"<tr style='--row-i:{i}'><td class='small mono'>{t['bill_date']}</td>"
            f"<td>{pill(t['owner'], t['owner'])}</td>"
            f"<td class='he merchant'>{html.escape(t['merchant'])}</td>"
            f"<td class='num mono'>{nis2(t['amount'])}</td>"
            f"<td>{pill(kind_label[k], kind_pill[k])}</td></tr>")
    earnings_rows = ''.join(earnings_rows_list)

    # Rent settlement timeline rows
    rent_timeline_rows = ''
    combined = sorted(rent_settlements + landlord_payments, key=lambda x:x['bill_date'])
    for i,t in enumerate(combined):
        if t['status'] == 'landlord_rent':
            badge = pill('🏠 landlord', 'income')
            direction = f"{LA if t['owner']=='person_a' else LB} → Landlord"
        else:
            badge = pill('settlement', 'shared')
            is_r2a = (t['owner']=='person_a' and t.get('sub_type')=='debit') or (t['owner']=='person_b' and t.get('sub_type')=='credit')
            direction = f'{LA} → {LB}' if is_r2a else f'{LB} → {LA}'
        rent_timeline_rows += f"<tr style='--row-i:{i}'><td class='small mono'>{t['bill_date']}</td><td>{direction}</td><td>{badge}</td><td class='num mono'>{nis2(t['amount'])}</td></tr>"

    # Per-car section
    def car_block(owner):
        items = cars[owner]
        bd = car_breakdown_r if owner == 'person_a' else car_breakdown_a
        total = car_totals[owner]
        rows = ''.join(f'<tr><td>{html.escape(k)}</td><td class="num mono">{nis(v)}</td></tr>' for k,v in sorted(bd.items(), key=lambda x:-x[1]))
        item_rows_html = ''.join(tx_row(t, show_owner=False, idx=i) for i,t in enumerate(sorted(items, key=lambda x:-x['amount'])[:25]))
        return f'''<div class="card glow-{owner}">
          <div class="card-hd">
            <h3 class="card-title"><span class="dot {owner}"></span>{owner.title()}'s car</h3>
            <div class="kpi-value" style="color:{OWNER_COLOR[owner]};font-size:24px;font-weight:700">{nis(total)}</div>
          </div>
          <table class="mini">
            <tbody>{rows or '<tr><td colspan="2" class="muted">No items</td></tr>'}</tbody>
          </table>
          <details>
            <summary class="muted small">View {len(items)} transactions</summary>
            <div class="scroll" style="max-height:280px;margin-top:10px">
              <table><thead><tr><th>Date</th><th>Merchant</th><th>Cat</th><th class="num">₪</th></tr></thead>
              <tbody>{item_rows_html}</tbody></table>
            </div>
          </details>
        </div>'''

    # Loans section
    loans_section_html = ''
    if loans_summary:
        loan_rows = []
        for l in sorted(loans_summary, key=lambda x:-x['repaid']):
            out = l['outstanding_estimate']
            out_txt = nis(out) if out is not None else '<span class="muted">unknown</span>'
            loan_rows.append(f'''<tr>
              <td><span class="dot {l['owner']}"></span><strong>{l['owner'].title()}</strong></td>
              <td class="small muted mono">#{l['loan_id']}</td>
              <td class="num mono">{nis(l['received']) if l['received'] else '<span class="muted">—</span>'}</td>
              <td class="num mono">{nis(l['repaid'])}</td>
              <td class="num mono"><strong>{out_txt}</strong></td>
              <td class="num small muted">{l['repayment_count']}× ~{nis(l['avg_payment'])}</td>
              <td class="small muted mono">{l['last_payment_date']}</td>
            </tr>''')
        loan_tx_rows = ''.join(
            f"<tr style='--row-i:{i}'><td class='small mono'>{t['bill_date']}</td><td>{pill(t['owner'], t['owner'])}</td>"
            f"<td class='small muted mono'>#{t.get('loan_id','?')}</td>"
            f"<td>{('received' if t.get('tag')=='loan_received' else 'repayment')}</td>"
            f"<td class='num mono'>{nis2(t['amount'])}</td></tr>"
            for i,t in enumerate(sorted(loans_raw, key=lambda x:x['bill_date'])))
        outstanding_total = sum(l['outstanding_estimate'] or 0 for l in loans_summary)
        loans_section_html = f'''<section class="section" id="loans">
          <div class="section-hd">
            <h2 class="section-title">{icon('loan','sec-icon')} Loans</h2>
            <div class="section-meta">{len(loans_summary)} loan(s) · {nis(loans_total_repaid)} repaid in period</div>
          </div>
          <p class="section-desc">Personal financial obligations per owner. Excluded from settlement.</p>
          <div class="grid g-3">
            {kpi_card('Repaid this period', loans_total_repaid, nis(loans_total_repaid/months_count)+'/mo avg', icon_name='loan')}
            {kpi_card('New loans drawn', loans_total_received if loans_total_received else 0, 'principal received')}
            {kpi_card('Outstanding (est.)', outstanding_total, 'from visible setups')}
          </div>
          <div class="card no-pad" style="margin-top:16px">
            <table>
              <thead><tr><th>Owner</th><th>Loan ID</th><th class="num">Received</th><th class="num">Repaid</th><th class="num">Outstanding</th><th class="num">Cadence</th><th>Last paid</th></tr></thead>
              <tbody>{"".join(loan_rows)}</tbody>
            </table>
          </div>
          <h4 class="sub-title" style="margin-top:24px">All loan transactions</h4>
          {table_card(['Date','Owner','Loan','Kind','₪'], loan_tx_rows)}
        </section>'''

    # House utilities table with icons
    util_labels = {
        'utility:electric': ('electric', 'Electric'),
        'utility:water':    ('water', 'Water'),
        'utility:gas':      ('fire', 'Gas'),
        'utility:arnona':   ('building', 'Arnona'),
        'utility:internet': ('wifi', 'Internet / TV'),
        'utility:building': ('building', "Va'ad bayit"),
        'utility:rent_mortgage': ('home', 'Rent / Mortgage'),
    }
    util_rows_html = []
    util_total_r = util_total_a = 0
    for tag,(ic,label) in util_labels.items():
        if tag not in utilities: continue
        r = utilities[tag].get('person_a', 0); a = utilities[tag].get('person_b', 0); t = r + a
        if t == 0: continue
        util_total_r += r; util_total_a += a
        if r > a: imb = pill(f'{LA} +{nis(r-a)}', 'person_a')
        elif a > r: imb = pill(f'{LB} +{nis(a-r)}', 'person_b')
        else: imb = pill('Equal', 'shared')
        util_rows_html.append(
            f'<tr><td><span class="util-row">{icon(ic,"util-ic")} {label}</span></td>'
            f'<td class="num mono">{nis(r)}</td>'
            f'<td class="num mono">{nis(a)}</td>'
            f'<td class="num mono"><strong>{nis(t)}</strong></td>'
            f'<td>{imb}</td></tr>')
    grocery_items = [t for t in shared_items if t.get('tag') in ('grocery','grocery_or_household')]
    grocery_r = sum(t['amount'] for t in grocery_items if t['owner']=='person_a')
    grocery_a = sum(t['amount'] for t in grocery_items if t['owner']=='person_b')
    grocery_total = grocery_r + grocery_a
    if grocery_total:
        if grocery_r > grocery_a: gp = pill(f'{LA} +{nis(grocery_r-grocery_a)}', 'person_a')
        elif grocery_a > grocery_r: gp = pill(f'{LB} +{nis(grocery_a-grocery_r)}', 'person_b')
        else: gp = pill('Equal', 'shared')
        util_rows_html.append(
            f'<tr><td><span class="util-row">{icon("cart","util-ic")} Food / groceries</span></td>'
            f'<td class="num mono">{nis(grocery_r)}</td>'
            f'<td class="num mono">{nis(grocery_a)}</td>'
            f'<td class="num mono"><strong>{nis(grocery_total)}</strong></td>'
            f'<td>{gp}</td></tr>')
    house_total = util_total_r + util_total_a + grocery_total
    house_total_r = util_total_r + grocery_r
    house_total_a = util_total_a + grocery_a
    util_rows_html.append(
        f'<tr class="total-row"><td><strong>Total household</strong></td>'
        f'<td class="num mono"><strong>{nis(house_total_r)}</strong></td>'
        f'<td class="num mono"><strong>{nis(house_total_a)}</strong></td>'
        f'<td class="num mono"><strong>{nis(house_total)}</strong></td>'
        f'<td class="small muted">{nis(house_total/months_count)}/mo</td></tr>')

    # Assumptions
    assumptions = [
        ('1', 'Apartment rent', 'shared',
         f'₪5,400/mo × 6 = ₪32,400, split 50/50',
         f'Each owes {nis(assumed_rent_each)}'),
        ('2', 'Phone bills', 'personal',
         'סלקום / פרטנר / פלאפון', 'Each pays own'),
        ('3', 'Insurance', 'personal',
         'All life/health/vehicle/home insurance', 'Each pays own'),
        ('4', 'Vehicles', 'personal',
         'Fuel, DMV, parking, mechanic, toll roads', f'{LA} {nis(car_totals["person_a"])} · {LB} {nis(car_totals["person_b"])}'),
        ('5', 'Gym + entertainment subs', 'personal',
         'Netflix, Apple, YouTube, gym', f'Subs {nis(subs_total)} · Gym {nis(gyms_total)}'),
        ('6', 'Restaurants', 'noted',
         'Pooled, not distributed', f'Total {nis(rest_total)}'),
        ('7', 'Vacations / travel', 'noted',
         'Pooled, not distributed', f'Total {nis(vac_total)}'),
        ('8', 'Business / SaaS', 'business',
         'Claude, AWS, GitHub, Cloudflare, etc.', f'Total {nis(business_total)}'),
        ('9', 'Furniture / home decor', 'shared',
         'IKEA, פנדה הום, TAKE IT, Temu, etc.', f'Total {nis(furniture_total)}'),
        ('10', 'Loans', 'personal',
         'Loans', f'Repaid {nis(loans_total_repaid)}'),
        ('11', 'Rental income', 'income',
         'Rental income', f'Total {nis(earnings_person_a_rental)}'),
        ('12', 'Date window', 'noted',
         'Bill date Oct 25 → Mar 26', '6 months'),
    ]
    assumption_cards = ''.join(
        f'''<div class="card assumption-card {kind}">
          <div class="assumption-num">{n}</div>
          <h4 class="assumption-title">{title}</h4>
          <p class="assumption-desc">{html.escape(desc)}</p>
          <div class="assumption-meta">{html.escape(meta)}</div>
        </div>''' for n,title,kind,desc,meta in assumptions
    )

    today_str = datetime.now().strftime('%b %d, %Y')

    return f'''<!doctype html>
<html lang="en" dir="ltr"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Expenses · {LA} + {LB}</title>
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1"></script>
<style>
:root {{
  /* Color tokens — OLED dark with semantic roles */
  --bg-base:        #07080d;
  --bg-elevated:    #0e1019;
  --bg-card:        #131623;
  --bg-card-hover:  #181b2b;
  --bg-glass:       rgba(255,255,255,0.025);
  --border:         rgba(255,255,255,0.06);
  --border-strong:  rgba(255,255,255,0.12);
  --ink:            #f3f4fa;
  --ink-2:          #b8bdd4;
  --ink-3:          #7c84a3;
  --ink-4:          #50556b;

  /* Brand */
  --person_a:           #5ea2ff;
  --person_a-glow:      rgba(94,162,255,0.22);
  --person_b:          #ff7ea8;
  --person_b-glow:     rgba(255,126,168,0.22);

  /* Semantic */
  --shared:         #8ee0bf;
  --shared-glow:    rgba(142,224,191,0.18);
  --personal:       #c3b6ff;
  --personal-glow:  rgba(195,182,255,0.18);
  --flag:           #ffd166;
  --flag-glow:      rgba(255,209,102,0.18);
  --income:         #7be0a5;
  --income-glow:    rgba(123,224,165,0.18);
  --danger:         #ff7e9c;
  --danger-glow:    rgba(255,126,156,0.18);

  /* Geometry */
  --r-sm: 8px;
  --r-md: 12px;
  --r-lg: 16px;
  --r-xl: 20px;

  /* Motion */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in:  cubic-bezier(0.7, 0, 0.84, 0);
  --dur-fast: 150ms;
  --dur-base: 240ms;
  --dur-slow: 380ms;

  /* Layout */
  --nav-w: 240px;
  --content-max: 1400px;
}}
@media (prefers-reduced-motion: reduce) {{
  *,*::before,*::after {{
    animation-duration: 0.001s !important;
    transition-duration: 0.001s !important;
  }}
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  background: var(--bg-base);
  color: var(--ink);
  font: 14px/1.55 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  font-feature-settings: "cv11", "ss01", "ss03";
  letter-spacing: -0.005em;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
  min-height: 100vh;
}}
/* Ambient background gradients */
body::before {{
  content: "";
  position: fixed; inset: 0;
  background:
    radial-gradient(900px 600px at 18% -5%, rgba(94,162,255,0.10) 0%, transparent 55%),
    radial-gradient(800px 500px at 100% 0%, rgba(255,126,168,0.08) 0%, transparent 55%),
    radial-gradient(700px 500px at 50% 100%, rgba(142,224,191,0.05) 0%, transparent 55%);
  pointer-events: none; z-index: 0;
}}

.app {{ display: flex; min-height: 100vh; position: relative; z-index: 1; }}

/* ─── SIDEBAR ─── */
aside.nav {{
  width: var(--nav-w);
  flex: 0 0 var(--nav-w);
  padding: 24px 16px;
  position: sticky; top: 0; height: 100vh; overflow-y: auto;
  border-right: 1px solid var(--border);
  background: rgba(7,8,13,0.65);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  z-index: 10;
}}
.brand {{
  display: flex; align-items: center; gap: 10px;
  padding: 4px 8px 20px;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--border);
}}
.brand-dot {{
  width: 32px; height: 32px; border-radius: 9px;
  background: linear-gradient(135deg, var(--person_a), var(--person_b));
  display: grid; place-items: center;
  box-shadow: 0 4px 14px rgba(94,162,255,0.3);
}}
.brand-dot::after {{
  content: "₪"; color: white; font-weight: 700; font-size: 16px;
}}
.brand-meta {{ display: flex; flex-direction: column; gap: 0; }}
.brand-name {{ font-weight: 700; font-size: 14px; letter-spacing: -0.02em; }}
.brand-period {{ font-size: 11px; color: var(--ink-3); font-weight: 500; }}

nav.nav-list {{ display: flex; flex-direction: column; gap: 1px; }}
nav.nav-list a {{
  display: flex; align-items: center; gap: 10px;
  padding: 9px 11px;
  border-radius: var(--r-sm);
  color: var(--ink-2);
  text-decoration: none;
  font-size: 13px; font-weight: 500;
  transition: all var(--dur-fast) var(--ease-out);
  position: relative;
}}
nav.nav-list a svg {{ width: 16px; height: 16px; flex: 0 0 16px; opacity: 0.85; }}
nav.nav-list a:hover {{
  background: var(--bg-card);
  color: var(--ink);
}}
nav.nav-list a.active {{
  background: var(--bg-card);
  color: var(--ink);
}}
nav.nav-list a.active::before {{
  content: "";
  position: absolute; left: -16px; top: 50%; transform: translateY(-50%);
  width: 3px; height: 18px; border-radius: 2px;
  background: linear-gradient(180deg, var(--person_a), var(--person_b));
}}

.nav-section {{
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.12em;
  color: var(--ink-4); font-weight: 600;
  padding: 16px 11px 6px;
}}

/* ─── MAIN ─── */
main.content {{
  flex: 1;
  min-width: 0;
  max-width: calc(100% - var(--nav-w));
  padding: 28px 40px 80px;
}}
@media (max-width: 1100px) {{
  main.content {{ padding: 24px 24px 60px; }}
}}
@media (max-width: 820px) {{
  aside.nav {{ display: none; }}
  main.content {{ max-width: 100%; padding: 16px 16px 60px; }}
  .mobile-nav {{ display: flex !important; }}
}}

/* Mobile top nav */
.mobile-nav {{
  display: none;
  position: sticky; top: 0; z-index: 30;
  background: rgba(7,8,13,0.9);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  padding: 12px 16px;
  margin: -16px -16px 20px;
  gap: 4px; overflow-x: auto;
}}
.mobile-nav::-webkit-scrollbar {{ display: none; }}

/* Add scroll-margin to all sections so they don't get hidden under sticky bars */
section.section, .hero {{ scroll-margin-top: 24px; }}
@media (max-width: 820px) {{ section.section, .hero {{ scroll-margin-top: 76px; }} }}
.mobile-nav a {{
  padding: 8px 12px; border-radius: 8px;
  color: var(--ink-2); text-decoration: none;
  font-size: 12px; font-weight: 600; white-space: nowrap;
  background: var(--bg-card);
  transition: all var(--dur-fast);
}}
.mobile-nav a.active {{ background: var(--ink); color: var(--bg-base); }}

/* ─── TOP CONTROLS BAR (sticky) ─── */
.controls {{
  position: sticky; top: 0; z-index: 25;
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 0;
  margin: -28px -40px 24px;
  padding-left: 40px; padding-right: 40px;
  background: rgba(7, 8, 13, 0.78);
  backdrop-filter: saturate(180%) blur(18px);
  -webkit-backdrop-filter: saturate(180%) blur(18px);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap; gap: 14px;
  transition: border-color var(--dur-base);
}}
.controls.scrolled {{ border-bottom-color: var(--border-strong); box-shadow: 0 4px 24px rgba(0,0,0,0.25); }}
@media (max-width: 1100px) {{ .controls {{ margin: -24px -24px 20px; padding: 12px 24px; }} }}
@media (max-width: 820px) {{ .controls {{ margin: 0 -16px 16px; padding: 10px 16px; top: 56px; }} }}

.controls-left {{ display: flex; align-items: center; gap: 14px; }}
.controls-left h1 {{
  font-size: 16px; font-weight: 700; margin: 0; letter-spacing: -0.01em;
}}
.controls-left .sub {{ color: var(--ink-3); font-size: 12px; margin-top: 1px; }}
.controls-left .filter-indicator {{
  font-size: 11px; padding: 4px 9px; border-radius: 999px;
  font-weight: 700; letter-spacing: 0.02em;
  background: var(--bg-card-hover); color: var(--ink-3);
  display: none; align-items: center; gap: 6px;
}}
.controls-left .filter-indicator.active.person_a {{ background: var(--person_a-glow); color: var(--person_a); display: inline-flex; }}
.controls-left .filter-indicator.active.person_b {{ background: var(--person_b-glow); color: var(--person_b); display: inline-flex; }}
.controls-left .filter-indicator::before {{ content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }}

.controls-right {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}

/* Global search input */
.global-search {{
  position: relative; width: 240px;
}}
@media (max-width: 700px) {{ .global-search {{ width: 160px; }} }}
.global-search input {{
  width: 100%; height: 34px;
  padding: 0 34px 0 32px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 9px;
  color: var(--ink);
  font: 12.5px 'Inter', sans-serif;
  outline: none;
  transition: all var(--dur-fast);
}}
.global-search input::placeholder {{ color: var(--ink-4); }}
.global-search input:focus {{ border-color: var(--person_a); background: var(--bg-base); box-shadow: 0 0 0 3px var(--person_a-glow); }}
.global-search-icon {{ position: absolute; left: 10px; top: 50%; transform: translateY(-50%); width: 14px; height: 14px; color: var(--ink-4); pointer-events: none; }}
.global-search-kbd {{
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  padding: 2px 6px; border-radius: 4px;
  background: var(--bg-card-hover); color: var(--ink-3);
  border: 1px solid var(--border);
  pointer-events: none;
}}

/* Filter chips group */
.filter-group {{
  display: inline-flex; padding: 3px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 9px;
  gap: 2px;
}}
.filter-chip {{
  padding: 6px 14px;
  border: 0; background: transparent;
  color: var(--ink-3);
  font-family: inherit; font-size: 12px; font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease-out);
  display: inline-flex; align-items: center; gap: 6px;
}}
.filter-chip:hover {{ color: var(--ink); background: var(--bg-card-hover); }}
.filter-chip.active {{
  background: var(--bg-elevated);
  color: var(--ink);
  box-shadow: 0 1px 0 var(--border-strong), inset 0 0 0 1px var(--border);
}}
.filter-chip.active::before {{
  content: ""; width: 6px; height: 6px; border-radius: 50%;
  background: var(--ink-3);
}}
.filter-chip.active.person_a {{ color: var(--person_a); }}
.filter-chip.active.person_a::before {{ background: var(--person_a); box-shadow: 0 0 8px var(--person_a); }}
.filter-chip.active.person_b {{ color: var(--person_b); }}
.filter-chip.active.person_b::before {{ background: var(--person_b); box-shadow: 0 0 8px var(--person_b); }}

/* Icon-only round buttons */
.icon-btn {{
  width: 34px; height: 34px;
  display: grid; place-items: center;
  border: 1px solid var(--border);
  background: var(--bg-card);
  border-radius: 9px;
  color: var(--ink-2);
  cursor: pointer;
  transition: all var(--dur-fast);
}}
.icon-btn:hover {{ color: var(--ink); border-color: var(--border-strong); background: var(--bg-card-hover); }}
.icon-btn svg {{ width: 16px; height: 16px; }}
.icon-btn.scroll-top {{ position: fixed; bottom: 24px; right: 24px; z-index: 50; opacity: 0; pointer-events: none; transform: translateY(8px); transition: all var(--dur-base) var(--ease-out); box-shadow: 0 4px 14px rgba(0,0,0,0.3); }}
.icon-btn.scroll-top.visible {{ opacity: 1; pointer-events: auto; transform: none; }}

/* Filtering banner — shows under controls when filtering */
.filter-banner {{
  display: none;
  align-items: center; gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 12.5px;
  margin-bottom: 18px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
}}
.filter-banner.active {{ display: flex; }}
.filter-banner.person_a {{ background: var(--person_a-glow); border-color: transparent; color: var(--person_a); }}
.filter-banner.person_b {{ background: var(--person_b-glow); border-color: transparent; color: var(--person_b); }}
.filter-banner button {{
  margin-left: auto;
  background: transparent; border: 0;
  color: inherit; opacity: 0.7;
  font: inherit; font-weight: 600;
  cursor: pointer;
  padding: 4px 8px; border-radius: 6px;
  transition: opacity var(--dur-fast), background var(--dur-fast);
}}
.filter-banner button:hover {{ opacity: 1; background: rgba(255,255,255,0.1); }}

/* Search results palette */
.search-overlay {{
  position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
  display: none;
  align-items: flex-start; justify-content: center;
  padding-top: 100px;
}}
.search-overlay.open {{ display: flex; animation: fadeIn 160ms var(--ease-out); }}
@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
.search-palette {{
  width: min(640px, calc(100% - 32px));
  background: var(--bg-elevated);
  border: 1px solid var(--border-strong);
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}}
.search-palette-input {{
  width: 100%; padding: 16px 20px;
  background: transparent; border: 0;
  color: var(--ink);
  font: 16px 'Inter', sans-serif;
  outline: none;
  border-bottom: 1px solid var(--border);
}}
.search-palette-results {{ max-height: 360px; overflow-y: auto; }}
.search-result {{
  padding: 11px 20px;
  display: flex; align-items: center; gap: 12px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background var(--dur-fast);
}}
.search-result:hover, .search-result.focused {{ background: var(--bg-card-hover); }}
.search-result-icon {{ width: 16px; height: 16px; color: var(--ink-3); flex-shrink: 0; }}
.search-result-text {{ flex: 1; min-width: 0; }}
.search-result-name {{ font-size: 13.5px; color: var(--ink); font-weight: 500; }}
.search-result-meta {{ font-size: 11.5px; color: var(--ink-3); margin-top: 2px; }}
.search-palette-empty {{ padding: 32px 20px; text-align: center; color: var(--ink-3); font-size: 13px; }}
.search-palette-hint {{
  padding: 8px 20px; display: flex; gap: 16px; align-items: center;
  background: var(--bg-card); border-top: 1px solid var(--border);
  font-size: 11px; color: var(--ink-3);
}}
.search-palette-hint kbd {{
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  padding: 2px 6px; background: var(--bg-card-hover); border: 1px solid var(--border-strong);
  border-radius: 4px; color: var(--ink-2);
}}

/* ─── HERO ─── */
.hero {{
  border-radius: var(--r-xl);
  padding: 32px;
  margin-bottom: 28px;
  background:
    linear-gradient(135deg, rgba(94,162,255,0.10) 0%, transparent 50%, rgba(255,126,168,0.10) 100%),
    var(--bg-elevated);
  border: 1px solid var(--border);
  position: relative; overflow: hidden;
}}
.hero::before {{
  content: ""; position: absolute; inset: 0;
  background: radial-gradient(circle at 50% 0%, rgba(255,255,255,0.04) 0%, transparent 60%);
  pointer-events: none;
}}
.hero-grid {{
  display: grid; grid-template-columns: 1.4fr 1fr;
  gap: 28px; position: relative; z-index: 1;
}}
@media (max-width: 880px) {{ .hero-grid {{ grid-template-columns: 1fr; gap: 20px; }} }}
.hero-label {{
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.15em;
  color: var(--ink-3); font-weight: 600;
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 14px;
}}
.hero-label::before {{
  content: ""; width: 6px; height: 6px; border-radius: 50%;
  background: var(--shared); box-shadow: 0 0 12px var(--shared);
}}
.hero-amount {{
  font-size: clamp(40px, 6vw, 64px);
  font-weight: 800; line-height: 0.95; letter-spacing: -0.04em;
  background: linear-gradient(180deg, var(--ink) 0%, var(--ink-2) 100%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
  font-variant-numeric: tabular-nums;
}}
.hero-amount-suffix {{
  font-size: 0.4em; color: var(--ink-3); font-weight: 500;
  margin-left: 6px; letter-spacing: 0;
  -webkit-text-fill-color: var(--ink-3);
}}
.hero-desc {{
  margin-top: 14px; color: var(--ink-2); font-size: 14px; line-height: 1.6;
  max-width: 56ch;
}}
.hero-stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
.hero-stat {{
  padding: 14px 16px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  transition: border-color var(--dur-fast);
}}
.hero-stat:hover {{ border-color: var(--border-strong); }}
.hero-stat-l {{ color: var(--ink-3); font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; }}
.hero-stat-v {{ font-size: 20px; font-weight: 700; margin-top: 4px; letter-spacing: -0.02em; font-variant-numeric: tabular-nums; }}
.hero-stat-sub {{ font-size: 11px; color: var(--ink-3); margin-top: 2px; }}

/* ─── SECTIONS ─── */
section.section {{ margin: 48px 0 0; scroll-margin-top: 20px; }}
section.section:first-of-type {{ margin-top: 0; }}
.section-hd {{
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 6px; gap: 16px;
}}
.section-title {{
  font-size: 18px; font-weight: 700; margin: 0; letter-spacing: -0.015em;
  display: flex; align-items: center; gap: 10px;
}}
.section-title .sec-icon {{ width: 18px; height: 18px; opacity: 0.7; }}
.section-meta {{ color: var(--ink-3); font-size: 12px; font-weight: 500; font-variant-numeric: tabular-nums; }}
.section-desc {{ color: var(--ink-3); font-size: 13px; margin: 0 0 16px; max-width: 70ch; line-height: 1.55; }}
.sub-title {{ font-size: 13px; font-weight: 600; color: var(--ink-2); margin: 16px 0 8px; }}

/* ─── CARDS ─── */
.card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 20px;
  transition: border-color var(--dur-base) var(--ease-out), background var(--dur-base);
}}
.card:hover {{ border-color: var(--border-strong); }}
.card.no-pad {{ padding: 0; overflow: hidden; }}
.glow-person_a {{ background: linear-gradient(165deg, var(--person_a-glow) 0%, var(--bg-card) 60%); }}
.glow-person_b {{ background: linear-gradient(165deg, var(--person_b-glow) 0%, var(--bg-card) 60%); }}

.card-hd {{
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px; gap: 12px; flex-wrap: wrap;
}}
.card-title {{
  font-size: 14px; font-weight: 600; margin: 0;
  display: flex; align-items: center; gap: 8px; letter-spacing: -0.005em;
}}
.dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; }}
.dot.person_a {{ background: var(--person_a); box-shadow: 0 0 10px var(--person_a-glow); }}
.dot.person_b {{ background: var(--person_b); box-shadow: 0 0 10px var(--person_b-glow); }}

/* Grid */
.grid {{ display: grid; gap: 14px; }}
.g-2 {{ grid-template-columns: 1fr 1fr; }}
.g-3 {{ grid-template-columns: repeat(3, 1fr); }}
.g-4 {{ grid-template-columns: repeat(4, 1fr); }}
@media (max-width: 1000px) {{ .g-4, .g-3 {{ grid-template-columns: repeat(2, 1fr); }} }}
@media (max-width: 560px) {{ .g-4, .g-3, .g-2 {{ grid-template-columns: 1fr; }} }}

/* KPI */
.kpi-card {{ position: relative; overflow: hidden; }}
.kpi-icon {{
  position: absolute; top: 16px; right: 16px;
  width: 20px; height: 20px; color: var(--ink-3); opacity: 0.7;
}}
.kpi-icon svg {{ width: 100%; height: 100%; }}
.kpi-label {{
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--ink-3); font-weight: 600;
}}
.kpi-value {{
  font-size: 26px; font-weight: 700; margin-top: 8px;
  letter-spacing: -0.025em; font-variant-numeric: tabular-nums;
  line-height: 1.1;
}}
.kpi-delta {{ color: var(--ink-3); font-size: 12px; margin-top: 6px; line-height: 1.5; }}
canvas.sparkline {{
  margin-top: 12px;
  width: 100% !important; height: 32px !important;
  opacity: 0.85;
}}

/* Pills */
.pill {{
  display: inline-block; padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px; font-weight: 600; letter-spacing: 0.01em;
  white-space: nowrap;
}}
.pill-person_a {{ background: var(--person_a-glow); color: var(--person_a); }}
.pill-person_b {{ background: var(--person_b-glow); color: var(--person_b); }}
.pill-shared {{ background: var(--shared-glow); color: var(--shared); }}
.pill-personal {{ background: var(--personal-glow); color: var(--personal); }}
.pill-flag {{ background: var(--flag-glow); color: var(--flag); }}
.pill-income {{ background: var(--income-glow); color: var(--income); }}
.pill-business {{ background: var(--personal-glow); color: var(--personal); }}
.pill-noted {{ background: var(--bg-card-hover); color: var(--ink-3); }}

/* ─── Table card with filter bar ─── */
.table-card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  overflow: hidden;
  transition: border-color var(--dur-base);
}}
.table-card:hover {{ border-color: var(--border-strong); }}

.table-filter {{
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}}
.filter-input-wrap {{
  position: relative;
  flex: 1; min-width: 200px;
}}
.filter-icon {{
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  width: 14px; height: 14px; color: var(--ink-4);
  pointer-events: none;
}}
.filter-input {{
  width: 100%;
  height: 36px;
  padding: 0 36px 0 36px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 9px;
  color: var(--ink);
  font: 13px 'Inter', sans-serif;
  transition: border-color var(--dur-fast), background var(--dur-fast);
  outline: none;
}}
.filter-input::placeholder {{ color: var(--ink-4); }}
.filter-input:hover {{ border-color: var(--border-strong); }}
.filter-input:focus {{
  border-color: var(--person_a);
  background: var(--bg-base);
  box-shadow: 0 0 0 3px var(--person_a-glow);
}}
.filter-clear {{
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  width: 22px; height: 22px; border-radius: 6px;
  border: 0; background: transparent;
  color: var(--ink-3);
  font-size: 18px; line-height: 1;
  cursor: pointer; display: none;
  transition: all var(--dur-fast);
}}
.filter-clear:hover {{ background: var(--bg-card-hover); color: var(--ink); }}
.filter-input-wrap.has-value .filter-clear {{ display: grid; place-items: center; }}

.filter-stats {{ display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }}
.stat-chip {{
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 7px;
  font-size: 12px;
  white-space: nowrap;
}}
.stat-chip.primary {{
  background: var(--shared-glow);
  border-color: transparent;
  color: var(--shared);
}}
.stat-label {{ color: var(--ink-3); font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }}
.stat-chip.primary .stat-label {{ color: var(--shared); opacity: 0.7; }}
.stat-val {{ font-weight: 700; color: var(--ink); font-variant-numeric: tabular-nums; }}
.stat-chip.primary .stat-val {{ color: var(--shared); }}

/* Tables */
.table-card table {{ width: 100%; border-collapse: collapse; font-size: 13px; font-variant-numeric: tabular-nums; }}
.table-card th, .table-card td {{
  padding: 12px 16px; text-align: left; vertical-align: middle;
  border-bottom: 1px solid var(--border);
}}
.table-card thead th {{
  font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--ink-3); font-weight: 600;
  background: var(--bg-card);
  position: sticky; top: 0; z-index: 2;
  user-select: none;
  border-bottom: 1px solid var(--border-strong);
}}
.table-card tbody tr:last-child td {{ border-bottom: 0; }}
.table-card table[data-sortable] th {{ cursor: pointer; transition: color var(--dur-fast); position: relative; padding-right: 24px; }}
.table-card table[data-sortable] th:hover {{ color: var(--ink); background: var(--bg-card-hover); }}
.table-card table[data-sortable] th::after {{
  content: ""; position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  width: 8px; height: 8px;
  background-image: linear-gradient(180deg, transparent 0%, transparent 40%, var(--ink-4) 40%, var(--ink-4) 60%, transparent 60%);
  opacity: 0; transition: opacity var(--dur-fast);
}}
.table-card table[data-sortable] th.sort-asc::after, .table-card table[data-sortable] th.sort-desc::after {{
  content: ""; opacity: 1;
  width: 0; height: 0; background: none;
  border-left: 4px solid transparent; border-right: 4px solid transparent;
}}
.table-card table[data-sortable] th.sort-asc::after {{ border-bottom: 5px solid var(--person_a); }}
.table-card table[data-sortable] th.sort-desc::after {{ border-top: 5px solid var(--person_a); }}

.table-card tbody tr {{
  transition: background var(--dur-fast);
  animation: rowIn 280ms var(--ease-out) backwards;
  animation-delay: calc(min(var(--row-i, 0), 30) * 10ms);
}}
@keyframes rowIn {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: none; }} }}
.table-card tbody tr:nth-child(odd) {{ background: rgba(255,255,255,0.012); }}
.table-card tbody tr:hover {{ background: var(--bg-card-hover) !important; }}
.table-card tbody tr.hidden {{ display: none; }}
.table-card tr.total-row td {{ border-top: 1.5px solid var(--border-strong); background: rgba(255,255,255,0.025); font-weight: 600; }}
.table-card td.num, .table-card th.num {{ text-align: right; }}
.mono {{ font-family: 'JetBrains Mono', ui-monospace, SF Mono, Menlo, monospace; font-size: 12.5px; font-weight: 500; font-variant-numeric: tabular-nums; }}
.he {{ direction: rtl; text-align: right; font-family: 'SF Hebrew', 'Arial Hebrew', 'Segoe UI', sans-serif; unicode-bidi: plaintext; }}
.muted {{ color: var(--ink-3); }}
.small {{ font-size: 12px; }}

/* Generic tables (non-card wrapped) */
table {{ width: 100%; border-collapse: collapse; font-size: 13px; font-variant-numeric: tabular-nums; }}
.card > table th, .card > table td, .card.no-pad table th, .card.no-pad table td {{
  padding: 12px 16px; text-align: left; vertical-align: middle;
  border-bottom: 1px solid var(--border);
}}
.card > table thead th, .card.no-pad table thead th {{
  font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--ink-3); font-weight: 600;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-strong);
}}
.card.no-pad table tbody tr:hover {{ background: var(--bg-card-hover); }}
.card.no-pad table tr.total-row td {{ border-top: 1.5px solid var(--border-strong); background: rgba(255,255,255,0.025); font-weight: 600; }}
.card.no-pad table td.num, .card.no-pad table th.num {{ text-align: right; }}

/* Scrollbar */
.scroll {{ overflow: auto; }}
.scroll::-webkit-scrollbar {{ width: 8px; height: 8px; }}
.scroll::-webkit-scrollbar-track {{ background: transparent; }}
.scroll::-webkit-scrollbar-thumb {{ background: var(--border-strong); border-radius: 4px; }}
.scroll::-webkit-scrollbar-thumb:hover {{ background: var(--ink-4); }}

table.mini th, table.mini td {{ padding: 9px 0; border: 0; font-size: 13px; }}
table.mini td:last-child {{ text-align: right; font-family: 'JetBrains Mono', monospace; font-weight: 500; }}

details {{ margin-top: 14px; }}
details summary {{ cursor: pointer; padding: 4px 0; outline: none; font-size: 12px; }}
details summary:hover {{ color: var(--ink); }}

/* Settlement */
.settle-arrow {{
  display: grid; grid-template-columns: 1fr auto 1fr;
  align-items: center; gap: 24px;
  padding: 28px 0 12px;
}}
.settle-from, .settle-to {{
  display: flex; flex-direction: column; gap: 6px;
}}
.settle-from {{ text-align: right; }}
.settle-name {{ font-size: 22px; font-weight: 700; letter-spacing: -0.02em; }}
.settle-from.person_a .settle-name, .settle-to.person_a .settle-name {{ color: var(--person_a); }}
.settle-from.person_b .settle-name, .settle-to.person_b .settle-name {{ color: var(--person_b); }}
.settle-role {{ font-size: 12px; color: var(--ink-3); text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; }}
.settle-mid {{
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}}
.settle-mid svg {{ width: 36px; height: 36px; color: var(--shared); }}
.settle-mid-amt {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 28px; font-weight: 700; color: var(--shared);
  font-variant-numeric: tabular-nums; letter-spacing: -0.02em;
}}
.settle-even {{ text-align: center; padding: 24px 0; }}

.settle-pieces {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 18px; }}
@media (max-width: 700px) {{ .settle-pieces {{ grid-template-columns: 1fr; }} }}
.settle-piece {{
  padding: 14px 16px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
}}
.piece-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--ink-3); font-weight: 600; }}
.piece-amt {{ font-size: 14px; margin-top: 6px; font-weight: 500; }}
.piece-amt.danger {{ color: var(--danger); }}
.piece-amt.income {{ color: var(--income); }}

/* Charts */
.chart-box {{ position: relative; height: 320px; }}
.chart-box.short {{ height: 280px; }}

/* Utility row */
.util-row {{ display: inline-flex; align-items: center; gap: 10px; }}
.util-ic {{ width: 16px; height: 16px; color: var(--ink-3); }}

/* Assumption cards */
.assumption-card {{
  position: relative; padding: 18px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  transition: transform var(--dur-base) var(--ease-out), border-color var(--dur-base);
}}
.assumption-card:hover {{ border-color: var(--border-strong); transform: translateY(-2px); }}
.assumption-num {{
  position: absolute; top: 14px; right: 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; color: var(--ink-4); font-weight: 600;
}}
.assumption-title {{ font-size: 14px; font-weight: 600; margin: 0 0 6px; padding-right: 24px; }}
.assumption-desc {{ font-size: 12.5px; color: var(--ink-2); margin: 0 0 10px; line-height: 1.55; }}
.assumption-meta {{ font-size: 11.5px; color: var(--ink-3); font-family: 'JetBrains Mono', monospace; }}
.assumption-card::before {{
  content: ""; position: absolute; top: 0; left: 0; bottom: 0;
  width: 2px; border-radius: 2px 0 0 2px;
}}
.assumption-card.shared::before {{ background: var(--shared); }}
.assumption-card.personal::before {{ background: var(--personal); }}
.assumption-card.business::before {{ background: var(--personal); }}
.assumption-card.income::before {{ background: var(--income); }}
.assumption-card.noted::before {{ background: var(--ink-4); }}

/* Person split (person A vs person B side-by-side) */
.person-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
@media (max-width: 800px) {{ .person-grid {{ grid-template-columns: 1fr; }} }}
.person-card {{ position: relative; padding: 22px; overflow: hidden; border-radius: var(--r-lg); border: 1px solid var(--border); background: var(--bg-card); }}
.person-card.person_a {{ background: radial-gradient(circle at 100% 0%, var(--person_a-glow), transparent 60%), var(--bg-card); }}
.person-card.person_b {{ background: radial-gradient(circle at 100% 0%, var(--person_b-glow), transparent 60%), var(--bg-card); }}
.person-name {{ font-size: 14px; font-weight: 700; display: flex; align-items: center; gap: 8px; }}
.person-total {{ font-size: 32px; font-weight: 700; margin: 6px 0 16px; letter-spacing: -0.025em; font-variant-numeric: tabular-nums; }}
.person-card.person_a .person-total {{ color: var(--person_a); }}
.person-card.person_b .person-total {{ color: var(--person_b); }}

/* Tooltips for charts */
.chartjs-tooltip {{
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-strong) !important;
}}

/* ─── Future Estimation ─── */
.future-controls {{ position: sticky; top: 16px; align-self: start; }}
@media (max-width: 1100px) {{
  #future .grid.g-2 {{ grid-template-columns: 1fr !important; }}
  .future-controls {{ position: static; }}
}}
.ctrl-group {{ margin-bottom: 18px; }}
.ctrl-head {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }}
.ctrl-label {{ font-size: 12px; font-weight: 600; color: var(--ink-2); }}
.ctrl-value {{ font-size: 13px; font-weight: 700; color: var(--ink); font-variant-numeric: tabular-nums; }}
.ctrl-meta {{ display: flex; justify-content: space-between; font-size: 11px; color: var(--ink-3); margin-top: 6px; }}
.ctrl-meta span {{ display: flex; align-items: center; gap: 4px; }}
.ctrl-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}

.future-slider {{
  -webkit-appearance: none; appearance: none;
  width: 100%; height: 4px;
  background: var(--bg-card-hover);
  border-radius: 2px;
  outline: none;
}}
.future-slider::-webkit-slider-thumb {{
  -webkit-appearance: none; appearance: none;
  width: 16px; height: 16px; border-radius: 50%;
  background: var(--person_a);
  cursor: pointer;
  box-shadow: 0 0 0 4px rgba(94,162,255,0.2);
  transition: box-shadow var(--dur-fast), transform var(--dur-fast);
}}
.future-slider::-webkit-slider-thumb:hover {{ box-shadow: 0 0 0 6px rgba(94,162,255,0.3); transform: scale(1.1); }}
.future-slider::-webkit-slider-thumb:active {{ box-shadow: 0 0 0 8px rgba(94,162,255,0.4); }}
.future-slider::-moz-range-thumb {{
  width: 16px; height: 16px; border-radius: 50%; border: 0;
  background: var(--person_a); cursor: pointer;
  box-shadow: 0 0 0 4px rgba(94,162,255,0.2);
}}

.future-date, .future-num {{
  background: var(--bg-card); border: 1px solid var(--border);
  color: var(--ink); padding: 4px 8px; border-radius: 6px;
  font: inherit; font-size: 11.5px;
  color-scheme: dark;
}}
.future-date.wide {{ width: 100%; padding: 6px 10px; font-size: 13px; }}
.future-num {{ width: 50px; text-align: center; }}
.future-date:focus, .future-num:focus {{ outline: none; border-color: var(--person_a); box-shadow: 0 0 0 3px var(--person_a-glow); }}

.reset-btn {{
  width: 100%; margin-top: 6px;
  padding: 10px;
  background: transparent; border: 1px solid var(--border-strong);
  color: var(--ink-2); font: 600 12px/1 inherit;
  border-radius: 8px; cursor: pointer;
  transition: all var(--dur-fast);
}}
.ctrl-divider {{
  display: flex; align-items: center; gap: 10px;
  margin: 20px 0 14px;
  color: var(--ink-3); font-size: 10.5px;
  text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600;
}}
.ctrl-divider::before, .ctrl-divider::after {{
  content: ""; flex: 1; height: 1px; background: var(--border);
}}
.set-required-btn {{
  width: 100%; margin-top: 8px;
  padding: 7px 10px;
  background: var(--flag-glow);
  border: 1px solid transparent;
  color: var(--flag);
  font: 600 11.5px/1 inherit;
  border-radius: 7px;
  cursor: pointer;
  transition: all var(--dur-fast);
}}
.set-required-btn:hover {{ background: rgba(255,209,102,0.25); }}
.required-card {{
  background: linear-gradient(165deg, rgba(255,209,102,0.10) 0%, var(--bg-card) 60%);
  border-color: rgba(255,209,102,0.25);
}}
.required-detail .required-grid {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
}}
@media (max-width: 1000px) {{ .required-detail .required-grid {{ grid-template-columns: 1fr 1fr; }} }}
.required-item {{
  padding: 14px 16px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
}}
.req-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--ink-3); font-weight: 600; margin-bottom: 8px; line-height: 1.4; }}
.req-val {{ font-size: 22px; font-weight: 700; letter-spacing: -0.02em; color: var(--ink); font-variant-numeric: tabular-nums; }}
.req-meta {{ font-size: 11px; color: var(--ink-3); margin-top: 4px; }}
.reset-btn:hover {{ background: var(--bg-card-hover); color: var(--ink); border-color: var(--person_a); }}

.legend-inline {{ display: flex; gap: 16px; font-size: 11.5px; color: var(--ink-3); flex-wrap: wrap; }}
.legend-inline span {{ display: inline-flex; align-items: center; gap: 6px; }}
.leg-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}

.insights-list {{ display: flex; flex-direction: column; gap: 10px; }}
.insight {{
  display: flex; align-items: flex-start; gap: 12px;
  padding: 12px 14px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 13px; line-height: 1.5;
}}
.insight.warn {{ border-left: 3px solid var(--flag); background: rgba(255,209,102,0.04); }}
.insight.danger {{ border-left: 3px solid var(--danger); background: rgba(255,126,156,0.04); }}
.insight.good {{ border-left: 3px solid var(--income); background: rgba(123,224,165,0.04); }}
.insight-ic {{ flex: 0 0 18px; margin-top: 2px; opacity: 0.9; }}
.insight-ic svg {{ width: 18px; height: 18px; }}
.insight.warn .insight-ic {{ color: var(--flag); }}
.insight.danger .insight-ic {{ color: var(--danger); }}
.insight.good .insight-ic {{ color: var(--income); }}
.insight strong {{ color: var(--ink); }}

#future-tbody tr.month-deficit td {{ color: var(--danger); }}
#future-tbody tr.month-deficit td:first-child::before {{ content:"⚠ "; }}
#future-tbody tr.month-event td {{ background: rgba(255,209,102,0.04); }}
.month-tag {{
  display: inline-block; padding: 1px 7px; border-radius: 4px;
  font-size: 10.5px; font-weight: 600; background: var(--bg-card-hover); color: var(--ink-3);
  margin-right: 4px;
}}
.month-tag.rent {{ color: var(--person_a); background: var(--person_a-glow); }}
.month-tag.baby {{ color: var(--person_b); background: var(--person_b-glow); }}
.month-tag.maternity {{ color: var(--flag); background: var(--flag-glow); }}
.month-tag.daycare {{ color: var(--personal); background: var(--personal-glow); }}

/* Print friendly */
@media print {{
  body::before {{ display: none; }}
  aside.nav, .mobile-nav, .controls {{ display: none !important; }}
  main.content {{ max-width: 100%; padding: 0; }}
}}
</style>
</head>
<body>

<div class="app">

  <!-- ─── SIDEBAR ─── -->
  <aside class="nav">
    <div class="brand">
      <div class="brand-dot" aria-hidden="true"></div>
      <div class="brand-meta">
        <div class="brand-name">Expenses</div>
        <div class="brand-period">Oct 25 – Mar 26</div>
      </div>
    </div>
    <nav class="nav-list" aria-label="Main navigation">
      <div class="nav-section">Summary</div>
      <a href="#overview">{icon('overview')} Overview</a>
      <a href="#settle">{icon('split')} Settlement</a>
      <a href="#earnings">{icon('income')} Earnings</a>
      <a href="#trends">{icon('overview')} Trends</a>

      <div class="nav-section">Household</div>
      <a href="#utilities">{icon('home')} Utilities</a>
      <a href="#rent">{icon('home')} Rent</a>
      <a href="#furniture">{icon('sofa')} Furniture</a>

      <div class="nav-section">Personal</div>
      <a href="#cars">{icon('car')} Cars</a>
      <a href="#business">{icon('business')} Business</a>
      <a href="#loans">{icon('loan')} Loans</a>

      <div class="nav-section">Lifestyle</div>
      <a href="#restaurants">{icon('utensils')} Restaurants</a>
      <a href="#vacations">{icon('plane')} Vacations</a>

      <div class="nav-section">Planning</div>
      <a href="#future">{icon('overview')} Future</a>

      <div class="nav-section">Detail</div>
      <a href="#shared">{icon('check')} Shared items</a>
      <a href="#flagged">{icon('flag')} Flagged</a>
      <a href="#transfers">{icon('transfer')} Transfers</a>
      <a href="#assumptions">{icon('info')} Assumptions</a>
    </nav>
  </aside>

  <!-- ─── MAIN ─── -->
  <main class="content">

    <!-- Mobile nav (visible only < 820px) -->
    <div class="mobile-nav">
      <a href="#overview">Overview</a><a href="#settle">Settlement</a><a href="#earnings">Earnings</a>
      <a href="#utilities">Utilities</a><a href="#rent">Rent</a><a href="#cars">Cars</a>
      <a href="#business">Business</a><a href="#loans">Loans</a>
      <a href="#restaurants">Restaurants</a><a href="#vacations">Vacations</a>
      <a href="#flagged">Flagged</a><a href="#future">Future</a><a href="#assumptions">Assumptions</a>
    </div>

    <!-- Top controls (sticky) -->
    <div class="controls" id="top-controls">
      <div class="controls-left">
        <div>
          <h1>{LA} + {LB}</h1>
          <div class="sub">Oct 25 → Mar 26 · {today_str}</div>
        </div>
        <span class="filter-indicator" id="filter-indicator">filtering by {LA}</span>
      </div>
      <div class="controls-right">
        <div class="global-search">
          <svg class="global-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="search" id="global-search-input" placeholder="Search all transactions..." aria-label="Global search">
          <kbd class="global-search-kbd">⌘K</kbd>
        </div>
        <div class="filter-group" role="group" aria-label="Filter by owner">
          <button class="filter-chip active" data-owner="both" title="Show both">Both</button>
          <button class="filter-chip" data-owner="person_a" title="{LA} only">{LA}</button>
          <button class="filter-chip" data-owner="person_b" title="{LB} only">{LB}</button>
        </div>
        <button class="icon-btn" id="btn-print" title="Print / export PDF" aria-label="Print">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
        </button>
        <button class="icon-btn" id="btn-collapse-all" title="Collapse all detail tables" aria-label="Collapse">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
        </button>
      </div>
    </div>

    <!-- Filter banner (appears when filtering) -->
    <div class="filter-banner" id="filter-banner">
      <span id="filter-banner-text">Showing {LA} only</span>
      <button id="filter-banner-clear">Clear filter ×</button>
    </div>

    <!-- Floating scroll-to-top button -->
    <button class="icon-btn scroll-top" id="btn-scroll-top" title="Back to top" aria-label="Scroll to top">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>
    </button>

    <!-- Global search palette (⌘K) -->
    <div class="search-overlay" id="search-overlay">
      <div class="search-palette" role="dialog" aria-label="Global search">
        <input type="search" class="search-palette-input" id="search-palette-input" placeholder="Search by merchant, category, amount...">
        <div class="search-palette-results" id="search-palette-results"></div>
        <div class="search-palette-hint">
          <span><kbd>↑↓</kbd> navigate</span>
          <span><kbd>Enter</kbd> jump to section</span>
          <span><kbd>Esc</kbd> close</span>
        </div>
      </div>
    </div>

    <!-- HERO -->
    <section id="overview" class="hero">
      <div class="hero-grid">
        <div>
          <div class="hero-label">Monthly burn rate</div>
          <div class="hero-amount"><span class="counter" data-target="{monthly_burn:.0f}" data-prefix="₪">₪0</span><span class="hero-amount-suffix">/mo</span></div>
          <p class="hero-desc">
            Combined household spend (cards + rent) over 6 months: <strong>{nis(total_burn)}</strong>.
            Income: <strong style="color:var(--income)">{nis(total_income/months_count)}/mo</strong> — {LA} {nis(earnings_person_a_total/months_count)}, {LB} {nis(earnings_person_b_total/months_count)}.
            <strong style="color:{('var(--income)' if total_income-total_burn>=0 else 'var(--danger)')}">Net {nis((total_income-total_burn)/months_count)}/mo</strong>.
          </p>
        </div>
        <div class="hero-stats">
          <div class="hero-stat"><div class="hero-stat-l">{LA} spend / mo</div><div class="hero-stat-v" style="color:var(--person_a)">{nis((totals['person_a']+assumed_rent_each)/months_count)}</div><div class="hero-stat-sub">incl. rent share</div></div>
          <div class="hero-stat"><div class="hero-stat-l">{LB} spend / mo</div><div class="hero-stat-v" style="color:var(--person_b)">{nis((totals['person_b']+assumed_rent_each)/months_count)}</div><div class="hero-stat-sub">incl. rent share</div></div>
          <div class="hero-stat"><div class="hero-stat-l">Shared bucket / mo</div><div class="hero-stat-v" style="color:var(--shared)">{nis(avg_shared)}</div><div class="hero-stat-sub">{nis(avg_shared/2)} each</div></div>
          <div class="hero-stat"><div class="hero-stat-l">Income / mo</div><div class="hero-stat-v" style="color:var(--income)">{nis(total_income/months_count)}</div><div class="hero-stat-sub">salary + rental</div></div>
        </div>
      </div>
    </section>

    <!-- KPI ROW with sparklines -->
    <section class="section">
      <div class="section-hd"><h2 class="section-title">{icon('overview','sec-icon')} At a glance</h2></div>
      <div class="grid g-4">
        {kpi_card('Total spend', total_burn, nis(total_burn/months_count)+'/mo combined', sparkline_data=[shared_pm[i]+personal_pm[i]+rest_pm[i]+vac_pm[i]+flag_pm[i] for i in range(len(months))], icon_name='overview')}
        {kpi_card('Household income', total_income, nis(total_income/months_count)+'/mo', color='var(--income)', sparkline_data=earnings_pm, icon_name='income')}
        {kpi_card('Shared (cards)', shared_cards_total, 'cards-only bucket', color='var(--shared)', sparkline_data=shared_pm, icon_name='home')}
        {kpi_card('Flagged', flag_total, str(len(flagged))+' items', color='var(--flag)', sparkline_data=flag_pm, icon_name='flag')}
      </div>
    </section>

    <!-- SETTLEMENT -->
    <section id="settle" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('split','sec-icon')} Settlement</h2>
      </div>
      <p class="section-desc">After splitting all shared expenses 50/50 and netting rent transfers.</p>
      <div class="card">
        {settlement_arrow_html}
        <div class="settle-pieces">{''.join(settle_pieces)}</div>
      </div>
    </section>

    <!-- PER-PERSON SUMMARY -->
    <section class="section" id="people">
      <div class="section-hd"><h2 class="section-title">{icon('overview','sec-icon')} By person</h2></div>
      <div class="person-grid">
        <div class="person-card person_a">
          <div class="person-name"><span class="dot person_a"></span>{LA}</div>
          <div class="person-total counter" data-target="{totals['person_a']+assumed_rent_each:.0f}" data-prefix="₪">₪0</div>
          <table class="mini">
            <tr><td>Cards spend</td><td>{nis(totals['person_a'])}</td></tr>
            <tr><td>Restaurants</td><td>{nis(rest_by_owner['person_a'])}</td></tr>
            <tr><td>Vacations</td><td>{nis(vac_by_owner['person_a'])}</td></tr>
            <tr><td>Car (personal)</td><td>{nis(car_totals['person_a'])}</td></tr>
            <tr><td>Business / SaaS</td><td>{nis(business_by_owner['person_a'])}</td></tr>
            <tr><td>Shared paid</td><td style="color:var(--shared)">{nis(shared_cards_person_a)}</td></tr>
            <tr><td>+ Rent share</td><td>{nis(assumed_rent_each)}</td></tr>
            <tr style="border-top:1px solid var(--border-strong)"><td><strong>Earnings</strong></td><td style="color:var(--income)"><strong>{nis(earnings_person_a_total)}</strong></td></tr>
            <tr><td><strong>Net</strong></td><td style="color:{('var(--income)' if earnings_person_a_total-(totals['person_a']+assumed_rent_each)>=0 else 'var(--danger)')}"><strong>{nis(earnings_person_a_total-(totals['person_a']+assumed_rent_each))}</strong></td></tr>
          </table>
        </div>
        <div class="person-card person_b">
          <div class="person-name"><span class="dot person_b"></span>{LB}</div>
          <div class="person-total counter" data-target="{totals['person_b']+assumed_rent_each:.0f}" data-prefix="₪">₪0</div>
          <table class="mini">
            <tr><td>Cards spend</td><td>{nis(totals['person_b'])}</td></tr>
            <tr><td>Restaurants</td><td>{nis(rest_by_owner['person_b'])}</td></tr>
            <tr><td>Vacations</td><td>{nis(vac_by_owner['person_b'])}</td></tr>
            <tr><td>Car (personal)</td><td>{nis(car_totals['person_b'])}</td></tr>
            <tr><td>Loans repaid</td><td>{nis(loans_total_repaid)}</td></tr>
            <tr><td>Shared paid</td><td style="color:var(--shared)">{nis(shared_cards_person_b)}</td></tr>
            <tr><td>+ Rent share</td><td>{nis(assumed_rent_each)}</td></tr>
            <tr style="border-top:1px solid var(--border-strong)"><td><strong>Earnings</strong></td><td style="color:var(--income)"><strong>{nis(earnings_person_b_total)}</strong></td></tr>
            <tr><td><strong>Net</strong></td><td style="color:{('var(--income)' if earnings_person_b_total-(totals['person_b']+assumed_rent_each)>=0 else 'var(--danger)')}"><strong>{nis(earnings_person_b_total-(totals['person_b']+assumed_rent_each))}</strong></td></tr>
          </table>
        </div>
      </div>
    </section>

    <!-- TRENDS -->
    <section id="trends" class="section">
      <div class="section-hd"><h2 class="section-title">{icon('overview','sec-icon')} Trends</h2></div>
      <div class="grid g-2">
        <div class="card">
          <h3 class="card-title" style="margin-bottom:14px">Monthly spend (stacked)</h3>
          <div class="chart-box"><canvas id="chart-monthly"></canvas></div>
        </div>
        <div class="card">
          <h3 class="card-title" style="margin-bottom:14px">Earnings vs spend</h3>
          <div class="chart-box"><canvas id="chart-earnings"></canvas></div>
        </div>
        <div class="card">
          <h3 class="card-title" style="margin-bottom:14px">Spending by category</h3>
          <div class="chart-box short"><canvas id="chart-donut"></canvas></div>
        </div>
        <div class="card no-pad">
          <div style="padding:18px 20px 0"><h3 class="card-title">Top categories</h3></div>
          <table>
            <thead><tr><th>Category</th><th class="num">Amount</th><th class="num">Share</th></tr></thead>
            <tbody>{cat_rows_html}</tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- EARNINGS -->
    <section id="earnings" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('income','sec-icon')} Earnings</h2>
        <div class="section-meta">Bank credits, 6 months</div>
      </div>
      <h4 class="sub-title"><span class="dot person_a"></span>{LA}</h4>
      <div class="grid g-4">
        {kpi_card('Salary', earnings_person_a_salary, nis(earnings_person_a_salary/months_count)+'/mo', color='var(--income)', icon_name='income')}
        {kpi_card('Rental income', earnings_person_a_rental, '₪2,100 × ' + str(len([t for t in bank_credits if t.get('earnings_kind')=='rental' and t['owner']=='person_a'])) + ' months', color='var(--income)', icon_name='home')}
        {kpi_card('Other credits', earnings_person_a_other, 'small inflows', color='var(--flag)', icon_name='transfer')}
        {kpi_card('Surplus 6 mo', earnings_person_a_total-(totals['person_a']+assumed_rent_each), 'after spend + rent', color=('var(--income)' if earnings_person_a_total-(totals['person_a']+assumed_rent_each)>=0 else 'var(--danger)'), icon_name='income')}
      </div>
      <h4 class="sub-title" style="margin-top:24px"><span class="dot person_b"></span>{LB}</h4>
      <div class="grid g-4">
        {kpi_card('Salary', earnings_person_b_salary, str(len([t for t in person_b_credits if t.get('earnings_kind')=='salary']))+' months visible', color='var(--income)', icon_name='income')}
        {kpi_card('Other credits', earnings_person_b_other, 'fee refunds, payments', color='var(--flag)', icon_name='transfer')}
        {kpi_card('Total visible', earnings_person_b_total, '', color='var(--income)', icon_name='income')}
        {kpi_card('Surplus 6 mo', earnings_person_b_total-(totals['person_b']+assumed_rent_each), 'after spend + rent', color=('var(--income)' if earnings_person_b_total-(totals['person_b']+assumed_rent_each)>=0 else 'var(--danger)'), icon_name='income')}
      </div>
      <h4 class="sub-title" style="margin-top:24px">All credits</h4>
      {table_card(['Date','Owner','Description','₪','Kind'], earnings_rows)}
    </section>

    <!-- HOUSE UTILITIES -->
    <section id="utilities" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('home','sec-icon')} House utilities</h2>
        <div class="section-meta">{nis(house_total)} · {nis(house_total/months_count)}/mo</div>
      </div>
      <p class="section-desc">Electric, water, gas, arnona, internet/TV, and food shopping. All shared 50/50.</p>
      <div class="card no-pad">
        <table>
          <thead><tr><th>Category</th><th class="num">{LA} paid</th><th class="num">{LB} paid</th><th class="num">Total</th><th>Imbalance</th></tr></thead>
          <tbody>{''.join(util_rows_html)}</tbody>
        </table>
      </div>
    </section>

    <!-- RENT -->
    <section id="rent" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('home','sec-icon')} Rent</h2>
        <div class="section-meta">monthly rent · paid to landlord</div>
      </div>
      <p class="section-desc">{f"One person pays the landlord each month; the other settles their share by transfer. Treated as net 0."}</p>
      <div class="grid g-3">
        {kpi_card(f'{LA} paid landlord', person_a_landlord_paid, str(person_a_landlord_count)+' months · '+(', '.join(person_a_landlord_months) if person_a_landlord_months else 'none'), icon_name='home')}
        {kpi_card(f'{LB} paid landlord', person_b_landlord_paid_inferred, str(person_b_landlord_count)+' months', icon_name='home')}
        {kpi_card(f'{LA} → {LB} transfers', rent_r2a, 'settlements', icon_name='transfer')}
      </div>
      <h4 class="sub-title" style="margin-top:20px">Rent timeline (cheques + settlements)</h4>
      {table_card(['Date','Direction','Type','₪'], rent_timeline_rows)}
    </section>

    <!-- CARS -->
    <section id="cars" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('car','sec-icon')} Cars</h2>
        <div class="section-meta">personal · each owns their own</div>
      </div>
      <div class="grid g-2">{car_block('person_a')}{car_block('person_b')}</div>
    </section>

    <!-- BUSINESS -->
    <section id="business" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('business','sec-icon')} Business / SaaS</h2>
        <div class="section-meta">{len(business)} items · {nis(business_total)} · {nis(business_total/months_count)}/mo</div>
      </div>
      <p class="section-desc">{f"{LA}'s business tools (dev, AI APIs, hosting). Personal cost — not split."}</p>
      {table_card(['Date','Owner','Merchant','Cat','₪'], business_rows)}
    </section>

    {loans_section_html}

    <!-- FURNITURE -->
    <section id="furniture" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('sofa','sec-icon')} Furniture & home</h2>
        <div class="section-meta">{len(furniture)} items · {nis(furniture_total)} · shared</div>
      </div>
      <p class="section-desc">Furniture, decor, household goods. Counted as shared.</p>
      <div class="grid g-3">
        {kpi_card(LA, furniture_by_owner['person_a'], '', color='var(--person_a)')}
        {kpi_card(LB, furniture_by_owner['person_b'], '', color='var(--person_b)')}
        {kpi_card('Combined', furniture_total, nis(furniture_total/months_count)+'/mo', color='var(--shared)')}
      </div>
      {table_card(['Date','Owner','Merchant','Cat','₪'], furniture_rows)}
    </section>

    <!-- RESTAURANTS -->
    <section id="restaurants" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('utensils','sec-icon')} Restaurants</h2>
        <div class="section-meta">{len(restaurants)} items · {nis(rest_total)} · pooled, not split</div>
      </div>
      <div class="grid g-3">
        {kpi_card(LA, rest_by_owner['person_a'], '', color='var(--person_a)')}
        {kpi_card(LB, rest_by_owner['person_b'], '', color='var(--person_b)')}
        {kpi_card('Combined', rest_total, nis(rest_total/months_count)+'/mo', color='var(--shared)')}
      </div>
      {table_card(['Date','Owner','Merchant','Cat','₪'], rest_rows)}
    </section>

    <!-- VACATIONS -->
    <section id="vacations" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('plane','sec-icon')} Vacations</h2>
        <div class="section-meta">{len(vacations)} items · {nis(vac_total)} · pooled, not split</div>
      </div>
      <div class="grid g-3">
        {kpi_card(LA, vac_by_owner['person_a'], '', color='var(--person_a)')}
        {kpi_card(LB, vac_by_owner['person_b'], '', color='var(--person_b)')}
        {kpi_card('Combined', vac_total, nis(vac_total/months_count)+'/mo', color='var(--shared)')}
      </div>
      {table_card(['Date','Owner','Merchant','Cat','₪'], vac_rows)}
    </section>

    <!-- SHARED ITEMS -->
    <section id="shared" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('check','sec-icon')} Auto-classified shared</h2>
        <div class="section-meta">{len(shared_items)} items · {nis(shared_cards_total)} (cards)</div>
      </div>
      {table_card(['Date','Owner','Merchant','Cat','₪','Why shared'], shared_rows)}
    </section>

    <!-- FLAGGED -->
    <section id="flagged" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('flag','sec-icon')} Flagged for review</h2>
        <div class="section-meta">{len(flagged)} items · {nis(flag_total)}</div>
      </div>
      <p class="section-desc">Didn't match an auto rule. Top 100 by amount.</p>
      {table_card(['Date','Owner','Merchant','Cat','₪','Why flagged'], flag_rows)}
    </section>

    <!-- TRANSFERS -->
    <section id="transfers" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('transfer','sec-icon')} Transfers & cash</h2>
        <div class="section-meta">{len(transfers)} items · {nis(transfers_total)} · excluded from spending</div>
      </div>
      {table_card(['Date','Owner','Merchant','Cat','₪'], transfer_rows)}
    </section>

    <!-- FUTURE ESTIMATION -->
    <section id="future" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('overview','sec-icon')} Future estimation</h2>
        <div class="section-meta">interactive · adjust assumptions to see impact</div>
      </div>
      <p class="section-desc">Forward-looking cash flow given upcoming life changes. Drag the sliders — chart and numbers update live.</p>

      <div class="grid g-2" style="grid-template-columns: 380px 1fr; gap: 18px;">
        <!-- Controls -->
        <div class="card future-controls">
          <h3 class="card-title" style="margin-bottom:16px">Scenario inputs</h3>

          <div class="ctrl-group">
            <div class="ctrl-head"><label class="ctrl-label">New apartment rent</label><span class="ctrl-value mono" id="v-rent">₪8,000</span></div>
            <input type="range" class="future-slider" id="s-rent" min="5400" max="15000" step="100" value="8000">
            <div class="ctrl-meta"><span>Starts <input type="month" id="s-rent-date" value="2026-08" class="future-date"></span><span>Current: ₪5,400/mo</span></div>
          </div>

          <div class="ctrl-group">
            <div class="ctrl-head"><label class="ctrl-label">Baby due</label><span class="ctrl-value" id="v-baby">Dec 2026</span></div>
            <input type="month" id="s-baby-date" value="2026-12" class="future-date wide">
          </div>

          <div class="ctrl-group">
            <div class="ctrl-head"><label class="ctrl-label">Baby setup (one-time)</label><span class="ctrl-value mono" id="v-setup">₪15,000</span></div>
            <input type="range" class="future-slider" id="s-setup" min="0" max="40000" step="500" value="15000">
            <div class="ctrl-meta"><span>Stroller, crib, gear, hospital co-pay</span></div>
          </div>

          <div class="ctrl-group">
            <div class="ctrl-head"><label class="ctrl-label">Baby monthly (first year)</label><span class="ctrl-value mono" id="v-baby-pm">₪3,500</span></div>
            <input type="range" class="future-slider" id="s-baby-pm" min="1000" max="8000" step="100" value="3500">
            <div class="ctrl-meta"><span>Diapers, formula, doctor, clothes</span></div>
          </div>

          <div class="ctrl-group">
            <div class="ctrl-head"><label class="ctrl-label">Daycare (מעון)</label><span class="ctrl-value mono" id="v-daycare">₪3,500/mo</span></div>
            <input type="range" class="future-slider" id="s-daycare" min="0" max="6000" step="100" value="3500">
            <div class="ctrl-meta"><span>Starts <input type="number" id="s-daycare-after" value="4" min="0" max="24" class="future-num"> months after birth</span></div>
          </div>

          <div class="ctrl-group">
            <div class="ctrl-head"><label class="ctrl-label">Paid maternity leave</label><span class="ctrl-value" id="v-mat">100 days · 100% paid</span></div>
            <div class="ctrl-row">
              <input type="range" class="future-slider" id="s-mat-days" min="0" max="180" step="5" value="100">
              <input type="range" class="future-slider" id="s-mat-pct" min="0" max="100" step="5" value="100">
            </div>
            <div class="ctrl-meta"><span>days</span><span>% of salary</span></div>
          </div>

          <div class="ctrl-group">
            <div class="ctrl-head"><label class="ctrl-label">Unpaid extension</label><span class="ctrl-value" id="v-unpaid">3 months · ₪0</span></div>
            <input type="range" class="future-slider" id="s-unpaid-months" min="0" max="9" step="1" value="3">
            <div class="ctrl-meta"><span>months after paid leave</span><span>{LB} earns 0 · {LA} unchanged</span></div>
          </div>

          <div class="ctrl-group">
            <div class="ctrl-head"><label class="ctrl-label">Annual vacation budget</label><span class="ctrl-value mono" id="v-vacation">₪30,000</span></div>
            <input type="range" class="future-slider" id="s-vacation" min="0" max="80000" step="1000" value="30000">
            <div class="ctrl-meta"><span>Spread evenly across the year</span></div>
          </div>

          <div class="ctrl-group">
            <div class="ctrl-head"><label class="ctrl-label">Starting cash buffer</label><span class="ctrl-value mono" id="v-buffer">₪0</span></div>
            <input type="range" class="future-slider" id="s-buffer" min="0" max="200000" step="5000" value="0">
            <div class="ctrl-meta"><span>What you have saved today</span></div>
          </div>

          <div class="ctrl-divider"><span>Future income</span></div>

          <div class="ctrl-group">
            <div class="ctrl-head"><label class="ctrl-label">{LB} new salary (net)</label><span class="ctrl-value mono" id="v-person_b-new">{CUR}15,000</span></div>
            <input type="range" class="future-slider" id="s-person_b-new" min="5000" max="35000" step="500" value="15000">
            <div class="ctrl-meta"><span>Starts <input type="month" id="s-person_b-new-date" value="2026-10" class="future-date"></span><span>Now: baseline</span></div>
          </div>

          <div class="ctrl-group">
            <div class="ctrl-head"><label class="ctrl-label">{LA} salary (net)</label><span class="ctrl-value mono" id="v-person_a-new">{CUR}0</span></div>
            <input type="range" class="future-slider" id="s-person_a-new" min="0" max="50000" step="500" value="0">
            <div class="ctrl-meta"><span>Constant across period</span><span id="v-person_a-required-hint">Set to required ↓</span></div>
            <button class="set-required-btn" id="btn-set-required" type="button" style="display:none">Set to required: <span id="set-required-amount">—</span></button>
          </div>

          <button id="future-reset" class="reset-btn" type="button">↻ Reset to defaults</button>
        </div>

        <!-- Chart + insights -->
        <div style="display:flex;flex-direction:column;gap:14px;min-width:0">
          <div class="grid g-4">
            <div class="card kpi-card"><div class="kpi-label">Avg income / mo</div><div class="kpi-value mono" style="color:var(--income)" id="kpi-future-income">—</div><div class="kpi-delta" id="kpi-future-income-sub">—</div></div>
            <div class="card kpi-card"><div class="kpi-label">Avg spend / mo</div><div class="kpi-value mono" id="kpi-future-spend">—</div><div class="kpi-delta" id="kpi-future-spend-sub">—</div></div>
            <div class="card kpi-card"><div class="kpi-label">Net 18-month</div><div class="kpi-value mono" id="kpi-future-net">—</div><div class="kpi-delta" id="kpi-future-net-sub">—</div></div>
            <div class="card kpi-card required-card"><div class="kpi-label">{LA} needs to earn</div><div class="kpi-value mono" style="color:var(--flag)" id="kpi-future-required">—</div><div class="kpi-delta" id="kpi-future-required-sub">to break even monthly</div></div>
          </div>

          <!-- Required income detail -->
          <div class="card required-detail" id="required-detail" style="margin-top:14px">
            <div class="card-hd" style="margin-bottom:8px"><h3 class="card-title">💼 Required income for {LA}</h3></div>
            <div class="required-grid">
              <div class="required-item">
                <div class="req-label">To break even (zero balance change)</div>
                <div class="req-val mono" id="req-breakeven">—</div>
              </div>
              <div class="required-item">
                <div class="req-label">To save ₪3K/mo</div>
                <div class="req-val mono" id="req-3k">—</div>
              </div>
              <div class="required-item">
                <div class="req-label">To save ₪7K/mo (recommended)</div>
                <div class="req-val mono" id="req-7k">—</div>
              </div>
              <div class="required-item">
                <div class="req-label">Peak month (baby+rent jump)</div>
                <div class="req-val mono" id="req-peak">—</div>
                <div class="req-meta" id="req-peak-month">—</div>
              </div>
            </div>
          </div>
          <div class="card">
            <div class="card-hd" style="margin-bottom:8px">
              <h3 class="card-title">Cash flow projection</h3>
              <div class="legend-inline">
                <span><span class="leg-dot" style="background:var(--income)"></span>Income</span>
                <span><span class="leg-dot" style="background:var(--person_b)"></span>Spend</span>
                <span><span class="leg-dot" style="background:var(--shared)"></span>Cumulative balance</span>
              </div>
            </div>
            <div class="chart-box"><canvas id="chart-future"></canvas></div>
          </div>
          <div class="card" id="insights-card">
            <h3 class="card-title" style="margin-bottom:14px">Insights</h3>
            <div id="insights-list" class="insights-list"></div>
          </div>
          <div class="table-card">
            <div class="table-filter">
              <h4 style="margin:0;font-size:13px;font-weight:600">Monthly breakdown</h4>
              <div class="filter-stats">
                <span class="stat-chip"><span class="stat-label">months</span> <span class="stat-val" id="future-months-count">—</span></span>
                <span class="stat-chip primary"><span class="stat-label">end balance</span> <span class="stat-val mono" id="future-end-balance">—</span></span>
              </div>
            </div>
            <div class="scroll" style="max-height:520px">
              <table>
                <thead><tr><th>Month</th><th class="num">Income</th><th class="num">Spend</th><th class="num">Net</th><th class="num">Balance</th><th>Notes</th></tr></thead>
                <tbody id="future-tbody"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ASSUMPTIONS -->
    <section id="assumptions" class="section">
      <div class="section-hd">
        <h2 class="section-title">{icon('info','sec-icon')} Assumptions</h2>
      </div>
      <p class="section-desc">Rules driving the classification. Tell me to change any.</p>
      <div class="grid g-3">{assumption_cards}</div>
    </section>

  </main>
</div>

<script>
'use strict';

// ─── Theme tokens (mirrors CSS) ─────────────────────────────────────────
const T = {{
  ink:'#f3f4fa', ink2:'#b8bdd4', ink3:'#7c84a3', ink4:'#50556b',
  person_a:'#5ea2ff', person_b:'#ff7ea8',
  shared:'#8ee0bf', personal:'#c3b6ff', flag:'#ffd166', income:'#7be0a5',
  cat:['#5ea2ff','#ff7ea8','#8ee0bf','#c3b6ff','#ffd166','#7be0a5','#ff9f6e','#86b8ff','#d39bff','#f8c1d7'],
  border:'rgba(255,255,255,.08)',
}};
Chart.defaults.color = T.ink2;
Chart.defaults.borderColor = T.border;
Chart.defaults.font.family = "'Inter','SF Pro Text',system-ui,sans-serif";
Chart.defaults.font.size = 11.5;
Chart.defaults.plugins.tooltip.backgroundColor = '#131623';
Chart.defaults.plugins.tooltip.titleColor = T.ink;
Chart.defaults.plugins.tooltip.bodyColor = T.ink2;
Chart.defaults.plugins.tooltip.borderColor = T.border;
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.titleFont = {{weight:600, size:12}};
Chart.defaults.plugins.tooltip.bodyFont = {{size:12}};

const months = {json.dumps(month_labels)};
const fmtNis = v => '₪' + Number(v).toLocaleString('en-IL', {{maximumFractionDigits:0}});

// ─── Animated counters ──────────────────────────────────────────────────
function animateCounter(el) {{
  const target = parseFloat(el.dataset.target || '0');
  const prefix = el.dataset.prefix || '';
  const dur = 950;
  const start = performance.now();
  function tick(now) {{
    const t = Math.min(1, (now - start) / dur);
    const eased = 1 - Math.pow(1 - t, 4);
    const v = Math.round(target * eased);
    el.textContent = prefix + v.toLocaleString('en-IL');
    if (t < 1) requestAnimationFrame(tick);
  }}
  requestAnimationFrame(tick);
}}

const counterObs = new IntersectionObserver(entries => {{
  for (const e of entries) {{
    if (e.isIntersecting) {{
      animateCounter(e.target);
      counterObs.unobserve(e.target);
    }}
  }}
}}, {{rootMargin: '0px 0px -40px 0px'}});
document.querySelectorAll('.counter').forEach(el => {{
  if (!el.dataset.prefix && el.textContent.startsWith('₪')) el.dataset.prefix = '₪';
  counterObs.observe(el);
}});

// ─── Sparklines ────────────────────────────────────────────────────────
document.querySelectorAll('canvas.sparkline').forEach(cv => {{
  const data = JSON.parse(cv.dataset.spark || '[]');
  const color = cv.dataset.color || T.ink3;
  new Chart(cv, {{
    type: 'line',
    data: {{
      labels: data.map((_,i) => i),
      datasets: [{{
        data,
        borderColor: color,
        backgroundColor: color + '22',
        fill: true, tension: 0.4,
        pointRadius: 0, borderWidth: 1.75,
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }}, tooltip: {{ enabled: false }} }},
      scales: {{ x: {{ display: false }}, y: {{ display: false }} }},
      elements: {{ line: {{ capBezierPoints: true }} }},
    }}
  }});
}});

// ─── Main charts ────────────────────────────────────────────────────────
new Chart(document.getElementById('chart-monthly'), {{
  type: 'bar',
  data: {{
    labels: months,
    datasets: [
      {{ label: 'Shared',      data: {json.dumps(shared_pm)},   backgroundColor: T.shared,   borderRadius: 6, borderSkipped: false }},
      {{ label: 'Personal',    data: {json.dumps(personal_pm)}, backgroundColor: T.personal, borderRadius: 6, borderSkipped: false }},
      {{ label: 'Restaurants', data: {json.dumps(rest_pm)},     backgroundColor: '#ff9f6e',  borderRadius: 6, borderSkipped: false }},
      {{ label: 'Vacations',   data: {json.dumps(vac_pm)},      backgroundColor: '#d39bff',  borderRadius: 6, borderSkipped: false }},
      {{ label: 'Flagged',     data: {json.dumps(flag_pm)},     backgroundColor: T.flag,     borderRadius: 6, borderSkipped: false }},
    ],
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ position:'bottom', labels:{{ padding:14, boxWidth:8, boxHeight:8, usePointStyle:true, pointStyle:'circle' }} }},
      tooltip: {{ callbacks: {{ label: c => c.dataset.label + ': ' + fmtNis(c.parsed.y) }} }}
    }},
    scales: {{
      x: {{ stacked: true, grid: {{ display: false }} }},
      y: {{ stacked: true, ticks: {{ callback: fmtNis }}, grid: {{ color: T.border }}, border: {{ display: false }} }}
    }},
    animation: {{ duration: 600, easing: 'easeOutQuart' }},
  }}
}});

new Chart(document.getElementById('chart-earnings'), {{
  type: 'line',
  data: {{
    labels: months,
    datasets: [
      {{ label: 'Income',     data: {json.dumps(earnings_pm)}, borderColor: T.income, backgroundColor: T.income+'1f', fill: true, tension: 0.4, pointRadius: 4, pointHoverRadius: 6, borderWidth: 2.5, pointBackgroundColor: T.income }},
      {{ label: '{LA} spend', data: {json.dumps(person_a_pm)},     borderColor: T.person_a,   borderDash: [4,4], fill: false, tension: 0.4, pointRadius: 3, borderWidth: 2, pointBackgroundColor: T.person_a }},
      {{ label: '{LB} spend',data: {json.dumps(person_b_pm)},    borderColor: T.person_b,  borderDash: [4,4], fill: false, tension: 0.4, pointRadius: 3, borderWidth: 2, pointBackgroundColor: T.person_b }},
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ position:'bottom', labels:{{ padding:14, boxWidth:8, boxHeight:8, usePointStyle:true, pointStyle:'circle' }} }},
      tooltip: {{ callbacks: {{ label: c => c.dataset.label + ': ' + fmtNis(c.parsed.y) }} }}
    }},
    scales: {{
      x: {{ grid: {{ display: false }} }},
      y: {{ ticks: {{ callback: fmtNis }}, grid: {{ color: T.border }}, border: {{ display: false }} }}
    }},
    animation: {{ duration: 700, easing: 'easeOutQuart' }},
  }}
}});

new Chart(document.getElementById('chart-donut'), {{
  type: 'doughnut',
  data: {{
    labels: {json.dumps(cat_labels)},
    datasets: [{{
      data: {json.dumps(cat_data)},
      backgroundColor: T.cat,
      borderColor: '#131623',
      borderWidth: 3,
      hoverOffset: 8,
      hoverBorderWidth: 0,
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    cutout: '64%',
    plugins: {{
      legend: {{ position: 'right', labels: {{ padding: 10, boxWidth: 10, boxHeight: 10, usePointStyle: true, pointStyle: 'circle', font: {{ size: 11.5 }} }} }},
      tooltip: {{ callbacks: {{ label: c => c.label + ': ' + fmtNis(c.parsed) }} }}
    }},
    animation: {{ animateScale: true, animateRotate: true, duration: 800, easing: 'easeOutQuart' }},
  }}
}});

// ─── Scroll spy for sidebar nav ─────────────────────────────────────────
const navLinks = document.querySelectorAll('aside.nav nav.nav-list a, .mobile-nav a');
const sections = Array.from(document.querySelectorAll('section[id]')).reverse();
function updateActiveNav() {{
  const y = window.scrollY + 120;
  let activeId = null;
  for (const s of sections) {{
    if (s.offsetTop <= y) {{ activeId = s.id; break; }}
  }}
  navLinks.forEach(a => {{
    const href = a.getAttribute('href');
    a.classList.toggle('active', href === '#' + activeId);
  }});
}}
let rafId = null;
window.addEventListener('scroll', () => {{
  if (rafId) cancelAnimationFrame(rafId);
  rafId = requestAnimationFrame(updateActiveNav);
}}, {{ passive: true }});
updateActiveNav();

// ─── Sortable tables ────────────────────────────────────────────────────
document.querySelectorAll('table[data-sortable]').forEach(table => {{
  const headers = table.querySelectorAll('thead th');
  headers.forEach((th, colIdx) => {{
    th.addEventListener('click', () => {{
      const asc = !th.classList.contains('sort-asc');
      headers.forEach(h => h.classList.remove('sort-asc','sort-desc'));
      th.classList.add(asc ? 'sort-asc' : 'sort-desc');
      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
      rows.sort((a,b) => {{
        const ea = a.children[colIdx], eb = b.children[colIdx];
        const da = ea?.dataset.amount, db = eb?.dataset.amount;
        if (da !== undefined && db !== undefined) {{
          const na = parseFloat(da), nb = parseFloat(db);
          return asc ? na-nb : nb-na;
        }}
        const ca = (ea?.innerText || '').trim();
        const cb = (eb?.innerText || '').trim();
        const na = parseFloat(ca.replace(/[^\\d.-]/g,''));
        const nb = parseFloat(cb.replace(/[^\\d.-]/g,''));
        if (!isNaN(na) && !isNaN(nb)) return asc ? na-nb : nb-na;
        return asc ? ca.localeCompare(cb) : cb.localeCompare(ca);
      }});
      rows.forEach(r => tbody.appendChild(r));
      // Recompute stats after sort
      const card = table.closest('.table-card');
      if (card) recomputeTableStats(card);
    }});
  }});
}});

// ─── Table filter system (per-table search + sum) ───────────────────────
function recomputeTableStats(tableCard) {{
  const tid = tableCard.dataset.tableId;
  const amountCol = parseInt(tableCard.dataset.amountCol || '4', 10);
  const tbody = tableCard.querySelector('tbody');
  if (!tbody) return;
  let count = 0, sum = 0;
  for (const tr of tbody.querySelectorAll('tr')) {{
    if (tr.classList.contains('hidden') || tr.style.display === 'none') continue;
    if (tr.classList.contains('total-row')) continue;
    count++;
    const amtCell = tr.children[amountCol];
    if (amtCell) {{
      const raw = amtCell.dataset.amount;
      const v = raw !== undefined ? parseFloat(raw) : parseFloat((amtCell.innerText || '').replace(/[^\\d.-]/g,''));
      if (!isNaN(v)) sum += v;
    }}
  }}
  const stats = document.querySelector('.filter-stats[data-table="'+tid+'"]');
  if (stats) {{
    const cEl = stats.querySelector('[data-stat="count"]');
    const sEl = stats.querySelector('[data-stat="sum"]');
    if (cEl) cEl.textContent = count.toLocaleString('en-IL');
    if (sEl) sEl.textContent = '₪' + Math.round(sum).toLocaleString('en-IL');
  }}
}}

function applyTableFilter(tableCard) {{
  const tid = tableCard.dataset.tableId;
  const input = document.querySelector('.filter-input[data-table="'+tid+'"]');
  const q = (input?.value || '').trim().toLowerCase();
  const ownerFilter = document.querySelector('.filter-chip.active')?.dataset.owner || 'both';
  const tbody = tableCard.querySelector('tbody');
  if (!tbody) return;
  for (const tr of tbody.querySelectorAll('tr')) {{
    if (tr.classList.contains('total-row')) continue;
    const txt = (tr.dataset.search || tr.innerText || '').toLowerCase();
    const matchesSearch = !q || txt.includes(q);
    const rowOwner = tr.dataset.owner;
    const matchesOwner = ownerFilter === 'both' || !rowOwner || rowOwner === ownerFilter;
    tr.classList.toggle('hidden', !(matchesSearch && matchesOwner));
  }}
  recomputeTableStats(tableCard);
  // Show/hide clear button
  const wrap = input?.closest('.filter-input-wrap');
  if (wrap) wrap.classList.toggle('has-value', !!q);
}}

// Initial stats compute + wire up listeners
document.querySelectorAll('.table-card').forEach(card => {{
  recomputeTableStats(card);
}});
document.querySelectorAll('.filter-input').forEach(inp => {{
  let timer = null;
  inp.addEventListener('input', () => {{
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {{
      const card = document.querySelector('.table-card[data-table-id="'+inp.dataset.table+'"]');
      if (card) applyTableFilter(card);
    }}, 120);
  }});
  inp.addEventListener('keydown', e => {{ if (e.key === 'Escape') {{ inp.value = ''; inp.dispatchEvent(new Event('input')); }} }});
}});
document.querySelectorAll('.filter-clear').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const inp = document.querySelector('.filter-input[data-table="'+btn.dataset.table+'"]');
    if (inp) {{ inp.value = ''; inp.focus(); inp.dispatchEvent(new Event('input')); }}
  }});
}});

// ─── Future Estimation ─────────────────────────────────────────────────
const BASELINE = {json.dumps(baseline)};
const FUTURE_DEFAULTS = {{
  rent: 8000, rentDate: '2026-08',
  babyDate: '2026-12',
  setup: 15000,
  babyPm: 3500,
  daycare: 3500, daycareAfter: 4,
  matDays: 100, matPct: 100,
  unpaidMonths: 3,
  vacation: 30000,
  buffer: 0,
  person_bNew: 15000, person_bNewDate: '2026-10',
  person_aNew: Math.round(BASELINE.person_a_salary_pm),
}};

const futureEls = {{
  rent: document.getElementById('s-rent'),
  rentDate: document.getElementById('s-rent-date'),
  babyDate: document.getElementById('s-baby-date'),
  setup: document.getElementById('s-setup'),
  babyPm: document.getElementById('s-baby-pm'),
  daycare: document.getElementById('s-daycare'),
  daycareAfter: document.getElementById('s-daycare-after'),
  matDays: document.getElementById('s-mat-days'),
  matPct: document.getElementById('s-mat-pct'),
  unpaidMonths: document.getElementById('s-unpaid-months'),
  vacation: document.getElementById('s-vacation'),
  buffer: document.getElementById('s-buffer'),
  person_bNew: document.getElementById('s-person_b-new'),
  person_bNewDate: document.getElementById('s-person_b-new-date'),
  person_aNew: document.getElementById('s-person_a-new'),
}};
// Initialize person A slider to baseline
futureEls.person_aNew.value = FUTURE_DEFAULTS.person_aNew;

function fmtMonth(d) {{
  return d.toLocaleString('en-US', {{ month: 'short', year: '2-digit' }});
}}
function ymStr(d) {{
  return d.toLocaleString('en-US', {{ month: 'short', year: 'numeric' }});
}}
function parseYM(s) {{
  const [y,m] = s.split('-').map(Number); return new Date(y, m-1, 1);
}}
function monthDiff(a, b) {{
  return (b.getFullYear()-a.getFullYear())*12 + (b.getMonth()-a.getMonth());
}}

function computeFuture() {{
  const cfg = {{
    rent: +futureEls.rent.value,
    rentStart: parseYM(futureEls.rentDate.value),
    babyStart: parseYM(futureEls.babyDate.value),
    setup: +futureEls.setup.value,
    babyPm: +futureEls.babyPm.value,
    daycare: +futureEls.daycare.value,
    daycareAfter: +futureEls.daycareAfter.value,
    matDays: +futureEls.matDays.value,
    matPct: +futureEls.matPct.value / 100,
    unpaidMonths: +futureEls.unpaidMonths.value,
    vacationPm: +futureEls.vacation.value / 12,
    buffer: +futureEls.buffer.value,
    person_bNew: +futureEls.person_bNew.value,
    person_bNewStart: parseYM(futureEls.person_bNewDate.value),
    person_aNew: +futureEls.person_aNew.value,
  }};

  // Projection start: month after the data period (we have data through Mar 2026; projection starts May 2026)
  const start = new Date(2026, 4, 1); // May 2026
  const months = [];
  for (let i = 0; i < 24; i++) {{
    const d = new Date(start.getFullYear(), start.getMonth()+i, 1);
    months.push(d);
  }}

  // Daycare start = babyStart + daycareAfter months
  const daycareStart = new Date(cfg.babyStart.getFullYear(), cfg.babyStart.getMonth()+cfg.daycareAfter, 1);
  // Paid maternity end = babyStart + matDays (rounded to nearest month)
  const matMonths = cfg.matDays / 30.44;
  const matEnd = new Date(cfg.babyStart.getFullYear(), cfg.babyStart.getMonth()+Math.ceil(matMonths), 1);
  // Unpaid extension end
  const unpaidEnd = new Date(matEnd.getFullYear(), matEnd.getMonth()+cfg.unpaidMonths, 1);

  let balance = cfg.buffer;
  const rows = [];

  months.forEach((d, idx) => {{
    const ym = d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0');
    let income = 0, spend = 0, events = [];

    // Income — person A uses adjustable slider; person B uses baseline until salary bump date
    income += cfg.person_aNew;
    income += BASELINE.rental_income_pm;
    // person B base salary varies: baseline OR new salary after person_bNewStart
    const person_bBase = d >= cfg.person_bNewStart ? cfg.person_bNew : BASELINE.person_b_salary_pm;
    // Maternity: paid period (matEnd) → unpaid extension (unpaidEnd) → resume
    if (d >= cfg.babyStart && d < matEnd) {{
      // Paid maternity (100% by default = Bituach Leumi covers)
      income += person_bBase * cfg.matPct;
      events.push({{tag:'maternity', txt: cfg.matPct >= 1 ? 'maternity (100% paid)' : `maternity (${{Math.round(cfg.matPct*100)}}% paid)`}});
    }} else if (d >= matEnd && d < unpaidEnd) {{
      // Unpaid extension — person B earns ₪0
      income += 0;
      events.push({{tag:'maternity', txt:'unpaid leave'}});
    }} else {{
      income += person_bBase;
      if (d.getTime() === cfg.person_bNewStart.getTime()) events.push({{tag:'rent', txt:'{LB} new salary'}});
      if (d.getTime() === unpaidEnd.getTime() && cfg.unpaidMonths > 0) events.push({{tag:'maternity', txt:'{LB} returns to work'}});
    }}

    // Rent: current ₪5,400 until rentStart, then new rent
    const rent = d >= cfg.rentStart ? cfg.rent : BASELINE.rent_pm;
    spend += rent;
    if (d.getTime() === cfg.rentStart.getTime()) events.push({{tag:'rent', txt:'new rent starts'}});

    // Regular spend (utilities, groceries, restaurants, cars, business, subs, furniture, loans)
    spend += BASELINE.utilities_pm
           + BASELINE.groceries_pm
           + BASELINE.restaurants_pm
           + BASELINE.cars_pm
           + BASELINE.business_pm
           + BASELINE.subs_gym_pm
           + BASELINE.furniture_pm
           + BASELINE.loans_pm;
    // Vacation budget
    spend += cfg.vacationPm;

    // Baby costs (only from baby month onwards, first year)
    const monthsSinceBaby = monthDiff(cfg.babyStart, d);
    if (d.getTime() === cfg.babyStart.getTime()) {{
      // One-time setup paid in baby month (could split across last preg month too)
      spend += cfg.setup;
      events.push({{tag:'baby', txt:'baby born + setup'}});
    }}
    if (monthsSinceBaby >= 0 && monthsSinceBaby < 12) {{
      spend += cfg.babyPm;
    }} else if (monthsSinceBaby >= 12) {{
      spend += cfg.babyPm * 0.6; // toddler costs drop a bit (no more formula etc.)
    }}
    // Daycare
    if (d >= daycareStart && monthsSinceBaby >= 0) {{
      spend += cfg.daycare;
      if (d.getTime() === daycareStart.getTime()) events.push({{tag:'daycare', txt:'daycare starts'}});
    }}

    const net = income - spend;
    balance += net;
    rows.push({{ d, idx, income, spend, net, balance, events }});
  }});

  return {{ cfg, rows, daycareStart, matEnd }};
}}

// ─── Render the Future section ─────────────────────────────────────────
let futureChart = null;

function renderFuture() {{
  const cfg = {{
    rent: +futureEls.rent.value,
    babyDate: futureEls.babyDate.value,
    setup: +futureEls.setup.value,
    babyPm: +futureEls.babyPm.value,
    daycare: +futureEls.daycare.value,
    daycareAfter: +futureEls.daycareAfter.value,
    matDays: +futureEls.matDays.value,
    matPct: +futureEls.matPct.value,
    unpaidMonths: +futureEls.unpaidMonths.value,
    vacation: +futureEls.vacation.value,
    buffer: +futureEls.buffer.value,
  }};

  // Update value labels
  document.getElementById('v-rent').textContent = '₪' + cfg.rent.toLocaleString();
  document.getElementById('v-setup').textContent = '₪' + cfg.setup.toLocaleString();
  document.getElementById('v-baby-pm').textContent = '₪' + cfg.babyPm.toLocaleString();
  document.getElementById('v-daycare').textContent = '₪' + cfg.daycare.toLocaleString() + '/mo';
  document.getElementById('v-vacation').textContent = '₪' + cfg.vacation.toLocaleString();
  document.getElementById('v-buffer').textContent = '₪' + cfg.buffer.toLocaleString();
  document.getElementById('v-baby').textContent = ymStr(parseYM(cfg.babyDate));
  document.getElementById('v-mat').textContent = (+futureEls.matDays.value) + ' days · ' + cfg.matPct + '% paid';
  const unpaidM = +futureEls.unpaidMonths.value;
  document.getElementById('v-unpaid').textContent = unpaidM === 0 ? 'none' : (unpaidM + ' month' + (unpaidM>1?'s':'') + ' · ₪0');
  document.getElementById('v-person_b-new').textContent = '₪' + (+futureEls.person_bNew.value).toLocaleString();
  document.getElementById('v-person_a-new').textContent = '₪' + (+futureEls.person_aNew.value).toLocaleString();

  const {{ rows }} = computeFuture();

  // KPIs
  const avgIncome = rows.reduce((s,r) => s+r.income, 0) / rows.length;
  const avgSpend  = rows.reduce((s,r) => s+r.spend, 0) / rows.length;
  const first18 = rows.slice(0,18);
  const netOutcome = first18.reduce((s,r) => s+r.net, 0);
  const endBal = first18[first18.length-1].balance;

  // ─── Required income calc ──────────────────────────────────────────
  // For each month: spend - (income - person_aNew) = the contribution person A needs that month.
  // Average across 18 months = sustainable break-even monthly salary.
  // For peak: the single month with highest required = max needed in any given month.
  const person_aContribCurrent = +futureEls.person_aNew.value;
  const requiredPerMonth = first18.map(r => {{
    const incomeWithoutPersonA = r.income - person_aContribCurrent;
    return r.spend - incomeWithoutPersonA;
  }});
  const avgRequired = requiredPerMonth.reduce((s,v) => s+v, 0) / requiredPerMonth.length;
  const peakRequired = Math.max(...requiredPerMonth);
  const peakIdx = requiredPerMonth.indexOf(peakRequired);
  const peakMonth = first18[peakIdx];
  // Target-savings calc — to save Xk/mo on top of break-even
  const reqBreakEven = avgRequired;
  const req3k = avgRequired + 3000;
  const req7k = avgRequired + 7000;

  document.getElementById('req-breakeven').textContent = fmtNis(Math.round(reqBreakEven));
  document.getElementById('req-3k').textContent = fmtNis(Math.round(req3k));
  document.getElementById('req-7k').textContent = fmtNis(Math.round(req7k));
  document.getElementById('req-peak').textContent = fmtNis(Math.round(peakRequired));
  document.getElementById('req-peak-month').textContent = peakMonth ? ymStr(peakMonth.d) : '';
  document.getElementById('kpi-future-required').textContent = fmtNis(Math.round(reqBreakEven));
  document.getElementById('kpi-future-required-sub').textContent = reqBreakEven > person_aContribCurrent
    ? `+${{fmtNis(Math.round(reqBreakEven - person_aContribCurrent))}}/mo vs current ₪${{person_aContribCurrent.toLocaleString()}}`
    : `${{fmtNis(Math.round(person_aContribCurrent - reqBreakEven))}}/mo surplus over current`;

  // Set-to-required button
  const setBtn = document.getElementById('btn-set-required');
  if (Math.abs(reqBreakEven - person_aContribCurrent) > 100) {{
    setBtn.style.display = 'block';
    document.getElementById('set-required-amount').textContent = '₪' + Math.round(reqBreakEven).toLocaleString();
  }} else {{
    setBtn.style.display = 'none';
  }}
  document.getElementById('kpi-future-income').textContent = fmtNis(Math.round(avgIncome));
  document.getElementById('kpi-future-income-sub').textContent = '{LA} + {LB} + rental';
  document.getElementById('kpi-future-spend').textContent = fmtNis(Math.round(avgSpend));
  document.getElementById('kpi-future-spend-sub').textContent = 'all categories incl. baby';
  document.getElementById('kpi-future-net').textContent = fmtNis(Math.round(netOutcome));
  document.getElementById('kpi-future-net-sub').textContent = endBal >= 0 ? 'Net positive over 18 mo' : 'Net negative — needs cash buffer';
  document.getElementById('kpi-future-net').style.color = netOutcome >= 0 ? 'var(--income)' : 'var(--danger)';

  // Chart
  const labels = rows.map(r => fmtMonth(r.d));
  const incomeArr = rows.map(r => Math.round(r.income));
  const spendArr = rows.map(r => Math.round(r.spend));
  const balArr = rows.map(r => Math.round(r.balance));

  if (futureChart) futureChart.destroy();
  futureChart = new Chart(document.getElementById('chart-future'), {{
    data: {{
      labels,
      datasets: [
        {{ type:'line', label:'Income', data: incomeArr, borderColor: T.income, backgroundColor: 'transparent', fill:false, tension:0.35, pointRadius:0, borderWidth: 2.5, yAxisID: 'y' }},
        {{ type:'line', label:'Spend', data: spendArr, borderColor: T.person_b, backgroundColor: 'transparent', fill:false, tension:0.35, pointRadius:0, borderWidth: 2.5, borderDash: [4,4], yAxisID: 'y' }},
        {{ type:'line', label:'Balance', data: balArr, borderColor: T.shared, backgroundColor: T.shared+'1e', fill:true, tension:0.35, pointRadius:3, pointHoverRadius:5, borderWidth: 2, pointBackgroundColor: T.shared, yAxisID: 'y2' }},
      ],
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: c => c.dataset.label + ': ' + fmtNis(c.parsed.y) }} }},
      }},
      scales: {{
        x: {{ grid: {{ display: false }} }},
        y: {{ position:'left', ticks: {{ callback: fmtNis }}, grid: {{ color: T.border }}, border: {{ display: false }} }},
        y2: {{ position:'right', ticks: {{ callback: fmtNis, color: T.shared }}, grid: {{ display: false }}, border: {{ display: false }} }},
      }},
      animation: {{ duration: 300 }},
    }},
  }});

  // Insights
  const insights = [];
  const firstDeficitIdx = rows.findIndex(r => r.balance < 0);
  if (firstDeficitIdx >= 0) {{
    const def = rows[firstDeficitIdx];
    const needed = Math.abs(def.balance) + 10000;
    insights.push({{kind:'danger', icon:'flag', html: `Balance goes <strong>negative in ${{ymStr(def.d)}}</strong>. To avoid red ink, build a cash buffer of at least <strong>${{fmtNis(needed)}}</strong> before then.`}});
  }} else {{
    insights.push({{kind:'good', icon:'check', html: `Balance stays positive across all 24 months. End balance: <strong>${{fmtNis(rows[rows.length-1].balance)}}</strong>.`}});
  }}

  // Rent jump impact
  const rentDiff = cfg.rent - BASELINE.rent_pm;
  insights.push({{kind:'warn', icon:'info', html: `Rent jump adds <strong>${{fmtNis(rentDiff)}}/mo</strong> starting ${{ymStr(parseYM(futureEls.rentDate.value))}} (₪${{(rentDiff/2).toLocaleString()}}/mo each).`}});

  // Baby month
  const babyMonthRow = rows.find(r => r.d.getTime() === parseYM(cfg.babyDate).getTime());
  if (babyMonthRow) {{
    insights.push({{kind:'warn', icon:'info', html: `Baby month: spend <strong>${{fmtNis(babyMonthRow.spend)}}</strong> (incl. ${{fmtNis(cfg.setup)}} one-time setup). Net <strong>${{fmtNis(babyMonthRow.net)}}</strong>.`}});
  }}

  // Lowest balance month
  const lowest = rows.reduce((min, r) => r.balance < min.balance ? r : min, rows[0]);
  if (lowest.balance < cfg.buffer) {{
    insights.push({{kind:'warn', icon:'info', html: `Lowest balance: <strong>${{fmtNis(lowest.balance)}}</strong> in ${{ymStr(lowest.d)}}.`}});
  }}

  // Monthly stress (deficits)
  const deficitMonths = rows.filter(r => r.net < 0).length;
  if (deficitMonths > 0) {{
    insights.push({{kind:'warn', icon:'flag', html: `<strong>${{deficitMonths}} of 24 months</strong> have negative monthly net (spend exceeds income). Cash buffer absorbs them.`}});
  }}

  const insEl = document.getElementById('insights-list');
  insEl.innerHTML = insights.map(i => `<div class="insight ${{i.kind}}"><div class="insight-ic">${{ICONS_JS[i.icon]||''}}</div><div>${{i.html}}</div></div>`).join('');

  // Monthly table
  const tbody = document.getElementById('future-tbody');
  tbody.innerHTML = rows.map(r => {{
    const tagHtml = r.events.map(e => `<span class="month-tag ${{e.tag}}">${{e.txt}}</span>`).join('');
    const isDef = r.balance < 0;
    const isEvent = r.events.length > 0;
    return `<tr class="${{isDef?'month-deficit':''}} ${{isEvent?'month-event':''}}">
      <td class="small mono">${{ymStr(r.d)}}</td>
      <td class="num mono">${{fmtNis(Math.round(r.income))}}</td>
      <td class="num mono">${{fmtNis(Math.round(r.spend))}}</td>
      <td class="num mono" style="color:${{r.net>=0?'var(--income)':'var(--danger)'}}">${{fmtNis(Math.round(r.net))}}</td>
      <td class="num mono" style="font-weight:600">${{fmtNis(Math.round(r.balance))}}</td>
      <td class="small">${{tagHtml}}</td>
    </tr>`;
  }}).join('');
  document.getElementById('future-months-count').textContent = rows.length;
  document.getElementById('future-end-balance').textContent = fmtNis(Math.round(rows[rows.length-1].balance));
}}

const ICONS_JS = {{
  flag: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>',
  info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
}};

// Wire up listeners (debounced for sliders)
let futureTimer = null;
function scheduleFuture() {{
  if (futureTimer) cancelAnimationFrame(futureTimer);
  futureTimer = requestAnimationFrame(renderFuture);
}}
Object.values(futureEls).forEach(el => {{
  el.addEventListener('input', scheduleFuture);
  el.addEventListener('change', scheduleFuture);
}});
document.getElementById('future-reset').addEventListener('click', () => {{
  futureEls.rent.value = FUTURE_DEFAULTS.rent;
  futureEls.rentDate.value = FUTURE_DEFAULTS.rentDate;
  futureEls.babyDate.value = FUTURE_DEFAULTS.babyDate;
  futureEls.setup.value = FUTURE_DEFAULTS.setup;
  futureEls.babyPm.value = FUTURE_DEFAULTS.babyPm;
  futureEls.daycare.value = FUTURE_DEFAULTS.daycare;
  futureEls.daycareAfter.value = FUTURE_DEFAULTS.daycareAfter;
  futureEls.matDays.value = FUTURE_DEFAULTS.matDays;
  futureEls.matPct.value = FUTURE_DEFAULTS.matPct;
  futureEls.unpaidMonths.value = FUTURE_DEFAULTS.unpaidMonths;
  futureEls.vacation.value = FUTURE_DEFAULTS.vacation;
  futureEls.buffer.value = FUTURE_DEFAULTS.buffer;
  futureEls.person_bNew.value = FUTURE_DEFAULTS.person_bNew;
  futureEls.person_bNewDate.value = FUTURE_DEFAULTS.person_bNewDate;
  futureEls.person_aNew.value = FUTURE_DEFAULTS.person_aNew;
  renderFuture();
}});

// "Set person A salary to required" one-click button
document.getElementById('btn-set-required').addEventListener('click', () => {{
  const target = document.getElementById('set-required-amount').textContent.replace(/[^\\d]/g,'');
  const v = parseInt(target, 10);
  if (!isNaN(v)) {{
    futureEls.person_aNew.value = Math.min(v, +futureEls.person_aNew.max);
    renderFuture();
  }}
}});

// Initial render — defer to let charts library load
setTimeout(renderFuture, 50);

// ─── Owner filter chips ────────────────────────────────────────────────
const chips = document.querySelectorAll('.filter-chip');
const filterBanner = document.getElementById('filter-banner');
const filterBannerText = document.getElementById('filter-banner-text');
const filterIndicator = document.getElementById('filter-indicator');

function setFilter(owner) {{
  chips.forEach(c => c.classList.remove('active','person_a','person_b'));
  const target = document.querySelector('.filter-chip[data-owner="'+owner+'"]');
  if (target) {{
    target.classList.add('active');
    if (owner !== 'both') target.classList.add(owner);
  }}
  // Update indicator + banner
  filterIndicator.classList.remove('active','person_a','person_b');
  filterBanner.classList.remove('active','person_a','person_b');
  if (owner !== 'both') {{
    filterIndicator.classList.add('active', owner);
    filterIndicator.textContent = 'showing ' + owner;
    filterBanner.classList.add('active', owner);
    filterBannerText.textContent = 'Showing ' + owner.charAt(0).toUpperCase()+owner.slice(1) + ' only — KPI cards still show combined totals; tables and amounts are filtered';
  }}
  // Apply to all tables
  document.querySelectorAll('.table-card').forEach(applyTableFilter);
  document.querySelectorAll('.card > table, .card.no-pad table').forEach(t => {{
    if (t.closest('.table-card')) return;
    for (const tr of t.querySelectorAll('tbody tr')) {{
      if (tr.classList.contains('total-row')) continue;
      const ro = tr.dataset.owner;
      const show = owner === 'both' || !ro || ro === owner;
      tr.style.display = show ? '' : 'none';
    }}
  }});
  // Dim per-owner sections that don't match
  document.querySelectorAll('.person-card, .glow-person_a, .glow-person_b').forEach(c => {{
    const isPersonA = c.classList.contains('person_a') || c.classList.contains('glow-person_a');
    const isPersonB = c.classList.contains('person_b') || c.classList.contains('glow-person_b');
    if (owner === 'both' || (owner === 'person_a' && isPersonA) || (owner === 'person_b' && isPersonB)) {{
      c.style.opacity = '1'; c.style.filter = 'none';
    }} else if (isPersonA || isPersonB) {{
      c.style.opacity = '0.35'; c.style.filter = 'saturate(0.5)';
    }}
  }});
}}
chips.forEach(chip => chip.addEventListener('click', () => setFilter(chip.dataset.owner)));
document.getElementById('filter-banner-clear').addEventListener('click', () => setFilter('both'));

// ─── Sticky controls scroll-state ───────────────────────────────────────
const topCtrls = document.getElementById('top-controls');
const scrollTopBtn = document.getElementById('btn-scroll-top');
function onScroll() {{
  const y = window.scrollY;
  topCtrls.classList.toggle('scrolled', y > 8);
  scrollTopBtn.classList.toggle('visible', y > 400);
}}
window.addEventListener('scroll', () => requestAnimationFrame(onScroll), {{ passive: true }});
onScroll();

scrollTopBtn.addEventListener('click', () => window.scrollTo({{ top: 0, behavior: 'smooth' }}));

// ─── Print ──────────────────────────────────────────────────────────────
document.getElementById('btn-print').addEventListener('click', () => window.print());

// ─── Collapse all <details> ────────────────────────────────────────────
let allCollapsed = false;
document.getElementById('btn-collapse-all').addEventListener('click', () => {{
  allCollapsed = !allCollapsed;
  document.querySelectorAll('details').forEach(d => d.open = !allCollapsed);
}});

// ─── Global search palette (⌘K / ctrl+K) ───────────────────────────────
const searchOverlay = document.getElementById('search-overlay');
const searchInput = document.getElementById('search-palette-input');
const searchResults = document.getElementById('search-palette-results');
const globalSearchInput = document.getElementById('global-search-input');

// Build an index of all searchable rows
const SEARCH_INDEX = [];
document.querySelectorAll('.table-card tbody tr, .card.no-pad tbody tr').forEach(tr => {{
  const txt = (tr.dataset.search || tr.innerText || '').trim();
  if (!txt) return;
  // Find which section this row belongs to
  const section = tr.closest('section[id]');
  if (!section) return;
  const title = section.querySelector('.section-title')?.innerText.trim() || section.id;
  const merchant = tr.querySelector('.merchant')?.innerText.trim() || '';
  const amount = tr.querySelector('[data-amount]')?.dataset.amount || '';
  const owner = tr.dataset.owner || '';
  const date = tr.querySelector('.small.mono')?.innerText.trim() || '';
  SEARCH_INDEX.push({{ txt: txt.toLowerCase(), title, sectionId: section.id, merchant, amount: parseFloat(amount)||0, owner, date, row: tr }});
}});

function openSearch() {{
  searchOverlay.classList.add('open');
  searchInput.value = globalSearchInput.value || '';
  setTimeout(() => searchInput.focus(), 50);
  doSearch();
}}
function closeSearch() {{ searchOverlay.classList.remove('open'); }}

let focusedIdx = -1;
function doSearch() {{
  const q = searchInput.value.trim().toLowerCase();
  let results;
  if (!q) {{
    results = SEARCH_INDEX.slice(0, 20);
  }} else {{
    results = SEARCH_INDEX
      .filter(r => r.txt.includes(q) || String(r.amount).includes(q))
      .slice(0, 50);
  }}
  if (!results.length) {{
    searchResults.innerHTML = '<div class="search-palette-empty">No matches for "' + q + '"</div>';
    return;
  }}
  focusedIdx = 0;
  searchResults.innerHTML = results.map((r,i) => `
    <div class="search-result ${{i===focusedIdx?'focused':''}}" data-section="${{r.sectionId}}" data-idx="${{i}}">
      <svg class="search-result-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      <div class="search-result-text">
        <div class="search-result-name">${{r.merchant || r.txt.substring(0,60)}}</div>
        <div class="search-result-meta">${{r.title}} · ${{r.date}} · ${{r.owner||'—'}} · ${{r.amount ? fmtNis(r.amount) : ''}}</div>
      </div>
    </div>
  `).join('');
  searchResults.querySelectorAll('.search-result').forEach(el => {{
    el.addEventListener('click', () => {{
      const sec = document.getElementById(el.dataset.section);
      if (sec) {{ sec.scrollIntoView({{ behavior: 'smooth' }}); closeSearch(); }}
    }});
  }});
}}
searchInput.addEventListener('input', doSearch);
searchOverlay.addEventListener('click', e => {{ if (e.target === searchOverlay) closeSearch(); }});
searchInput.addEventListener('keydown', e => {{
  const items = searchResults.querySelectorAll('.search-result');
  if (e.key === 'Escape') {{ e.preventDefault(); closeSearch(); }}
  else if (e.key === 'ArrowDown') {{ e.preventDefault(); focusedIdx = Math.min(items.length-1, focusedIdx+1); updateFocused(items); }}
  else if (e.key === 'ArrowUp') {{ e.preventDefault(); focusedIdx = Math.max(0, focusedIdx-1); updateFocused(items); }}
  else if (e.key === 'Enter') {{ e.preventDefault(); items[focusedIdx]?.click(); }}
}});
function updateFocused(items) {{
  items.forEach((el,i) => el.classList.toggle('focused', i===focusedIdx));
  items[focusedIdx]?.scrollIntoView({{ block: 'nearest' }});
}}

// Hotkeys
window.addEventListener('keydown', e => {{
  if ((e.metaKey||e.ctrlKey) && e.key.toLowerCase() === 'k') {{
    e.preventDefault();
    if (searchOverlay.classList.contains('open')) closeSearch(); else openSearch();
  }}
  if (e.key === '/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) {{
    e.preventDefault();
    globalSearchInput.focus();
  }}
}});
globalSearchInput.addEventListener('focus', e => {{
  e.target.blur();  // redirect to palette
  openSearch();
}});
globalSearchInput.addEventListener('input', e => {{
  if (e.target.value) openSearch();
}});

</script>
</body></html>'''
