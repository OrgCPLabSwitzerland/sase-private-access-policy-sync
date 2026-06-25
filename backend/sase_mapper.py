"""
sase_mapper.py

Maps parsed SmartConsole rules into an internal SASE rule model.

Input (from rule_parser):
{
    "name": "Rule 1",
    "enabled": true,
    "action": "Accept",
    "source": [{ "name": "IoTServer", "value": "192.168.1.10" }],
    "destination": [{ "name": "Any", "value": "97ae..." }],
    "service": [...]
}

Output (internal model):
{
    "name": "...",
    "allowed": True/False,
    "sources": {"addresses": [...]} OR {"any": True},
    "destinations": {...}
}

Notes:
- "Any" (Check Point UID) is NOT resolved.
- "Any" is kept as {"any": True}.
- Conversion to SASE format ({} or CIDR) happens later in policy layer.
"""

import ipaddress
from sase_object_handling import resolve_address


# ============================================================
# Constants
# ============================================================

ANY_UID = "97aeb369-9aea-11d5-bd16-0090272ccb30"


# ============================================================
# Helpers
# ============================================================

def normalize_list(value):
    """Ensure value is always a list."""
    return value if isinstance(value, list) else ([value] if value else [])


def is_any_object(value):
    """Detect Check Point 'Any' object."""
    if isinstance(value, dict):
        return (
            value.get("value") == ANY_UID or
            str(value.get("name", "")).lower() == "any"
        )
    return str(value) == ANY_UID or str(value).lower() == "any"


def is_valid_address(value):
    """Validate IPv4/IPv6 or CIDR."""
    if not value:
        return False

    value = str(value).strip()

    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        pass

    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except ValueError:
        return False


# ============================================================
# Address Mapping
# ============================================================

def map_address_list(values):
    """
    Map source/destination objects.

    Returns:
    - {"any": True}
    - {"addresses": [ids]}
    - {}
    """

    addresses = []
    saw_any = False

    for item in normalize_list(values):

        # Handle ANY
        if is_any_object(item):
            saw_any = True
            continue

        # Extract fields
        if isinstance(item, dict):
            name = item.get("name")
            value = item.get("value")
            obj_type = item.get("type")

            # handle network objects -> convert to CIDR
            if obj_type == "network":
                subnet = item.get("subnet4")
                mask = item.get("mask-length4")

                if subnet and mask is not None:
                    value = f"{subnet}/{mask}"

        else:
            name = value = item

        # Skip non-address objects
        if not is_valid_address(value):
            return {
            "invalid": True,
            "original": value
        }

        # Resolve to SASE object ID
        obj_id = resolve_address(value, display_name=name)
        if isinstance(obj_id, dict) and obj_id.get("invalid"):
            return obj_id
        addresses.append(obj_id)

    if saw_any:
        return {"any": True}

    return {"addresses": addresses} if addresses else {}


def map_sources(values):
    return map_address_list(values)


def map_destinations(values):
    return map_address_list(values)


# ============================================================
# Services
# ============================================================

def map_services(values):
    """
    Map services.

    - Any -> None (omit field)
    - Specific -> map to SASE naming
    """

    services = []
    SASE_SUFFIX = "_cp-lab-switzerland"

    for item in normalize_list(values):

        if is_any_object(item):
            return None   # ✅ IMPORTANT

        if isinstance(item, dict):
            name = item.get("name") or item.get("value")
        else:
            name = item

        if name:
            name = str(name).lower()
            services.append(f"{name}{SASE_SUFFIX}")

    return services or None

# ============================================================
# Action Mapping
# ============================================================

def map_allowed(action):
    """Map Check Point action -> boolean."""
    value = str(action or "").lower()

    if value in ["accept", "allow"]:
        return True

    if value in ["drop", "deny", "reject", "block"]:
        return False

    raise RuntimeError(f"Unsupported action '{action}'")


# ============================================================
# Rule Mapping
# ============================================================

def map_rule_to_sase(rule):
    """Convert one parsed rule into internal SASE rule format."""

    name = rule.get("name") or f"rule-{rule.get('rule-number', 'unnamed')}"

    sources = map_sources(rule.get("source"))
    destinations = map_destinations(rule.get("destination"))
    services = map_services(rule.get("service"))

    sase_rule = {
        "name": name,
        "enabled": bool(rule.get("enabled", True)),
        "allowed": map_allowed(rule.get("action")),
        "sources": sources,
        "destinations": destinations
    }

    if services:
        sase_rule["services"] = services

    return sase_rule


def map_all(rules):
    """Map all rules."""

    mapped = []

    for rule in rules:
        try:
            result = map_rule_to_sase(rule)
            if result:
                mapped.append(result)
        except Exception as e:
            print(f"[MAPPER ERROR] rule={rule.get('name')} error={e}", flush=True)
    return mapped
