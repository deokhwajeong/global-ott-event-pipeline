"""Pseudonymous identifiers only (ADR-002 rule 2).

The client sends a rotating, platform-issued device ID. Serial numbers, account
IDs, and network identifiers must never reach storage, so ingest refuses any
envelope that carries them.
"""

from __future__ import annotations

import re
from typing import Any

# Platform-issued pseudonymous device ID: "pd_" followed by 128 random bits in hex.
PSEUDONYMOUS_DEVICE_ID = re.compile(r"^pd_[0-9a-f]{32}$")

FORBIDDEN_IDENTIFIER_KEYS = frozenset(
    {
        "serial",
        "serial_number",
        "account_id",
        "user_id",
        "email",
        "ip",
        "ip_address",
        "mac",
        "mac_address",
        "advertising_id",
    }
)


def is_pseudonymous_device_id(value: str) -> bool:
    return bool(PSEUDONYMOUS_DEVICE_ID.fullmatch(value))


def is_forbidden_key(key: str) -> bool:
    """True for a forbidden key, including the last segment of a dotted key."""
    return key.lower().rsplit(".", 1)[-1] in FORBIDDEN_IDENTIFIER_KEYS


def find_forbidden_identifier(value: Any, *, skip_keys: frozenset[str] = frozenset()) -> bool:
    """Recursively look for forbidden identifier keys, skipping the named subtrees."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key in skip_keys:
                continue
            if isinstance(key, str) and is_forbidden_key(key):
                return True
            if find_forbidden_identifier(child, skip_keys=skip_keys):
                return True
    elif isinstance(value, list):
        return any(find_forbidden_identifier(item, skip_keys=skip_keys) for item in value)
    return False
