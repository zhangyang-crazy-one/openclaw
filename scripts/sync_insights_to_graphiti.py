#!/usr/bin/env python3
"""Sync memory/insights/*.json files to Graphiti knowledge graph.

Reuses API pattern from sync_memory_to_graphiti.py.
"""
import json
import sys
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timezone

GRAPHITI_API = "http://localhost:8000"
INSIGHTS_DIR = Path('/home/liujerry/moltbot/memory/insights')
STATE_FILE = Path('/home/liujerry/moltbot/memory/.insights_sync_state.json')
GROUP_ID = "memory_insights_sync"


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def file_hash(path: Path) -> str:
    st = path.stat()
    return hashlib.md5(f"{st.st_size}:{st.st_mtime}:{st.st_ino}".encode()).hexdigest()


def build_episode_body(data: dict, fname: str) -> str:
    parts = [f"[insights/{fname}]"]
    parts.append(f"source: {data.get('source', 'unknown')}")
    ts = data.get('timestamp', '')
    if ts:
        parts.append(f"timestamp: {ts}")

    if 'concepts' in data:
        concepts = data.get('concepts', [])
        if concepts:
            names = [c.get('name', '') for c in concepts if c.get('name')]
            parts.append(f"concepts ({len(concepts)}): {', '.join(names[:25])}")
        relations = data.get('relations', [])
        if relations:
            rels = [f"{r.get('from','')}-{r.get('type','?')}-{r.get('to','')}" for r in relations]
            parts.append(f"relations ({len(relations)}): {', '.join(rels[:15])}")
        if 'summary' in data:
            parts.append(f"summary: {str(data['summary'])[:500]}")
        if 'key_findings' in data:
            parts.append(f"key_findings: {str(data['key_findings'])[:500]}")
    elif 'findings' in data:
        findings = data.get('findings', {})
        for section, content in findings.items():
            if isinstance(content, dict):
                keys = list(content.keys())[:10]
                parts.append(f"findings.{section}: {', '.join(keys)}")
            elif isinstance(content, list):
                parts.append(f"findings.{section}: {len(content)} items")
            else:
                parts.append(f"findings.{section}: {str(content)[:200]}")
    else:
        for k, v in list(data.items())[:8]:
            if isinstance(v, (str, int, float)):
                parts.append(f"{k}: {v}")
            elif isinstance(v, list):
                parts.append(f"{k}: [{len(v)} items]")
            elif isinstance(v, dict):
                parts.append(f"{k}: {{{len(v)} keys}}")

    return "\n".join(parts)


def post_message(name: str, body: str, source: str) -> bool:
    """POST to Graphiti /messages endpoint."""
    msg = {
        "content": body,
        "role_type": "user",
        "role": "memory",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_description": source,
        "name": name[:120],
    }
    payload = {"group_id": GROUP_ID, "messages": [msg]}
    try:
        r = requests.post(f"{GRAPHITI_API}/messages", json=payload, timeout=30)
        return r.status_code in (200, 202)
    except Exception as e:
        print(f"    ❌ POST error: {e}", file=sys.stderr)
        return False


def main():
    state = load_state()
    new_state = dict(state)
    added = 0
    skipped = 0
    failed = 0

    json_files = sorted(INSIGHTS_DIR.glob('*.json'))
    print(f"Found {len(json_files)} JSON files in insights/")
    print(f"Already processed: {len(state)}")

    for i, fpath in enumerate(json_files, 1):
        fh = file_hash(fpath)
        if state.get(fpath.name) == fh:
            skipped += 1
            continue
        try:
            data = json.loads(fpath.read_text())
            body = build_episode_body(data, fpath.name)
            ok = post_message(fpath.stem, body, f"insights:{fpath.name}")
            if ok:
                new_state[fpath.name] = fh
                added += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"  ❌ {fpath.name}: {e}", file=sys.stderr)

        if i % 100 == 0:
            print(f"  ... {i}/{len(json_files)} (added={added}, failed={failed})")
            save_state(new_state)  # periodic save

    save_state(new_state)
    print(f"\n=== Insights sync done ===")
    print(f"  Added: {added}")
    print(f"  Skipped (unchanged): {skipped}")
    print(f"  Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
