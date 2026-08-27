#!/usr/bin/env python3
"""
Cog CLI module execution entry point (python -m core.engine or python -m core).
"""

import sys
# Force UTF-8 console output on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from pathlib import Path

# Add parent directory to sys.path to allow execution from outside
CORE_DIR = Path(__file__).resolve().parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from engine import CogEngine

if __name__ == "__main__":
    target_repo = Path.cwd()
    engine = CogEngine(target_repo)
    engine.dispatch(sys.argv[1:])