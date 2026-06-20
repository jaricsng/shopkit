"""Structured security audit logging.

Emits one JSON line per security-relevant event to a dedicated `shopkit.audit`
logger — the trail an auditor / SIEM wants (SOC 2 CC7.2, ISO A.8.15). Ship these
to a tamper-evident store with a retention period (see the lab's
governance/data-governance.md). Record an actor identifier and outcome; never
log secrets, tokens, or request bodies.
"""

import json
import logging
from datetime import UTC, datetime

_logger = logging.getLogger("shopkit.audit")


def audit(event: str, *, actor: str | None = None, outcome: str = "success", **fields) -> None:
    """Emit one structured audit event."""
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "event": event,
        "actor": actor,
        "outcome": outcome,
        **fields,
    }
    _logger.info(json.dumps(record, separators=(",", ":")))
