#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-27

import shutil
import stat
from pathlib import Path
from ..utils.paths import (
    PGET_BIN,
    get_app_dir,
    get_doc_dir,
    ensure_dirs,
    ensure_path_in_shell,
    link_to_system_bin,
)
from ..utils.logger import get_logger
from ..utils.metadata import save_package_info


# New script directory (singular); keep legacy for migration.
PGET_SCRIPTS = Path.home() / ".pget" / "script"
LEGACY_SCRIPTS = Path.home() / ".pget" / "scripts"


def ensure_script_dir():
    """Ensure script directory exists; migrate legacy if needed."""
    if LEGACY_SCRIPTS.exists() and not PGET_SCRIPTS.exists():
        try:
            LEGACY_SCRIPTS.rename(PGET_SCRIPTS)
        except OSError:
            # If rename fails, fall back to creating the new dir
            pass
    PGET_SCRIPTS.mkdir(parents=True, exist_ok=True)


def install_as_script(source_path, app_name, version, source_url):
    """Install app as Python script (no Bazel required).

    Source is stored in ~/.pget/scripts/<app>/
    Executable wrapper is created in ~/.pget/bin/<app>

    Args:
        source_path: Path to extracted source code
        app_name: Name of the app
        version: Version string
        source_url: GitHub URL

    Returns:
        True if successful, False otherwise
    """
    logger = get_logger()
    ensure_dirs()
    ensure_script_dir()

    # Copy entire source to script directory (skip bazel artifacts and cache)
    script_dir = PGET_SCRIPTS / app_name

    # If source and destination are the same path (e.g. pget self-update from a script
    # install), make a temp copy first so rmtree doesn't delete the source.
    import tempfile as _tempfile
    _temp_dir = None
    if source_path.resolve() == script_dir.resolve():
        _temp_dir = Path(_tempfile.mkdtemp())
        _temp_source = _temp_dir / app_name
        shutil.copytree(source_path, _temp_source, symlinks=False)
        source_path = _temp_source

    if script_dir.exists():
        shutil.rmtree(script_dir)

    def ignore_patterns(dir, files):
        """Skip bazel artifacts, git, cache, and other build artifacts."""
        ignore = []
        for f in files:
            if (
                f.startswith('bazel-') or
                f in (
                    '.git',
                    '__pycache__',
                    '.pytest_cache',
                    '.mypy_cache',
                    'node_modules',
                )
            ):
                ignore.append(f)
        return ignore

    shutil.copytree(source_path, script_dir, ignore=ignore_patterns, symlinks=False)
    if _temp_dir and _temp_dir.exists():
        shutil.rmtree(_temp_dir, ignore_errors=True)
        source_path = script_dir  # point to installed copy for doc install below
    logger.debug(f"Copied source to {script_dir}")

    # Create executable wrapper in bin
    wrapper_path = PGET_BIN / app_name
    wrapper_content = """#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path.home() / ".pget" / "script" / "{app_name}"
if not (_root / "app" / "main.py").exists():
    print(
        "pget: {app_name} script install is missing or broken "
        "(expected source under ~/.pget/script/{app_name}/). "
        "Try: pget install {app_name}",
        file=sys.stderr,
    )
    sys.exit(1)
sys.path.insert(0, str(_root))
from app.main import main
sys.exit(main())
""".format(app_name=app_name)
    wrapper_path.write_text(wrapper_content)
    wrapper_path.chmod(
        wrapper_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
    )
    logger.debug(f"Created executable: {wrapper_path}")

    # Install documentation to helpers
    doc_source = source_path / "doc"
    if doc_source.exists():
        app_dir = get_app_dir(app_name)
        app_dir.mkdir(parents=True, exist_ok=True)
        doc_dest = get_doc_dir(app_name)
        if doc_dest.exists():
            shutil.rmtree(doc_dest)
        shutil.copytree(doc_source, doc_dest)
        logger.debug(f"Installed documentation for {app_name}")

    # Save metadata
    save_package_info(app_name, version, source_url, "script")

    logger.success(f"{app_name} installed successfully (script mode)")
    logger.info(f"Source: {script_dir}")
    ensure_path_in_shell()
    link_to_system_bin(app_name)

    return True


def uninstall_script(app_name):
    """Remove script installation.

    Args:
        app_name: Name of the app

    Returns:
        True if successful
    """
    logger = get_logger()

    # Remove script directory (new and legacy)
    script_dir = PGET_SCRIPTS / app_name
    legacy_dir = LEGACY_SCRIPTS / app_name
    for sd in (script_dir, legacy_dir):
        if sd.exists():
            shutil.rmtree(sd)
            logger.debug(f"Removed script: {sd}")

    return True

