#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import os
import platform as _platform
import tempfile
from pathlib import Path


PGET_ROOT = Path.home() / ".pget"
PGET_BIN = PGET_ROOT / "bin"
PGET_HELPERS = PGET_ROOT / "helpers"
PGET_PATH_LINE = 'export PATH="$HOME/.pget/bin:$PATH"'
SYSTEM_PATH_FILE = Path("/etc/paths.d/pget")
LINUX_PROFILE_FILE = Path("/etc/profile.d/pget.sh")
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
    """Attempt to add ~/.pget/bin to system PATH via OS-appropriate mechanism.

    macOS: writes /etc/paths.d/pget
    Linux: writes /etc/profile.d/pget.sh
    Falls back to per-user shell RC if not permitted.
    """
    if _platform.system() == "Darwin":
        return _ensure_system_path_macos()
    return _ensure_system_path_linux()


def _ensure_system_path_macos():
    """Add PATH via /etc/paths.d (macOS only)."""
    try:
        if SYSTEM_PATH_FILE.exists():
            existing = SYSTEM_PATH_FILE.read_text().strip()
            if str(PGET_BIN) in existing:
                return True
    except OSError:
        return False

    try:
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            SYSTEM_PATH_FILE.write_text(str(PGET_BIN))
            return True
    except Exception:
        return False

    return False


def _ensure_system_path_linux():
    """Add PATH via /etc/profile.d (Linux)."""
    try:
        if LINUX_PROFILE_FILE.exists():
            existing = LINUX_PROFILE_FILE.read_text()
            if PGET_PATH_LINE in existing:
                return True
    except OSError:
        return False

    try:
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            LINUX_PROFILE_FILE.write_text(PGET_PATH_LINE + "\n")
            return True
    except Exception:
        return False

    return False


def link_to_system_bin(app_name):
    """Symlink installed binary into /usr/local/bin for immediate PATH access.

    Returns True if symlink was created, False otherwise.
    """
    if SYSTEM_BIN is None:
        return False

    source = PGET_BIN / app_name
    if not source.exists():
        return False

    dest = SYSTEM_BIN / app_name
    try:
        # Remove existing symlink/file if it points to our binary
        if dest.is_symlink():
            if dest.resolve() == source.resolve():
                return True
            dest.unlink()
        elif dest.exists():
            # Don't overwrite non-symlink files we didn't create
            return False

        dest.symlink_to(source)
        return True
    except OSError:
        return False


def unlink_from_system_bin(app_name):
    """Remove symlink from /usr/local/bin if it points to our binary.

    Returns True if removed or didn't exist, False on error.
    """
    if SYSTEM_BIN is None:
        return True

    dest = SYSTEM_BIN / app_name
    source = PGET_BIN / app_name
    try:
        if dest.is_symlink():
            # Only remove if it points to our binary
            if dest.resolve() == source.resolve() or not source.exists():
                dest.unlink()
        return True
    except OSError:
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

