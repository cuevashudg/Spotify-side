"""
Behavioral analysis report with roast mode.

DEPRECATED: This script is now a backwards-compatible wrapper.
Use `scripts/analyze.py` instead for the unified analysis tool.

Usage (old style):
  python scripts/behavioral_report.py        # Standard report
  python scripts/behavioral_report.py --roast  # With roast commentary

Usage (new style):
  python scripts/analyze.py                  # Standard report
  python scripts/analyze.py --roast          # With roast commentary
  python scripts/analyze.py --interactive    # Interactive menu
"""

import sys
import subprocess


def main():
    """Wrapper for analyze.py - maintains backwards compatibility."""
    
    # Determine if --roast flag was passed
    args = sys.argv[1:]
    
    # Build call to analyze.py with same arguments
    cmd = [sys.executable, "scripts/analyze.py"] + args
    
    # Execute analyze.py
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

