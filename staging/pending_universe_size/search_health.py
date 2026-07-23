#!/usr/bin/env python3
"""Probe whether the websearch backends are alive. Prints one line:
   OK <engine> | DOWN
Used to decide when it is safe to resume size enrichment after the
parallel-load bot-detection outage. A single control-query, run rarely."""
import subprocess, sys, os

TOOL = os.path.expanduser("~/.claude/tools/websearch.py")
Q = "Apple Inc market capitalization revenue employees"

def try_engine(args):
    try:
        out = subprocess.run(
            [sys.executable, TOOL, *args, Q],
            capture_output=True, text=True, timeout=40,
        )
        txt = out.stdout
        # a healthy result has numbered hits and a real URL
        if "http" in txt and (". " in txt) and "fetch failed" not in txt \
           and "no parseable" not in txt and "blocked" not in txt:
            return True
    except Exception:
        pass
    return False

if try_engine(["-n", "3"]):
    print("OK ddg")
elif try_engine(["--engine", "bing", "-n", "3"]):
    print("OK bing")
else:
    print("DOWN")
