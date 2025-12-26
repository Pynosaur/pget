#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

from ..core.fetcher import GitHubFetcher
from ..core.installer import Installer
from ..utils.logger import get_logger


def run(args):
    """Update a package to the latest version.
    
    Usage: pget update <app_name>
    """
    if not args:
        logger = get_logger()
        logger.error("Usage: pget update <app_name>")
        return False
    
    app_name = args[0]
    logger = get_logger()
    installer = Installer()
    fetcher = GitHubFetcher()
    
    if not installer.is_installed(app_name):
        logger.error(f"{app_name} is not installed")
        logger.info(f"Use 'pget install {app_name}' to install it")
        return False
    
    # Check current version
    current_version = installer.get_installed_version(app_name)
    
    # Get latest version from GitHub release
    release = fetcher.get_latest_release(app_name)
    latest_version = None
    
    if release:
        latest_version = release.get("tag_name", "").lstrip('v')
    
    # If no release, download source to check version
    if not latest_version:
        logger.debug("No release found, checking source repository")
        source_result = fetcher.download_app_directory(app_name)
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
        return False
    
    if current_version == latest_version:
        logger.info(f"{app_name} is already at the latest version ({current_version})")
        return True
    
    logger.info(f"Updating {app_name} from {current_version} to {latest_version}")
    installer.uninstall(app_name)
    
    from .install import run as install_run
    return install_run([app_name])

