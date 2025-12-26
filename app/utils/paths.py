#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import tempfile
from pathlib import Path


PGET_ROOT = Path.home() / ".pget"
PGET_BIN = PGET_ROOT / "bin"
PGET_HELPERS = PGET_ROOT / "helpers"
PGET_PATH_LINE = 'export PATH="$HOME/.pget/bin:$PATH"'


def ensure_dirs():
    """Create pget directories if they don't exist."""
    PGET_BIN.mkdir(parents=True, exist_ok=True)
    PGET_HELPERS.mkdir(parents=True, exist_ok=True)


def ensure_path_in_shell():
    """Ensure ~/.pget/bin is added to user's shell PATH in rc file (idempotent)."""
    rc_candidates = [
        Path.home() / ".zshrc",
        Path.home() / ".bashrc",
        Path.home() / ".bash_profile",
        Path.home() / ".profile",
    ]

    target_rc = None
    for rc in rc_candidates:
        if rc.exists():
            target_rc = rc
            break
    if target_rc is None:
        target_rc = Path.home() / ".profile"

    try:
        existing = ""
        if target_rc.exists():
            existing = target_rc.read_text()
        if PGET_PATH_LINE not in existing:
            with target_rc.open("a") as f:
                f.write("\n" + PGET_PATH_LINE + "\n")
    except OSError:
        # Best-effort; do not crash install
        pass


def get_binary_path(app_name):
    """Get path to installed binary."""
    return PGET_BIN / app_name


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

