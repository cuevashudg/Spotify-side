"""
Personality-driven analysis with interactive tone selection.

DEPRECATED: This script is now a backwards-compatible wrapper.
Use `scripts/analyze.py --interactive` instead for the unified tool.

Usage (old style):
  python scripts/roast_me.py    # Interactive menu

Usage (new style):
  python scripts/analyze.py --interactive    # Interactive menu with all options
  python scripts/analyze.py                  # Standard behavioral analysis
"""

import sys
import subprocess


def main():
    """Wrapper for analyze.py --interactive - maintains backwards compatibility."""
    
    # Call analyze.py with --interactive flag
    cmd = [sys.executable, "scripts/analyze.py", "--interactive"]
    
    # Execute analyze.py
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

