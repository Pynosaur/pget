#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

from ..core.fetcher import GitHubFetcher
from ..core.installer import Installer
from ..utils.platform import get_platform_string
from ..utils.logger import get_logger


def run(args):
    """Install a package.
    
    Usage: pget install <app_name>
    """
    if not args:
        logger = get_logger()
        logger.error("Usage: pget install <app_name>")
        return False
    
    app_name = args[0]
    logger = get_logger()
    fetcher = GitHubFetcher()
    installer = Installer()
    
    # Check if already installed and get available version
    if installer.is_installed(app_name):
        current_version = installer.get_installed_version(app_name)
        
        # Check for newer version
        release = fetcher.get_latest_release(app_name)
        if release:
            latest_version = release.get("tag_name", "unknown")
            if latest_version != current_version and latest_version != "unknown":
                logger.info(f"{app_name} {current_version} is installed, but {latest_version} is available")
                logger.info("Use 'pget update' to upgrade")
            else:
                logger.warning(f"{app_name} {current_version} is already installed")
        else:
            logger.warning(f"{app_name} {current_version} is already installed")
        
        logger.info("Use 'pget remove' to uninstall first if you want to reinstall")
        return False
    
    logger.info(f"Installing {app_name}")
    
    # Check if repo exists
    repo_info = fetcher.get_repo_info(app_name)
    if not repo_info:
        logger.error(f"Package '{app_name}' not found in pynosaur organization")
        return False
    
    platform = get_platform_string()
    source_url = repo_info.get("html_url", "")
    
    # Try to download binary first (release asset)
    binary_result = fetcher.download_binary(app_name, platform)
    if binary_result and binary_result[0]:
        binary_path, version = binary_result
        
        # Also download source for documentation
        logger.debug(f"Downloading source for documentation")
        source_result = fetcher.download_app_directory(app_name)
        source_path = source_result[0] if source_result else None
        
        # Install binary
        success = installer.install_binary(
            binary_path=binary_path,
            app_name=app_name,
            version=version,
            source_url=source_url,
            platform=platform
        )
        
        # Install documentation if source was downloaded
        if success and source_path:
            installer.install_doc_files(source_path, app_name)
        
        return success
    
    # Build with Bazel (required if no release binary)
    logger.info("No release binary found; building with Bazel (bazel required)")
    source_result = fetcher.download_app_directory(app_name)
    
    if not source_result or not source_result[0]:
        logger.error(f"Failed to download {app_name}")
        return False
    
    source_path, version = source_result

    return installer.install_with_bazel(
        source_path=source_path,
        app_name=app_name,
        version=version,
        source_url=source_url,
        platform=platform
    )

