#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import os
import tempfile
from pathlib import Path


PGET_ROOT = Path.home() / ".pget"
PGET_BIN = PGET_ROOT / "bin"
PGET_HELPERS = PGET_ROOT / "helpers"
PGET_PATH_LINE = 'export PATH="$HOME/.pget/bin:$PATH"'
SYSTEM_PATH_FILE = Path("/etc/paths.d/pget")
# Preferred system bin for sudo installs (POSIX). None if not applicable.
SYSTEM_BIN = Path("/usr/local/bin") if os.name != "nt" else None


def ensure_dirs():
    """Create pget directories if they don't exist."""
    PGET_BIN.mkdir(parents=True, exist_ok=True)
    PGET_HELPERS.mkdir(parents=True, exist_ok=True)


def ensure_path_in_shell():
    """Ensure ~/.pget/bin is added to PATH in common shell rc files (idempotent)."""
    rc_candidates = [
        Path.home() / ".zshrc",
        Path.home() / ".bashrc",
        Path.home() / ".bash_profile",
        Path.home() / ".profile",
    ]

    # If no rc files exist, create .profile
    if not any(rc.exists() for rc in rc_candidates):
        rc_candidates.append(Path.home() / ".profile")

    for rc in rc_candidates:
        try:
            existing = rc.read_text() if rc.exists() else ""
            if PGET_PATH_LINE not in existing:
                with rc.open("a") as f:
                    f.write("\n" + PGET_PATH_LINE + "\n")
        except OSError:
            # Best-effort; do not crash install
            continue


def ensure_system_path():
    """Attempt to add ~/.pget/bin to system PATH via /etc/paths.d (may require sudo).

    Tries to write /etc/paths.d/pget so shells pick up the path automatically.
    Falls back to per-user shell RC if not permitted.
    """
    # If already exists, do nothing
    try:
        if SYSTEM_PATH_FILE.exists():
            existing = SYSTEM_PATH_FILE.read_text().strip()
            if str(PGET_BIN) in existing:
                return True
    except OSError:
        # Ignore and fall back
        return False

    # If running as root, write directly
    try:
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            SYSTEM_PATH_FILE.write_text(str(PGET_BIN))
            return True
    except Exception:
        return False

    # Try writing with elevated privileges (will prompt for password if required)
    try:
        import subprocess
        cmd = [
            "sudo",
            "sh",
            "-c",
            f'echo "{PGET_BIN}" > "{SYSTEM_PATH_FILE}"',
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        # Fall back silently; per-user path will still work
        return False


def get_binary_path(app_name):
    """Get path to installed binary."""
    return PGET_BIN / app_name


def get_system_binary_path(app_name):
    """Get system path for installed binary (may be None on non-POSIX)."""
    if SYSTEM_BIN is None:
        return None
    return SYSTEM_BIN / app_name


def find_existing_binary(app_name):
    """Return existing binary path (system preferred) if present."""
    for candidate in (get_system_binary_path(app_name), get_binary_path(app_name)):
        if candidate and candidate.exists():
            return candidate
    return None


def get_temp_cache_dir(app_name):
    """Get temporary cache directory for app (auto-cleaned on reboot)."""
    cache_dir = Path(tempfile.gettempdir()) / "pget" / app_name
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cache_path(app_name, filename):
    """Get path to cached file in temp directory."""
    return get_temp_cache_dir(app_name) / filename


def get_app_dir(app_name):
    """Get path to app's helper directory in ~/.pget/helpers/."""
    return PGET_HELPERS / app_name


def get_doc_dir(app_name):
    """Get path to app's documentation directory."""
    return get_app_dir(app_name) / "doc"


def get_data_dir(app_name):
    """Get path to app's data directory (for databases, persistent storage)."""
    return get_app_dir(app_name) / "data"


def get_config_dir(app_name):
    """Get path to app's config directory (user settings)."""
    return get_app_dir(app_name) / "config"


def get_cache_dir(app_name):
    """Get path to app's cache directory (temporary data)."""
    return get_app_dir(app_name) / "cache"

