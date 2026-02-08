#!/usr/bin/env python3
"""
Soul Reminder Script

This script can be used to periodically remind an agent of its SOUL.md personality.

Usage:
    python3 soul-reminder.py

The script:
1. Reads SOUL.md from the workspace
2. Extracts key personality traits
3. Creates a reminder file that can be checked by the agent

For automatic execution, add to crontab:
    * * * * * cd /path/to/workspace && python3 scripts/soul-reminder.py
"""

import json
import os
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
# SOUL.md is typically in the workspace or project root
SOUL_FILE = Path(__file__).parent.parent / "SOUL.md"
REMINDER_FILE = WORKSPACE / "soul_reminder.json"


def extract_key_traits(soul_content: str) -> dict:
    """Extract key personality traits from SOUL.md."""
    traits = {
        "core_truths": [],
        "boundaries": [],
        "vibe": [],
    }

    lines = soul_content.split("\n")
    current_section = None

    for line in lines:
        line = line.strip()
        if line.startswith("##"):
            current_section = line.lower().replace("## ", "").strip()
        elif line.startswith("**") and line.endswith("**"):
            trait = line.strip("*").strip()
            if current_section == "core truths":
                traits["core_truths"].append(trait)
            elif current_section == "boundaries":
                traits["boundaries"].append(trait)
            elif current_section == "vibe":
                traits["vibe"].append(trait)

    return traits


def main():
    """Main function to create soul reminder."""
    # Read SOUL.md
    if not SOUL_FILE.exists():
        print(f"SOUL.md not found at {SOUL_FILE}")
        return

    soul_content = SOUL_FILE.read_text()

    # Extract key traits
    traits = extract_key_traits(soul_content)

    # Create reminder
    reminder = {
        "last_updated": str(Path.cwd()),
        "personality_summary": {
            "core_truths": traits["core_truths"][:3] if traits["core_truths"] else [],
            "boundaries": traits["boundaries"][:3] if traits["boundaries"] else [],
            "vibe": " ".join(traits["vibe"]) if traits["vibe"] else "",
        },
        "key_points": [
            "Be genuinely helpful, not performatively helpful",
            "Have opinions - you're allowed to disagree and prefer things",
            "Be resourceful before asking - figure it out first",
            "Earn trust through competence",
            "Remember you're a guest - respect privacy",
            "Private things stay private",
            "Don't be a corporate drone or sycophant",
        ],
    }

    # Write reminder
    REMINDER_FILE.write_text(json.dumps(reminder, indent=2, ensure_ascii=False))
    print(f"Soul reminder updated at {REMINDER_FILE}")


if __name__ == "__main__":
    main()
