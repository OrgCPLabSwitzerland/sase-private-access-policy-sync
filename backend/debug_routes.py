"""
debug_routes.py

Debug endpoints for the full pipeline:

MGMT -> parser -> mapper -> payload -> SASE -> objects

Each endpoint represents one stage of the flow.
"""

from flask import Blueprint

from mgmt_api import login, logout, get_rulebase
from rule_parser import parse_rules
from sase_mapper import map_all
from sase_policy_handling import get_policy, build_sase_rule
from sase_api_client import sase_request


debug_bp = Blueprint("debug", __name__)

LAYER_NAME = "SASE-Private-Access-Layer"


# ============================================================
# Helper (removes duplication)
# ============================================================

def load_parsed_rules():
    sid = login()
    try:
        raw = get_rulebase(sid, LAYER_NAME)
        return parse_rules(raw)
    finally:
        logout(sid)


# ============================================================
# 1. RAW RULEBASE (MGMT API output)
# ============================================================

@debug_bp.route("/debug/raw-rulebase")
def debug_raw_rulebase():
    sid = login()
    try:
        return get_rulebase(sid, LAYER_NAME)
    finally:
        logout(sid)


# ============================================================
# 2. PARSED RULES (after parser)
# ============================================================

@debug_bp.route("/debug/parsed-rules")
def debug_parsed_rules():
    parsed = load_parsed_rules()

    return {
        "count": len(parsed),
        "rules": parsed
    }


# ============================================================
# 3. MAPPED RULES (after mapper)
# ============================================================

@debug_bp.route("/debug/mapped-rules")
def debug_mapped_rules():
    parsed = load_parsed_rules()
    mapped = map_all(parsed)

    return {
        "count": len(mapped),
        "rules": mapped
    }


# ============================================================
# 4. FINAL PAYLOAD (sent to SASE)
# ============================================================

@debug_bp.route("/debug/final-payload")
def debug_final_payload():
    sid = login()

    try:
        # ----------------------------------------------------
        # MGMT: Get and process rules
        # ----------------------------------------------------
        raw = get_rulebase(sid, LAYER_NAME)
        parsed = parse_rules(raw)
        mapped = map_all(parsed)

        # ----------------------------------------------------
        # SASE: Current policy
        # ----------------------------------------------------
        current_policy = get_policy()

        # ----------------------------------------------------
        # Build final payload
        # ----------------------------------------------------
        final_rules = []
        for rule in mapped:
            built = build_sase_rule(rule)
            if built:
                final_rules.append(built)

        return {
            "id": current_policy["id"],
            "enabled": current_policy.get("enabled", True),
            "allowed": current_policy.get("allowed", True),
            "trace": current_policy.get("trace", False),
            "policyRules": final_rules
        }

    except Exception as e:
        import traceback
        traceback.print_exc()

        return {
            "status": "error",
            "message": str(e)
        }, 500

    finally:
        logout(sid)

# ============================================================
# 5. CURRENT SASE POLICY
# ============================================================

@debug_bp.route("/debug/sase-policy")
def debug_sase_policy():
    return get_policy()


# ============================================================
# 6. SASE OBJECT INVENTORY
# ============================================================

@debug_bp.route("/debug/sase-objects")
def debug_sase_objects():
    data = sase_request("GET", "/v2.3/objects/addresses")

    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    return [
        {
            "id": obj["id"],
            "name": obj["name"],
            "value": obj["value"],
            "type": obj["valueType"]
        }
        for obj in data
    ]

# ============================================================
# All in one debug pipeline
# ============================================================

@debug_bp.route("/debug/pipeline")
def debug_pipeline():
    sid = login()

    try:
        raw = get_rulebase(sid, LAYER_NAME)
        parsed = parse_rules(raw)
        mapped = map_all(parsed)

        current_policy = get_policy()

        final_rules = []
        for rule in mapped:
            built = build_sase_rule(rule)
            if built:
                final_rules.append(built)

        return {
            "raw_count": len(raw.get("rulebase", [])),
            "parsed_count": len(parsed),
            "mapped_count": len(mapped),
            "final_count": len(final_rules),
            "sase_count": len(current_policy.get("policyRules", []))
        }

    finally:
        logout(sid)

@debug_bp.route("/debug/pipeline-full")
def debug_pipeline_full():
    sid = login()

    try:
        # ----------------------------------------------------
        # MGMT: full pipeline
        # ----------------------------------------------------
        raw = get_rulebase(sid, LAYER_NAME)
        parsed = parse_rules(raw)
        mapped = map_all(parsed)

        # ----------------------------------------------------
        # Build final payload
        # ----------------------------------------------------
        final_rules = []
        for rule in mapped:
            built = build_sase_rule(rule)
            if built:
                final_rules.append(built)

        # ----------------------------------------------------
        # SASE: state
        # ----------------------------------------------------
        sase_policy = get_policy()
        sase_objects = sase_request("GET", "/v2.3/objects/addresses")

        if isinstance(sase_objects, dict) and "data" in sase_objects:
            sase_objects = sase_objects["data"]

        # ----------------------------------------------------
        # Return EVERYTHING
        # ----------------------------------------------------
        return {
            # -------------------------
            # SUMMARY (fast view)
            # -------------------------
            "summary": {
                "raw_count": len(raw.get("rulebase", [])),
                "parsed_count": len(parsed),
                "mapped_count": len(mapped),
                "final_count": len(final_rules),
                "sase_count": len(sase_policy.get("policyRules", []))
            },

            # -------------------------
            # FULL DATA
            # -------------------------
            "raw_rulebase": raw,
            "parsed_rules": parsed,
            "mapped_rules": mapped,
            "final_payload": {
                "id": sase_policy["id"],
                "enabled": sase_policy.get("enabled", True),
                "allowed": sase_policy.get("allowed", True),
                "trace": sase_policy.get("trace", False),
                "policyRules": final_rules
            },
            "sase_policy": sase_policy,
            "sase_objects": sase_objects
        }

    finally:
        logout(sid)
