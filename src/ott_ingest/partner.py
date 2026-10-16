"""Partner extension namespace (ADR-003).

Partners may attach optional fields under ``partner.<partner_id>.<field>``.
Fields must be declared in the registry (reviewed during certification), must
belong to the partner that owns the app, must be scalars, and must fit a
small budget. Anything that fails is stripped and counted.

The one rule that matters most: extension handling can never block ingest.
The core event is stored whatever happens here.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from ott_ingest.privacy import is_forbidden_key

EXT_KEY = re.compile(r"^partner\.([a-z0-9_]{2,32})\.([a-z0-9_]{1,64}(?:\.[a-z0-9_]{1,64})*)$")
MAX_EXT_KEYS = 32
MAX_EXT_BYTES = 2048
SCALAR_TYPES: dict[str, tuple[type, ...]] = {
    "str": (str,),
    "int": (int,),
    "float": (int, float),
    "bool": (bool,),
}


@dataclass
class PartnerRegistry:
    """Which partner owns which app, and which extension fields each partner declared."""

    app_owner: dict[str, str] = field(default_factory=dict)  # app_id -> partner_id
    declared: dict[str, dict[str, str]] = field(default_factory=dict)  # partner -> field -> type

    def register(self, partner_id: str, app_ids: list[str], fields: dict[str, str]) -> None:
        for app_id in app_ids:
            self.app_owner[app_id] = partner_id
        self.declared[partner_id] = dict(fields)


def _type_ok(value: Any, type_name: str) -> bool:
    allowed = SCALAR_TYPES.get(type_name)
    if allowed is None:
        return False
    if isinstance(value, bool) and type_name != "bool":
        return False
    return isinstance(value, allowed)


def _sanitize(raw: Any, app_id: str, registry: PartnerRegistry) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(raw, dict):
        return {}, ["ext_not_object"]
    if len(raw) > MAX_EXT_KEYS or len(json.dumps(raw, default=str)) > MAX_EXT_BYTES:
        return {}, ["ext_over_budget"]

    kept: dict[str, Any] = {}
    stripped: list[str] = []
    owner = registry.app_owner.get(app_id)
    for key, value in raw.items():
        match = EXT_KEY.fullmatch(key) if isinstance(key, str) else None
        if match is None:
            stripped.append("ext_bad_key")
            continue
        partner_id, field_name = match.groups()
        if is_forbidden_key(key):
            stripped.append("ext_forbidden_identifier")
        elif partner_id != owner:
            stripped.append("ext_wrong_partner")
        elif field_name not in registry.declared.get(partner_id, {}):
            stripped.append("ext_undeclared")
        elif not _type_ok(value, registry.declared[partner_id][field_name]):
            stripped.append("ext_bad_type")
        else:
            kept[key] = value
    return kept, stripped


def sanitize_extensions(
    raw: Any, app_id: str, registry: PartnerRegistry
) -> tuple[dict[str, Any], list[str]]:
    """Return (kept fields, reasons for each stripped field). Never raises."""
    if raw is None:
        return {}, []
    try:
        return _sanitize(raw, app_id, registry)
    except Exception:  # deliberate: no extension problem may block the core event
        return {}, ["ext_error"]
