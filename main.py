#!/usr/bin/env python3
"""
MoneyPulse - local-first financial document processing
Desktop application entry point.
"""

import logging
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

def windows_application_data_dir():
    local_app_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return base / "MoneyPulse"


def setup_application(data_dir=BASE_DIR):
    """Create needed dirs and configure logging."""
    for folder in ("input", "output", "logs"):
        (data_dir / folder).mkdir(parents=True, exist_ok=True)

    log_path = data_dir / "logs" / "application.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point: setup then launch GUI."""
    frozen_windows = sys.platform == "win32" and getattr(sys, "frozen", False)
    data_dir = windows_application_data_dir() if frozen_windows else None
    try:
        setup_application(data_dir or BASE_DIR)

        from src.gui.premium_gui import launch_application
        launch_application(data_dir=data_dir)

    except ImportError:
        logging.exception("Application dependencies failed to load")
        if not frozen_windows:
            print("Check the desktop dependencies in requirements.txt.", file=sys.stderr)
        sys.exit(1)

    except Exception:
        logging.exception("Unhandled application error")
        sys.exit(1)

if __name__ == "__main__":
    main()
