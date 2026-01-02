#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

from ..core.installer import Installer
from ..utils.logger import get_logger


def _parse_names(args):
    names = []
    for a in args:
        for part in a.split(","):
            part = part.strip()
            if part:
                names.append(part)
    return names


def run(args):
    """Remove (uninstall) one or more packages.
    
    Usage: pget remove <app1>[,app2...] | pget remove app1 app2 ...
    """
    logger = get_logger()
    names = _parse_names(args)
    if not names:
        logger.error("Usage: pget remove <app_name>[,app2...]")
        return False
    
    installer = Installer()
    overall = True
    for name in names:
        ok = installer.uninstall(name)
        overall = overall and ok
    return overall

