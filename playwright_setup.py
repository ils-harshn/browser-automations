"""Must be imported before playwright. Ensures browsers exist on Render."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
from pathlib import Path

logger = logging.getLogger("playwright_setup")

PROJECT_ROOT = Path(__file__).resolve().parent

_configured = False
_install_lock = threading.Lock()
_install_done = False


def configure_playwright() -> None:
    global _configured
    if _configured:
        return
    _configured = True

    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        return

    if os.environ.get("PLAYWRIGHT_SKIP_INSTALL") == "1":
        return

    # Render native Python runtime: keep browsers inside the deploy directory.
    if os.environ.get("RENDER"):
        path = str(PROJECT_ROOT / ".playwright-browsers")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = path
        logger.info("Render detected; PLAYWRIGHT_BROWSERS_PATH=%s", path)


def _headless_shell_installed(browsers_dir: Path) -> bool:
    if not browsers_dir.is_dir():
        return False
    return any(browsers_dir.glob("**/chrome-headless-shell"))


def ensure_playwright_chromium() -> None:
    global _install_done

    configure_playwright()

    if os.environ.get("PLAYWRIGHT_SKIP_INSTALL") == "1":
        return

    browsers_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if browsers_path and _headless_shell_installed(Path(browsers_path)):
        return

    with _install_lock:
        if _install_done:
            return
        if browsers_path and _headless_shell_installed(Path(browsers_path)):
            _install_done = True
            return

        target = browsers_path or str(PROJECT_ROOT / ".playwright-browsers")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = target
        Path(target).mkdir(parents=True, exist_ok=True)

        logger.info("Installing Chromium to %s", target)
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            env=os.environ.copy(),
        )
        logger.info("Chromium install finished")
        _install_done = True


configure_playwright()
