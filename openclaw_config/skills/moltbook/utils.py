"""
Moltbook utilities for credential management and state tracking
"""

import os
import json

CREDENTIALS_FILE = os.path.expanduser("~/.config/moltbook/credentials.json")
STATE_FILE = os.path.expanduser("~/.config/moltbook/heartbeat_state.json")


def load_credentials():
    """Load Moltbook credentials"""
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


def save_credentials(api_key, agent_name):
    """Save Moltbook credentials"""
    os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump({
            "api_key": api_key,
            "agent_name": agent_name
        }, f, indent=2)


def load_state():
    """Load heartbeat state"""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_state(state):
    """Save heartbeat state"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
