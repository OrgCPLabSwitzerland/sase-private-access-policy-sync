import json
import os

# Project root
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# JSON config path
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise RuntimeError(f"Config file not found: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


# Load once
config = load_config()
