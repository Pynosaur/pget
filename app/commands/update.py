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


def update_pget_self(logger, installer, fetcher, edge_mode=False):
    """Update pget itself (special handling for self-update)."""
    current_version = installer.get_installed_version('pget')
    
    # In edge mode, always update from main
    if edge_mode:
        logger.info(f"Updating pget from {current_version} to latest main (--edge mode)")
        logger.info("Edge mode for pget self-update requires local source rebuild")
        logger.info("Run: cd pget && python3 app/main.py install pget")
        return False
    
    # Get latest version
    release = fetcher.get_latest_release('pget')
    if not release:
        logger.error("Could not fetch latest pget release")
        logger.info(f"Current version: {current_version}")
        logger.info("Try updating from source: git pull && bazel build //:pget_bin")
        return False
    
    latest_version = release.get("tag_name", "").lstrip('v')
    
    if current_version == latest_version:
        logger.info(f"pget is already at the latest version ({current_version})")
        return True
    
    logger.info(f"Updating pget from {current_version} to {latest_version}")
    
    # Download new version
    platform = get_platform_string()
    binary_result = fetcher.download_binary('pget', platform)
    
    if not binary_result or not binary_result[0]:
        logger.error("No binary available for your platform")
        logger.info("Update from source: git pull && bazel build //:pget_bin && cp bazel-bin/pget ~/.pget/bin/")
        return False
    
    new_binary_path, version = binary_result
    current_binary = find_existing_binary('pget') or get_binary_path('pget')
    
    # Backup current binary
    backup_path = current_binary.parent / "pget.old"
    if current_binary.exists():
        shutil.copy(current_binary, backup_path)
        logger.debug(f"Backed up current pget to {backup_path}")
    
    # Replace with new binary (no sudo subprocess; fall back if permission denied)
    try:
        shutil.copy(new_binary_path, current_binary)
        current_binary.chmod(current_binary.stat().st_mode | 0o111)  # Make executable
        replaced = True
    except Exception:
        logger.error("Failed to update pget (permission denied); run update with write access to the install path.")
        replaced = False

    if replaced:
        logger.success(f"pget updated successfully to {latest_version}")
        logger.info("Restart pget to use the new version")
        if backup_path.exists():
            backup_path.unlink()
        return True

    logger.error("Failed to update pget")
    if backup_path.exists():
        shutil.copy(backup_path, current_binary)
        logger.info("Restored previous version")
    return False


def run(args):
    """Update one or more packages to the latest version.
    
    Usage: pget update [--edge] [--script] <app1>[,app2...]
           pget update [--edge] [--script] app1 app2 ...
    """
    if not args:
        logger = get_logger()
        logger.error("Usage: pget update [--edge] [--script] <app_name>[,app2...]")
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
        logger.error("Usage: pget update [--edge] [--script] <app_name>[,app2...]")
        return False
    
    logger = get_logger()
    installer = Installer()
    fetcher = GitHubFetcher()
    overall = True
    
    for app_name in names:
        # Special handling for self-update
        if app_name == 'pget':
            ok = update_pget_self(logger, installer, fetcher, edge_mode=edge_mode)
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
        install_args.append(app_name)
        ok = install_run(install_args)
        overall = overall and ok
    
    return overall

