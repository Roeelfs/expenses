---
name: refresh
description: Pull fresh transactions from Moneytor, reason over the ambiguous residue once, and rebuild the expense dashboard. Use when the user says "refresh expenses", "pull new transactions", or wants the report updated with the latest data.
disable-model-invocation: true
argument-hint: "[--from YYYY-MM-DD] [--to YYYY-MM-DD] [--no-llm] [--retune] [--publish]"
allowed-tools: Bash(python3 engine/*.py *), Read, Edit
---

# /refresh — pull, reason once, rebuild

This is a side-effecting, manual operation. The deterministic steps are Python;
the only non-deterministic step (reasoning over the ambiguous residue) is you,
the harness. Each transaction is reasoned ONCE and persisted by `owner:id` in
`output/decisions.json`; rebuilds and incremental refreshes reuse it.

## Runbook

1. **Preflight (Rule Zero).** Run `python3 engine/refresh.py --preflight`. If it
   exits non-zero, STOP and fix `.gitignore`/tracked-token issues before anything
   else — never proceed past a failed preflight.

2. **Pull (the only networked step).** Run `python3 engine/refresh.py --pull`
   (optionally `--from`/`--to`). This reads each person's Moneytor JWT from the
   env vars named in `config.py` (`token_env`), pulls BOTH people all-or-nothing
   into `output/snapshot/<person>.json`, runs the regex first-pass, and writes the
   ambiguous residue to `output/residue.json`. The two tokens live ONLY in the
   gitignored `.env` — never echo, paste, or commit them.

3. **Reason over the residue (you).** Read `output/residue.json`. For each item,
   decide `{status, tag, reason, category}` using the rubric in
   `engine/classify_context.py` (the `RUBRIC`), the name tokens + amount constants
   from `build_context`, and the `siblings` examples. Record EACH verdict with:
   `python3 engine/refresh.py --record '{"owner":"person_a","id":"<id>","status":"<status>","tag":"<tag>","reason":"<why>","decided_by":"llm"}'`
   For a large residue, fork the `classification-reasoner` subagent to keep your
   context lean. If a transaction is genuinely undecidable, record it with
   `"status":"flag"` so it is surfaced, not silently dropped.

4. **Build.** Run `python3 engine/analyze.py` → writes `output/report.html` from
   the snapshot joined to the store. This step is offline, free, and deterministic.

5. **Publish (optional, `--publish`).** [Phase 2 — the Supabase viewer; not built
   in PR1.]

## Notes
- A normal build never calls Moneytor and never re-reasons — it reuses the store.
- Re-reasoning only happens for NEW transactions or when a transaction's source
  fields change (the store's `src_hash` drift rule) or the rubric changes.
