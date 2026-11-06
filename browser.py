"""PyBrowser legacy compatibility launcher.

Maintains backward compatibility with 'python browser.py' while delegating
to the modern, modular PySide6 architecture in src/pybrowser.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to sys.path so running 'python browser.py' works directly without pip install -e .
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pybrowser.app import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
