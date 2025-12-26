#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

from ..utils.paths import PGET_BIN
from ..utils.logger import get_logger
from ..utils.metadata import get_package_version


def run(args):
    """List installed packages.
    
    Usage: pget list
    """
    logger = get_logger()
    
    if not PGET_BIN.exists():
        logger.info("No packages installed")
        return True
    
    binaries = sorted([f.name for f in PGET_BIN.iterdir() if f.is_file() and not f.name.startswith('.')])
    
    if not binaries:
        logger.info("No packages installed")
        return True
    
    print(f"Installed packages in {PGET_BIN}:")
    print()  # Add blank line for spacing
    for name in binaries:
        version = get_package_version(name)
        print(f"  {name:<20} {version}")
    
    return True

