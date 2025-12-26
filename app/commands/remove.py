#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

from ..core.installer import Installer
from ..utils.logger import get_logger


def run(args):
    """Remove (uninstall) a package.
    
    Usage: pget remove <app_name>
    """
    if not args:
        logger = get_logger()
        logger.error("Usage: pget remove <app_name>")
        return False
    
    app_name = args[0]
    installer = Installer()
    
    return installer.uninstall(app_name)

