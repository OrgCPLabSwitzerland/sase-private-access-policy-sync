"""
sase_objects.py

Handles:
- Address lookup
- Address creation
- Ensures we always return SASE object IDs
"""

from sase_api_client import sase_request

_address_cache = None


def load_addresses():
    """Load all SASE address objects (cached)."""
    global _address_cache

    if _address_cache is not None:
        return _address_cache

    data = sase_request("GET", "/v2.3/objects/addresses")

    # API sometimes wraps result in "data"
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    _address_cache = data or []

    return _address_cache


def resolve_address(value, display_name=None):
    """
    Resolve IP/CIDR SASE object ID.
    - Reuse if exists
    - Create if missing
    """
    import ipaddress

    addresses = load_addresses()

    clean = str(value).strip()

    # Determine IP type
    if "/" in clean:
        ipaddress.ip_network(clean, strict=False)
        value_type = "cidr"
    else:
        ipaddress.ip_address(clean)
        value_type = "ip"

    val = [clean]

    #  Try reuse existing object
    for obj in addresses:
        if obj.get("value") == val and obj.get("valueType") == value_type:
            return obj["id"]

    #  Create new object
    name = f"quantum_{display_name or clean}"

    payload = {
        "name": name,
        "value": val,
        "valueType": value_type
    }

    new_obj = sase_request(
        "POST",
        "/v2.3/objects/addresses",
        payload
    )

    # IMPORTANT: update local cache immediately
    addresses.append(new_obj)

    return new_obj["id"]
