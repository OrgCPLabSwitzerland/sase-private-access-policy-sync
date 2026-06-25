"""
SASE Unified IA Policy - Backend Service

This Flask application acts as a bridge between:
- Check Point Management API (SmartConsole policy)
- SASE API (Private Access policy)

Main flow:
    SmartConsole -> Flask API -> Rule Parsing -> Mapping -> SASE API
"""

from flask import Flask, send_from_directory, request
from flask_cors import CORS

import os

# Internal modules
from mgmt_api import login, logout, get_rulebase
from sase_policy_handling import push_policy, get_policy, build_sase_rule
from sase_object_handling import resolve_address
from sase_api_client import sase_request
from rule_parser import parse_rules
from sase_mapper import map_all, is_valid_address

from debug_routes import debug_bp

# ============================================================
# Flask app initialization
# ============================================================

app = Flask(__name__, static_folder=None)
CORS(app)  # Enable CORS for SmartConsole frontend calls

app.register_blueprint(debug_bp)

# ============================================================
# Configuration
# ============================================================

# Layer in SmartConsole to extract rules from
LAYER_NAME = "SASE-Private-Access-Layer"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATIC_DIR = os.path.join(BASE_DIR, "frontend")

# TLS certificates
CERT_PATH = os.path.join(BASE_DIR, "certs", "cert.pem")
KEY_PATH = os.path.join(BASE_DIR, "certs", "key.pem")


# ============================================================
# Frontend (static UI)
# ============================================================

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(STATIC_DIR, path)

# ============================================================
# API: Frontend Worfklow to backend
# ============================================================

@app.route("/install-policy")
def install_policy():
    """
    Main endpoint triggered by SmartConsole UI.

    Flow:
        1. Fetch rulebase from Management API
        2. Parse rules
        3. Map rules to SASE format
        4. Push policy to Harmony SASE
    """
    network_id = request.args.get("network_id")

    sid = None

    try:
        # Login (API key -> SID)
        sid = login()

        # Step 2: Get rulebase
        raw_rulebase = get_rulebase(sid, LAYER_NAME)

        # Step 3: Parse rules
        rules = parse_rules(raw_rulebase)

        # Step 4: Map rules
        mapped_rules = map_all(rules)

        # validate mapped rules BEFORE pushing
        for rule in mapped_rules:
            for section in ["sources", "destinations"]:

                field = rule.get(section)

                # check for invalid marker
                if isinstance(field, dict) and field.get("invalid"):
                    return {
                        "status": "error",
                        "message": f"Invalid object '{field.get('original')}' in rule '{rule.get('name')}'"
                    }, 400

        # Step 5: Push to SASE
        sase_result = push_policy(mapped_rules, network_id=network_id)

        return {
            "status": "success",
            "rules_sent": len(mapped_rules),
            "rules": mapped_rules,
            "sase_result": sase_result,
            "object_map": build_object_name_map(rules)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()

        return {
            "status": "error",
            "message": str(e)
        }, 500

    finally:
        if sid:
            logout(sid)

@app.route("/validate-policy")
def validate_policy():
    """
    Validation endpoint.

    Flow:
        1. Fetch rulebase
        2. Parse rules
        3. Map rules (same as install)
        4. Validate mapped rules (NO push)
    """

    sid = None

    try:
        # Step 1: Login
        sid = login()

        # Step 2: Get rulebase
        raw_rulebase = get_rulebase(sid, LAYER_NAME)

        # Step 3: Parse rules
        rules = parse_rules(raw_rulebase)

        # Step 4: Map rules
        mapped_rules = map_all(rules)

        # Step 5: Validate mapped rules
        errors = []

        for rule in mapped_rules:
            for section in ["sources", "destinations"]:

                field = rule.get(section)

                # mapper already flags invalid objects like FQDN
                if isinstance(field, dict) and field.get("invalid"):
                    errors.append(
                        f"Rule '{rule.get('name')}' invalid {section}: {field.get('original')}"
                    )

        # Step 6: Return result
        if errors:
            return {
                "status": "invalid",
                "errors": errors
            }

        return {
            "status": "valid",
            "rules_checked": len(mapped_rules)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()

        return {
            "status": "error",
            "message": str(e)
        }, 500

    finally:
        if sid:
            logout(sid)

@app.route("/get-networks")
def get_networks():
    try:
        standard = sase_request("GET", "/v2.3/networks/standard")
        enhanced = sase_request("GET", "/v2.3/networks/enhanced")

        result = []

        # Standard networks
        if isinstance(standard, list):
            for net in standard:
                result.append({
                    "name": net.get("name"),
                    "id": net.get("id"),
                    "type": "standard"
                })

        # Enhanced networks
        if isinstance(enhanced, list):
            for net in enhanced:
                result.append({
                    "name": net.get("name"),
                    "id": net.get("id"),
                    "type": "enhanced"
                })

        return {
            "status": "success",
            "networks": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500

# ============================================================
# Helpers
# ============================================================

def build_object_name_map(rules):
    mapping = {}

    for rule in rules:
        for section in ["source", "destination"]:
            for obj in rule.get(section, []):

                value = obj.get("value")
                name = obj.get("name")

                # skip invalid values
                if not value or value == "Any":
                    continue

                try:
                    sase_id = resolve_address(value)

                    if isinstance(sase_id, str):
                        mapping[sase_id] = name

                except Exception:
                    # skip anything not resolvable
                    continue

    return mapping

# ============================================================
# App entry point
# ============================================================

if __name__ == "__main__":
    """
    Run Flask app with TLS enabled.
    Used by systemd service via start.sh.
    """
    app.run(
        host="0.0.0.0",
        port=5000,
        ssl_context=(CERT_PATH, KEY_PATH)
    )
