"""Deterministic helpers shared across generator modules.

Synthetic-data plan section 11 forbids ``uuid4`` and ``random``-based IDs.
Every primary key in this corpus is derived from the source card structure.
Timestamps are derived from the card's declared dates plus a deterministic
offset.

The fixed seed string lives in ``ops/seed/constants.py``; helpers here mix it
into SHA-256 inputs so unrelated IDs cannot collide.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, time, timedelta, timezone

from ops.seed.constants import DETERMINISTIC_SEED

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Lowercase + replace non [a-z0-9] runs with single dashes."""

    if not value:
        return "unknown"
    lowered = value.lower()
    cleaned = _SLUG_RE.sub("-", lowered).strip("-")
    return cleaned or "unknown"


def derive_id(*parts: str) -> str:
    """Return a deterministic 16-hex prefix derived from the seed + parts."""

    payload = "|".join((DETERMINISTIC_SEED, *parts)).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return digest[:16]


def derive_uuid_like(*parts: str) -> str:
    """Return a UUID-shaped (8-4-4-4-12) deterministic identifier."""

    payload = "|".join((DETERMINISTIC_SEED, "uuid", *parts)).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return f"{digest[0:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


def derive_timestamp(anchor: date | datetime, offset_minutes: int = 0) -> datetime:
    """Anchor a timestamp on the given date deterministically.

    The base time is 09:00 UTC; ``offset_minutes`` shifts forward in
    deterministic increments so every event timestamp on a given card date is
    distinct and ordered.
    """

    if isinstance(anchor, datetime):
        base = anchor
        if base.tzinfo is None:
            base = base.replace(tzinfo=timezone.utc)
    else:
        base = datetime.combine(anchor, time(9, 0, tzinfo=timezone.utc))
    return base + timedelta(minutes=offset_minutes)


def iso_z(value: datetime) -> str:
    """Render a ``datetime`` as ISO-8601 with explicit ``Z`` suffix."""

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    iso = value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return iso


def stable_sort_key(value: str) -> str:
    """Return ``value`` with consistent collation for deterministic sorting."""

    return value


__all__ = [
    "slugify",
    "derive_id",
    "derive_uuid_like",
    "derive_timestamp",
    "iso_z",
    "stable_sort_key",
]
