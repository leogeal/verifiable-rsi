"""Tamper-evident audit log for the self-improvement run.

Each promotion or stop decision is recorded with a hash that chains the previous
record's hash, so the lineage forms a verifiable chain: altering any past record
invalidates every hash after it. :func:`verify_chain` re-walks a list of record
dicts and confirms the chain is intact -- the audit trail can prove it was not
edited after the fact.
"""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Dict, List


def chain_hash(prev_hash: str, payload: Dict[str, Any]) -> str:
    """Hash ``payload`` together with the previous record's hash."""

    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = sha256()
    digest.update(prev_hash.encode("utf-8"))
    digest.update(b"\0")
    digest.update(body.encode("utf-8"))
    return digest.hexdigest()[:32]


def verify_chain(records: List[Dict[str, Any]]) -> bool:
    """Return True iff the ``record_hash`` chain in ``records`` is intact."""

    prev = ""
    for record in records:
        payload = {k: v for k, v in record.items() if k not in ("record_hash", "prev_hash")}
        expected = chain_hash(prev, payload)
        if record.get("prev_hash") != prev or record.get("record_hash") != expected:
            return False
        prev = expected
    return True
