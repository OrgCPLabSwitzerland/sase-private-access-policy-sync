"""
mgmt_api.py

Low-level Management API client.

Handles:
- API key authentication (via login → SID)
- Rulebase retrieval
"""

from config import config
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================
# Config
# ============================================================

MGMT_URL = config["MGMT_URL"]
API_KEY = config["MGMT_API_KEY"]
VERIFY_TLS = config.get("VERIFY_TLS", False)


# ============================================================
# HTTP session
# ============================================================

session = requests.Session()
session.verify = VERIFY_TLS


# ============================================================
# Authentication
# ============================================================

def login():
    """
    Login using API key → returns SID.
    """

    if not API_KEY:
        raise RuntimeError("MGMT_API_KEY is not configured")

    url = f"{MGMT_URL}/login"

    payload = {
        "api-key": API_KEY
    }

    res = session.post(url, json=payload)

    try:
        data = res.json()
    except Exception:
        raise RuntimeError(f"Login failed (invalid response): {res.text}")

    if "sid" not in data:
        raise RuntimeError(f"Login failed: {data}")

    return data["sid"]


def logout(sid):
    """
    Logout session (best effort).
    """
    if not sid:
        return

    url = f"{MGMT_URL}/logout"

    headers = {
        "X-chkp-sid": sid
    }

    try:
        session.post(url, headers=headers)
    except Exception:
        pass


# ============================================================
# API Calls
# ============================================================

def get_rulebase(sid, layer_name):
    """
    Fetch access rulebase for given layer.
    """

    url = f"{MGMT_URL}/show-access-rulebase"

    headers = {
        "X-chkp-sid": sid
    }

    payload = {
        "name": layer_name,
        "details-level": "full",
        "use-object-dictionary": True
    }

    res = session.post(url, json=payload, headers=headers)

    if res.status_code != 200:
        raise RuntimeError(
            f"MGMT request failed: {res.status_code} - {res.text}"
        )

    try:
        return res.json()
    except Exception:
        raise RuntimeError(f"Invalid JSON response: {res.text}")
