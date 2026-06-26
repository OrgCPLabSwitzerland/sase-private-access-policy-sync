"""
sase_api_client.py

Low-level SASE API client.
Handles:
- Authentication (token)
- Generic REST requests
"""

from config import config
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SASE_API_KEY = config["SASE_API_KEY"]
AUTH_URL = config["SASE_AUTH_URL"]
BASE_URL = config["SASE_BASE_URL"]

_token_cache = None


def get_token(force_refresh=False):
    """Get API token (cached). Use force_refresh=True to re-authenticate."""
    global _token_cache

    if _token_cache and not force_refresh:
        return _token_cache

    r = requests.post(
        AUTH_URL,
        json={
            "grantType": "api_key",
            "apiKey": SASE_API_KEY
        },
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        verify=False
    )

    if not r.ok:
        raise RuntimeError(f"Auth failed: {r.text}")

    data = r.json()

    token = data.get("data", {}).get("accessToken") or data.get("accessToken")

    if not token:
        raise RuntimeError(f"No token in response: {data}")

    _token_cache = token
    return token


def sase_request(method, path, payload=None):
    """Generic SASE API wrapper. Retries once on 401 (token expired)."""
    if not path.startswith("/"):
        path = "/" + path

    token = get_token()

    r = requests.request(
        method,
        BASE_URL + path,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        json=payload,
        verify=False
    )

    # Token expired — refresh and retry once
    if r.status_code == 401:
        token = get_token(force_refresh=True)
        r = requests.request(
            method,
            BASE_URL + path,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json=payload,
            verify=False
        )

    if not r.ok:
        raise RuntimeError(
            f"SASE request failed: {method} {path} "
            f"({r.status_code}): {r.text}"
        )

    return r.json() if r.text else {}
