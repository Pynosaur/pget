#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

from ..utils.paths import PGET_BIN
from ..utils.logger import get_logger
from ..utils.metadata import get_package_version
from ..core.script_installer import PGET_SCRIPTS, LEGACY_SCRIPTS


def run(args):
    """List installed packages.
    
    Usage: pget list
    """
    logger = get_logger()
    
    # Check scripts first
    scripts = set()
    for script_dir in (PGET_SCRIPTS, LEGACY_SCRIPTS):
        if script_dir.exists():
            for f in script_dir.iterdir():
                if f.is_dir():
                    scripts.add(f.name)
    scripts = sorted(scripts)
    
    # Check binaries (exclude script wrappers)
    binaries = []
    if PGET_BIN.exists():
        for f in PGET_BIN.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                # Skip if this is a script wrapper
                if f.name not in scripts:
                    binaries.append(f.name)
        binaries = sorted(binaries)
    
    if not binaries and not scripts:
        logger.info("No packages installed")
        return True
    
    if binaries:
        print(f"Installed packages in {PGET_BIN}:")
        print()
        for name in binaries:
            version = get_package_version(name)
            print(f"  {name:<20} {version}")
    
    if scripts:
        if binaries:
            print()
        print(f"Installed scripts in {PGET_SCRIPTS}:")
        print()
        for name in scripts:
            version = get_package_version(name)
            print(f"  {name:<20} {version}  [script]")
    
    return True
