"""Persisted classification store (decisions.json). Source of truth, keyed owner:id.

Atomic writes only; one freeze/drift rule; src_hash over RAW source fields only.
See spec section 4.3.
"""
from __future__ import annotations
import json, os, hashlib, tempfile
from datetime import date
from pathlib import Path

_HASH_FIELDS = ("id", "owner", "tx_date", "amount", "currency", "merchant",
                "notes", "moneytor_category", "type", "card", "bank_kind")


def key(tx: dict) -> str:
    return f"{tx['owner']}:{tx['id']}"


def src_hash(tx: dict) -> str:
    sub = {k: tx.get(k, "") for k in _HASH_FIELDS}
    blob = json.dumps(sub, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load(path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def save(path, store: dict) -> None:
    """Atomic: write a same-dir temp file, fsync, os.replace. Never write in place."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=p.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=0)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
        dirfd = os.open(str(p.parent), os.O_RDONLY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def put_decision(store: dict, tx: dict, *, status, tag, reason, decided_by,
                 rubric_hash, extra=None) -> None:
    rec = {
        "status": status, "tag": tag, "reason": reason, "decided_by": decided_by,
        "decided_at": date.today().isoformat(),
        "src_hash": src_hash(tx), "rubric_hash": rubric_hash,
        "extra": dict(extra or {}),
    }
    store[key(tx)] = rec


def lookup(store: dict, tx: dict, *, rubric_hash, retune=False):
    """Return the stored decision if valid, else None (caller re-queues).

    Valid iff src_hash AND rubric_hash match. On drift, the prior decision is
    retained in extra.prior and None is returned. rule records re-run (None) under
    retune; llm/human are never re-run by retune.
    """
    rec = store.get(key(tx))
    if rec is None:
        return None
    drift = rec["src_hash"] != src_hash(tx) or rec.get("rubric_hash") != rubric_hash
    if drift:
        rec.setdefault("extra", {}).setdefault("prior", {
            "status": rec["status"], "tag": rec["tag"], "reason": rec["reason"],
            "decided_by": rec["decided_by"],
        })
        return None
    if rec["decided_by"] == "rule" and retune:
        return None
    return rec
