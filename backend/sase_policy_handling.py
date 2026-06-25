# ============================================================
# SASE Policy Handling
# ============================================================

from sase_api_client import sase_request


# ============================================================
# Configuration (temporary fallback for debug only)
# ============================================================

NETWORK_NAME = "CP-LAB-Switzerland"
_network_id_cache = None


# ============================================================
# Network Resolver (hybrid: dynamic + fallback)
# ============================================================

def get_network_id(network_id=None):
    """
    Resolve SASE network ID.

    - If network_id provided -> use it (UI flow)
    - Else -> fallback to NETWORK_NAME (debug)
    """

    if network_id:
        return network_id

    global _network_id_cache

    if _network_id_cache:
        return _network_id_cache

    networks = sase_request("GET", "/v2.3/networks/standard")

    if not isinstance(networks, list) or not networks:
        raise RuntimeError(f"Invalid network response: {networks}")

    for net in networks:
        if net.get("name") == NETWORK_NAME:
            _network_id_cache = net.get("id")
            break

    if not _network_id_cache:
        raise RuntimeError(f"Network not found: {NETWORK_NAME}")

    return _network_id_cache


# ============================================================
# Policy Retrieval
# ============================================================

def get_policy(network_id=None):
    """
    Retrieve SASE policy for a given network.

    - Uses network_id if provided
    - Falls back to default for debug
    """

    target_network_id = get_network_id(network_id)

    return sase_request(
        "GET",
        f"/v2.3/networks/{target_network_id}/policy"
    )


# ============================================================
# Rule Builder
# ============================================================

def build_sase_rule(mapped_rule):
    """
    Convert mapped rule into SASE API format
    """

    name = mapped_rule.get("name") or "unnamed"

    def normalize(field):
        if not field:
            return {}
        if isinstance(field, dict) and field.get("any"):
            return {}
        return field

    rule = {
        "name": name,
        "enabled": bool(mapped_rule.get("enabled", True)),
        "allowed": bool(mapped_rule.get("allowed", True)),
        "sources": normalize(mapped_rule.get("sources")),
        "destinations": normalize(mapped_rule.get("destinations")),
    }

    if mapped_rule.get("services"):
        rule["services"] = mapped_rule["services"]

    return rule


# ============================================================
# Push Policy
# ============================================================

def push_policy(mapped_rules, network_id):
    """
    Push full policy to SASE.

    Requires network_id -> install flow must pass it.
    """

    if not network_id:
        raise RuntimeError("Missing network_id")

    # get policy from SAME network
    current_policy = get_policy(network_id)

    final_rules = []

    for mapped_rule in mapped_rules:
        final_rule = build_sase_rule(mapped_rule)
        final_rules.append(final_rule)

    payload = {
        "id": current_policy["id"],
        "enabled": bool(current_policy.get("enabled", True)),
        "allowed": bool(current_policy.get("allowed", True)),
        "trace": bool(current_policy.get("trace", False)),
        "policyRules": final_rules
    }

    return sase_request(
        "PUT",
        f"/v2.3/networks/{network_id}/policy",
        payload
    )
