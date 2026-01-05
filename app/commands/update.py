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
    from ..core.script_installer import install_as_script
    from ..utils.platform import get_platform_string
    from pathlib import Path
    
    current_version = installer.get_installed_version('pget')
    current_binary = find_existing_binary('pget') or get_binary_path('pget')
    
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
    
    # For script mode, use uninstall+reinstall (wrapper not locked)
    if script_mode or not current_binary.exists():
        installer.uninstall('pget')
        from .install import run as install_run
        install_args = ['--script'] if script_mode else []
        if edge_mode:
            install_args.append('--edge')
        install_args.append('pget')
        ok = install_run(install_args)
        if ok:
            logger.info("Restart pget to use the new version")
        return ok
    
    # For binary mode: download and swap (can't delete running binary)
    platform = get_platform_string()
    
    if build_mode or (not edge_mode and not script_mode):
        # Try downloading binary first (unless build mode)
        if not build_mode:
            binary_result = fetcher.download_binary('pget', platform)
            if binary_result and binary_result[0]:
                new_binary_path, _ = binary_result
                
                # Backup and replace strategy
                backup_path = current_binary.parent / "pget.old"
                try:
                    # Make current binary writable
                    if current_binary.exists():
                        current_binary.chmod(0o755)
                        shutil.copy(current_binary, backup_path)
                        logger.debug(f"Backed up to {backup_path}")
                    
                    # Replace (unlink first to avoid permission issues)
                    if current_binary.exists():
                        current_binary.unlink()
                    
                    shutil.copy(new_binary_path, current_binary)
                    current_binary.chmod(0o755)
                    
                    # Update metadata
                    from ..utils.metadata import save_package_info
                    save_package_info('pget', latest_version, f"https://github.com/pynosaur/pget", platform)
                    
                    logger.success(f"pget updated to {latest_version}")
                    logger.info("Restart pget to use the new version")
                    
                    # Remove backup immediately if successful
                    if backup_path.exists():
                        try:
                            backup_path.chmod(0o755)  # Ensure writable
                            backup_path.unlink()
                            logger.debug("Removed backup file")
                        except Exception as e:
                            logger.debug(f"Could not remove backup: {e}")
                    
                    return True
                except Exception as e:
                    logger.error(f"Failed to update: {e}")
                    # Restore from backup
                    if backup_path.exists() and not current_binary.exists():
                        try:
                            shutil.copy(backup_path, current_binary)
                            current_binary.chmod(0o755)
                            logger.info("Restored previous version")
                        except:
                            pass
                    return False
    
    # Build from source if requested or no binary available
    logger.info("Building pget from source for self-update")
    
    # Download source from GitHub (not local)
    use_edge = edge_mode
    version_to_download = None if edge_mode else latest_version
    source_result = fetcher.download_app_directory('pget', edge=use_edge, version=version_to_download)
    if not source_result or not source_result[0]:
        logger.error("Failed to download pget source")
        return False
    
    source_path, version_tag = source_result
    
    # Uninstall current version
    installer.uninstall('pget')
    
    # Build and install from downloaded source
    success = installer.install_with_bazel(
        source_path=source_path,
        app_name='pget',
        version=latest_version if not edge_mode else 'main',
        source_url="https://github.com/pynosaur/pget",
        platform=platform,
    )
    
    if success:
        logger.success(f"pget updated to {latest_version if not edge_mode else 'main'}")
        logger.info("Restart pget to use the new version")
    
    return success


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
    
    # Check for --no-verify-ssl flag
    no_verify_ssl = False
    if '--no-verify-ssl' in args:
        no_verify_ssl = True
        args = [a for a in args if a != '--no-verify-ssl']
    
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
        logger.error("Usage: pget update [--script|--build] [--edge] [--no-verify-ssl] <app_name>[,app2...]")
        return False
    
    logger = get_logger()
    installer = Installer()
    fetcher = GitHubFetcher(verify_ssl=not no_verify_ssl)
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

