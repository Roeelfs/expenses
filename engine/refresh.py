"""Local Moneytor refresh — the ONLY networked code. Preflight (Rule Zero) -> pull
both people (all-or-nothing) -> snapshot -> regex first-pass -> residue queue.
--record writes one decision. See spec sections 3.1, 4.4, 7, 8.
Token is read from os.environ only (never a CLI arg, never logged).
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys
from pathlib import Path

# A real JWT is `eyJ` + a base64url payload — match that shape so prose mentioning
# "eyJ" (e.g. these docs) does not false-positive the preflight.
_JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]{20,}")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import store as _store
import classify_context as _cc
import moneytor as _moneytor
import analyze as _analyze

BASE_URL = "https://app.moneytor.co.il/api/v1"


class PartialPullError(Exception): pass
class TruncationError(Exception): pass


def preflight(repo_root=ROOT):
    """Rule Zero hard gate. Returns (ok, message); abort the refresh if not ok."""
    repo_root = Path(repo_root)
    try:
        r = subprocess.run(["git", "check-ignore", ".env"], cwd=str(repo_root),
                           capture_output=True, text=True)
    except FileNotFoundError:
        return (False, "git not available for preflight")
    if r.returncode != 0:
        return (False, ".env is NOT gitignored — refusing to run (Rule Zero). Add /.env to .gitignore.")
    try:
        tracked = subprocess.run(["git", "ls-files"], cwd=str(repo_root),
                                 capture_output=True, text=True)
    except FileNotFoundError:
        return (False, "git not available for preflight")
    for f in tracked.stdout.split():
        if "example" in f:
            continue
        p = repo_root / f
        if not p.is_file():
            continue
        try:
            if _JWT_RE.search(p.read_text(encoding="utf-8", errors="ignore")):
                return (False, f"possible JWT/token material in tracked file: {f}")
        except Exception:
            continue
    return (True, "ok")


def check_truncation(rows, limit):
    if len(rows) >= limit:
        raise TruncationError(
            f"pull returned {len(rows)} rows == limit {limit}; more rows may exist — refusing to snapshot a truncated set")


def promote(out, snaps, meta):
    """All-or-nothing: if any person's data is None, raise and write NOTHING."""
    out = Path(out)
    if any(v is None for v in snaps.values()):
        failed = [k for k, v in snaps.items() if v is None]
        raise PartialPullError(f"partial pull (failed: {failed}); keeping previous snapshot generation")
    snap_dir = out / "snapshot"
    snap_dir.mkdir(parents=True, exist_ok=True)
    for person, data in snaps.items():
        _store.save(snap_dir / f"{person}.json", data)
    _store.save(snap_dir / "meta.json", meta)


def pull(frm=None, to=None, limit=2000):
    """Fetch both people from Moneytor (all-or-nothing) into snapshots."""
    C = _analyze.C
    frm = frm or C.PERIOD_START.isoformat()
    to = to or C.PERIOD_END.isoformat()
    snaps, counts = {}, {}
    for person in C.PEOPLE:
        src = person.sources[0] if person.sources else None
        token_env = getattr(src, "token_env", "") if src else ""
        token = os.environ.get(token_env) if token_env else None
        if not token:
            print(f"ERROR: env var {token_env!r} not set for {person.id}", file=sys.stderr)
            snaps[person.id] = None
            continue
        try:
            rows = _moneytor.fetch_transactions(BASE_URL, token, frm, to, limit)
            check_truncation(rows, limit)
            snaps[person.id] = {"ok": True, "transactions": rows}
            counts[person.id] = len(rows)
        except (_moneytor.MoneytorError, TruncationError) as e:
            print(f"ERROR pulling {person.id}: {e}", file=sys.stderr)
            snaps[person.id] = None
    promote(_analyze.OUTDIR, snaps, {"period": [frm, to], "limit": limit, "fetched_count": counts})


def first_pass_residue():
    """Regex first-pass over the latest snapshot; persist rule hits + write the residue queue."""
    txs = _analyze.load_all()
    store_path = _analyze.OUTDIR / "decisions.json"
    decisions = _store.load(store_path)
    queue = []
    _analyze.classify_all(txs, decisions, queue, rubric_hash=_cc.rubric_hash())
    _store.save(store_path, decisions)
    residue = [_cc.build_input(t, []) for t in queue]
    _store.save(_analyze.OUTDIR / "residue.json", {"items": residue})
    print(f"{len(residue)} transactions need LLM reasoning", file=sys.stderr)
    return queue


def _find_tx(owner, txid):
    snap = json.loads((_analyze.OUTDIR / "snapshot" / f"{owner}.json").read_text("utf-8"))
    for r in snap.get("transactions", []):
        if r["id"] == txid:
            return _analyze.map_moneytor(r, owner)
    return None


def record(json_str):
    """Write ONE decision. Reconstructs the full tx from the snapshot so src_hash matches the build."""
    d = json.loads(json_str)
    if d.get("status") not in _cc.STATUS_VALUES:
        raise ValueError(f"invalid status: {d.get('status')!r}")
    tx = _find_tx(d["owner"], d["id"])
    if tx is None:
        raise ValueError(f"tx {d['owner']}:{d['id']} not in current snapshot")
    store_path = _analyze.OUTDIR / "decisions.json"
    decisions = _store.load(store_path)
    _store.put_decision(decisions, tx, status=d["status"], tag=d.get("tag", ""),
                        reason=d.get("reason", ""), decided_by=d.get("decided_by", "llm"),
                        rubric_hash=_cc.rubric_hash(), extra=d.get("extra"))
    _store.save(store_path, decisions)
    print(f"recorded {d['owner']}:{d['id']} -> {d['status']}", file=sys.stderr)


def _main(argv=None):
    ap = argparse.ArgumentParser(description="Moneytor local refresh")
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--pull", action="store_true")
    ap.add_argument("--record", metavar="JSON")
    ap.add_argument("--from", dest="frm")
    ap.add_argument("--to", dest="to")
    args = ap.parse_args(argv)
    if args.preflight:
        ok, msg = preflight()
        print(msg, file=sys.stderr)
        sys.exit(0 if ok else 1)
    if args.pull:
        ok, msg = preflight()
        if not ok:
            print(f"PREFLIGHT FAILED: {msg}", file=sys.stderr)
            sys.exit(1)
        pull(args.frm, args.to)
        first_pass_residue()
        return
    if args.record:
        record(args.record)
        return
    ap.print_help()


if __name__ == "__main__":
    _main()
