#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import os
import shutil
import tempfile
from pathlib import Path
from ..core.fetcher import GitHubFetcher
from ..core.installer import Installer
from ..utils.logger import get_logger
from ..utils.paths import get_binary_path, find_existing_binary
from ..utils.platform import get_platform_string


def update_pget_self(logger, installer, fetcher, edge_mode=False, script_mode=False, build_mode=False):
    """Update pget itself (special handling for self-update)."""
    current_version = installer.get_installed_version('pget')
    
    # Determine latest version
    if edge_mode:
        latest_version = "main"
        logger.info(f"Updating pget from {current_version} to latest main (--edge mode)")
    else:
        release = fetcher.get_latest_release('pget')
        if not release:
            logger.error("Could not fetch latest pget release")
            logger.info(f"Current version: {current_version}")
            logger.info("Try: pget update --script pget")
            return False
        
        latest_version = release.get("tag_name", "").lstrip('v')
        
        if current_version == latest_version and not edge_mode:
            logger.info(f"pget is already at the latest version ({current_version})")
            return True
        
        logger.info(f"Updating pget from {current_version} to {latest_version}")
    
    # Uninstall current version
    current_binary = find_existing_binary('pget') or get_binary_path('pget')
    installer.uninstall('pget')
    
    # Reinstall with specified mode
    from .install import run as install_run
    install_args = []
    if edge_mode:
        install_args.append('--edge')
    if script_mode:
        install_args.append('--script')
    if build_mode:
        install_args.append('--build')
    install_args.append('pget')
    
    ok = install_run(install_args)
    if ok:
        logger.info("Restart pget to use the new version")
    return ok


def run(args):
    """Update one or more packages to the latest version.
    
    Usage: pget update [--script|--build] [--edge] <app1>[,app2...]
           pget update [--script|--build] [--edge] app1 app2 ...
    """
    if not args:
        logger = get_logger()
        logger.error("Usage: pget update [--script|--build] [--edge] <app_name>[,app2...]")
        return False
    
    # Check for --edge flag
    edge_mode = False
    if '--edge' in args:
        edge_mode = True
        args = [a for a in args if a != '--edge']
        if not args:
            logger = get_logger()
            logger.error("Usage: pget update --edge <app_name>[,app2...]")
            return False
    
    # Check for --script flag
    script_mode = False
    if '--script' in args:
        script_mode = True
        args = [a for a in args if a != '--script']
        if not args:
            logger = get_logger()
            logger.error("Usage: pget update --script <app_name>[,app2...]")
            return False
    
    # Check for --build flag
    build_mode = False
    if '--build' in args:
        build_mode = True
        args = [a for a in args if a != '--build']
        if not args:
            logger = get_logger()
            logger.error("Usage: pget update --build <app_name>[,app2...]")
            return False
    
    # --build and --script are mutually exclusive
    if script_mode and build_mode:
        logger = get_logger()
        logger.error("--build and --script cannot be used together")
        return False
    
    def _parse_names(values):
        res = []
        for a in values:
            for part in a.split(","):
                part = part.strip()
                if part:
                    res.append(part)
        return res
    
    names = _parse_names(args)
    if not names:
        logger = get_logger()
        logger.error("Usage: pget update [--script|--build] [--edge] <app_name>[,app2...]")
        return False
    
    logger = get_logger()
    installer = Installer()
    fetcher = GitHubFetcher()
    overall = True
    
    for app_name in names:
        # Special handling for self-update
        if app_name == 'pget':
            ok = update_pget_self(logger, installer, fetcher, edge_mode=edge_mode, script_mode=script_mode, build_mode=build_mode)
            overall = overall and ok
            continue
        
        if not installer.is_installed(app_name):
            logger.error(f"{app_name} is not installed")
            logger.info(f"Use 'pget install {app_name}' to install it")
            overall = False
            continue
        
        # Check current version
        current_version = installer.get_installed_version(app_name)
        
        # In edge mode, always force update from main without version check
        if edge_mode:
            logger.info(f"Updating {app_name} from {current_version} to latest main (--edge mode)")
            installer.uninstall(app_name)
            
            from .install import run as install_run
            install_args = []
            if edge_mode:
                install_args.append('--edge')
            if script_mode:
                install_args.append('--script')
            if build_mode:
                install_args.append('--build')
            install_args.append(app_name)
            ok = install_run(install_args)
            overall = overall and ok
            continue
        
        # Get latest version from GitHub release
        release = fetcher.get_latest_release(app_name)
        latest_version = None
        
        if release:
            latest_version = release.get("tag_name", "").lstrip('v')
        
        # If no release, download source to check version
        if not latest_version:
            logger.debug("No release found, checking source repository")
            source_result = fetcher.download_app_directory(app_name, edge=edge_mode)
            if source_result and source_result[0]:
                source_path = source_result[0]
                doc_file = source_path / "doc" / f"{app_name}.yaml"
                logger.debug(f"Looking for doc at: {doc_file}")
                logger.debug(f"Doc exists: {doc_file.exists()}")
                if doc_file.exists():
                    import re
                    content = doc_file.read_text()
                    logger.debug(f"Doc content length: {len(content)}")
                    version_match = re.search(r'^VERSION:\s*"([^"]+)"', content, re.MULTILINE)
                    if version_match:
                        latest_version = version_match.group(1)
                        logger.debug(f"Found version in doc: {latest_version}")
        
        # Compare versions
        if not latest_version:
            logger.error(f"Could not determine latest version for {app_name}")
            logger.info(f"Current version: {current_version}")
            overall = False
            continue
        
        if current_version == latest_version:
            logger.info(f"{app_name} is already at the latest version ({current_version})")
            continue
        
        logger.info(f"Updating {app_name} from {current_version} to {latest_version}")
        installer.uninstall(app_name)
        
        from .install import run as install_run
        install_args = []
        if script_mode:
            install_args.append('--script')
        if build_mode:
            install_args.append('--build')
        install_args.append(app_name)
        ok = install_run(install_args)
        overall = overall and ok
    
    return overall

