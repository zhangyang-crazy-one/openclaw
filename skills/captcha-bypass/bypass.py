#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Captcha Bypass Skill - 使用 Claude Code 分析并生成滑块验证码绕过代码

Usage:
    python3 bypass.py <target_url> [--output <dir>] [--analyze-only]
    
Or invoke directly:
    @DeepSeeker 帮我绕过验证码 https://example.com/captcha
"""

import argparse
import os
import subprocess
import json
import sys
import time
from pathlib import Path

SKILL_DIR = Path(__file__).parent
DEFAULT_OUTPUT = Path("~/captcha_bypass").expanduser()


def check_dependencies():
    """Check required dependencies"""
    missing = []
    
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("claude")
    
    if missing:
        print(f"Missing: {', '.join(missing)}")
        return False
    return True


def generate_prompt(target_url: str, output_dir: Path, analyze_only: bool = False) -> str:
    """Generate the Claude Code prompt"""
    
    task_type = "analyze only" if analyze_only else "full analysis and code generation"
    
    prompt = f"""# Task: Slider Captcha Bypass Analysis

## Target Website
{target_url}

## Task Type
{task_type}

## Steps

### Phase 1: Analyze Target Website
1. Visit the target website
2. Identify captcha type (Geetest 4th gen / Tencent WaterWall / Other)
3. Analyze captcha initialization requests and parameters

### Phase 2: Generate Bypass Code (if not analyze-only)
Create the following files in {output_dir}:

1. **analyze_result.md** - Analysis report
2. **solver.py** - Main bypass code (Selenium + OpenCV)
3. **trajectory.py** - Human trajectory simulation
4. **requirements.txt** - Dependencies

### Geetest 4th Gen Key Parameters
- `c`: Encrypted verification info
- `s`: Signature  
- `w`: Encrypted trajectory data

### Gap Detection Algorithm
```python
import cv2
import numpy as np

def find_gap(bg_path, gap_path):
    bg = cv2.imread(bg_path, 0)
    gap = cv2.imread(gap_path, 0)
    result = cv2.matchTemplate(bg, gap, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(result)
    return max_loc[0]
```

### Trajectory Generation Algorithm
```python
import random

def generate_trajectory(distance, duration=1.5):
    def ease_out(t):
        return 1 - (1 - t) ** 3
    
    points = []
    for i in range(int(duration * 60)):
        t = i / (duration * 60)
        x = distance * ease_out(t)
        jitter = random.uniform(-1, 1)
        points.append((x + jitter, random.uniform(-0.5, 0.5)))
    return points
```

## Requirements
- For authorized security testing only
- Generate complete runnable code
- Include detailed comments

## Completion Report
1. Captcha type
2. Key findings
3. Generated file list
4. Bypass approach
"""
    return prompt.strip()


def analyze_and_generate(target_url: str, output_dir: Path, analyze_only: bool = False):
    """Use Claude Code to analyze target website"""
    
    session_name = f"captcha-bypass-{int(time.time())}"
    prompt = generate_prompt(target_url, output_dir, analyze_only)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save session info
    session_info = {
        "session_name": session_name,
        "target_url": target_url,
        "output_dir": str(output_dir),
        "analyze_only": analyze_only,
        "created_at": str(time.time())
    }
    (output_dir / ".session_info.json").write_text(json.dumps(session_info, indent=2))
    
    # Build claude command
    cmd = [
        "claude",
        "--print",
        "--permission-mode", "bypassPermissions",
        "--no-session-persistence",
        "-n", session_name,
        prompt
    ]
    
    print(f"Starting Claude Code session: {session_name}")
    print(f"Target: {target_url}")
    print(f"Output: {output_dir}")
    print(f"Mode: {'analyze only' if analyze_only else 'full generation'}")
    print()
    print("Claude Code is analyzing... (this may take a few minutes)")
    print(f"Session log: ~/.claude/sessions/{session_name}/session.jsonl")
    print()
    
    # Run in background
    log_file = output_dir / "claude_output.log"
    try:
        with open(log_file, "w") as f:
            result = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(SKILL_DIR)
            )
        print(f"Claude Code started (PID: {result.pid})")
        print(f"Output log: {log_file}")
        return True
    except Exception as e:
        print(f"Failed to start: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Slider captcha bypass analysis using Claude Code"
    )
    parser.add_argument("target_url", help="Target website URL")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT,
                        help=f"Output directory (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--analyze-only", "-a", action="store_true",
                        help="Analyze only, do not generate bypass code")
    
    args = parser.parse_args()
    
    if not check_dependencies():
        sys.exit(1)
    
    output_dir = args.output / f"target_{int(time.time())}"
    success = analyze_and_generate(args.target_url, output_dir, args.analyze_only)
    
    if success:
        print()
        print("Claude Code is running in background.")
        print("Check output with: tail -f", output_dir / "claude_output.log")
    else:
        print("Failed to start")
        sys.exit(1)


if __name__ == "__main__":
    main()
