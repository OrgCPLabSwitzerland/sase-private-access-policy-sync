"""
rule_parser.py

Extracts and normalizes rules from Check Point Management API.

Output format:
[
    {
        "rule-number": 1,
        "name": "Rule 1",
        "source": [{"name": "...", "value": "..."}],
        "destination": [...],
        "service": [...],
        "action": "Accept",
        "enabled": True
    }
]

Notes:
- Objects are resolved using objects-dictionary
- Hosts are resolved to IPs
- "Any" is NOT resolved -> handled later in mapper
"""


# ============================================================
# Rule extraction (handles sections recursively)
# ============================================================

def extract_rules(rulebase):
    """Flatten rulebase into a list of access-rule objects."""
    result = []

    for item in rulebase or []:
        if item.get("type") == "access-rule":
            result.append(item)

        elif item.get("type") == "access-section":
            # recursively extract rules from sections
            result.extend(extract_rules(item.get("rulebase", [])))

    return result


# ============================================================
# Object dictionary (UID -> object)
# ============================================================

def build_obj_dict(obj_list):
    """Build quick lookup table for objects by UID."""
    obj_dict = {}

    for obj in obj_list or []:
        uid = obj.get("uid")
        if uid:
            obj_dict[uid] = obj

    return obj_dict


# ============================================================
# Field normalization
# ============================================================

def normalize_field(field, obj_dict):
    """
    Normalize source/destination/service fields.

    Returns list of:
    [{"name": "...", "value": "..."}]

    Behavior:
    - host -> IP
    - network -> CIDR
    - Any -> "Any"
    - everything else -> UID
    """

    result = []

    if not field:
        return result

    for item in field:

        # ----------------------------------------------------
        # Resolve UID to object
        # ----------------------------------------------------
        if isinstance(item, str):
            uid = item
            obj = obj_dict.get(uid)

        elif isinstance(item, dict):
            uid = item.get("uid")
            obj = obj_dict.get(uid)

        else:
            continue

        # ----------------------------------------------------
        # Object exists
        # ----------------------------------------------------
        if obj:
            obj_type = obj.get("type")

            # ✅ HOST
            if obj_type == "host":
                result.append({
                    "name": obj.get("name"),
                    "value": obj.get("ipv4-address")
                })

            # ✅ NETWORK (THIS FIXES YOUR ISSUE)
            elif obj_type == "network":
                subnet = obj.get("subnet4")
                mask = obj.get("mask-length4")

                if subnet and mask is not None:
                    result.append({
                        "name": obj.get("name"),
                        "value": f"{subnet}/{mask}"
                    })
                else:
                    # fallback if incomplete
                    result.append({
                        "name": obj.get("name"),
                        "value": uid
                    })

            # ✅ ANY
            elif obj_type == "CpmiAnyObject":
                result.append({
                    "name": "Any",
                    "value": "Any"
                })

            # ✅ EVERYTHING ELSE (fqdn, group, etc.)
            else:
                result.append({
                    "name": obj.get("name"),
                    "value": uid
                })

        # ----------------------------------------------------
        # Object NOT found
        # ----------------------------------------------------
        else:
            result.append({
                "name": uid,
                "value": uid
            })

    return result

# ============================================================
# Main parser
# ============================================================

def parse_rules(data):
    """
    Convert full rulebase API response into simplified structure.

    Pipeline:
    raw  -> extract_rules -> normalize_field -> simplified rules
    """

    obj_dict = build_obj_dict(data.get("objects-dictionary", []))
    rules = []

    for r in extract_rules(data.get("rulebase", [])):
        rules.append({
            "rule-number": r.get("rule-number"),
            "name": r.get("name"),

            "source": normalize_field(r.get("source"), obj_dict),
            "destination": normalize_field(r.get("destination"), obj_dict),
            "service": normalize_field(r.get("service"), obj_dict),

            # resolve action UID -> name
            "action": obj_dict.get(r.get("action"), {}).get("name", r.get("action")),
            "enabled": r.get("enabled", True),
        })

    return rules
