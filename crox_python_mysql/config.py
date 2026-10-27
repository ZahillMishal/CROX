"""
Configuration Module for CROX Python + MySQL Version
Manages MySQL connection parameters and user overrides.
"""

import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'db_config.json')

DEFAULT_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "crox_db",
    "prefer_mysql": True
}

def load_db_config():
    """Load configuration from JSON or return defaults."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(saved)
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_db_config(config_dict):
    """Save database configuration to JSON file."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
