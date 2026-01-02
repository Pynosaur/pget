#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import shutil
import urllib.error
import urllib.request
from pathlib import Path
from ..core.config import IGNORED_REPOS
from ..core.fetcher import GitHubFetcher
from ..core.installer import Installer
from ..core.script_installer import install_as_script
from ..utils.platform import get_platform_string
from ..utils.logger import get_logger
from ..utils.paths import ensure_path_in_shell
from .. import __version__ as PGET_VERSION


def _parse_names(args):
    names = []
    for a in args:
        for part in a.split(","):
            part = part.strip()
            if part:
                names.append(part)
    return names


def run(args):
    """Install one or more packages.
    
    Usage: pget install [--script] [--edge] <app1>[,app2...]
           pget install [--script] [--edge] app1 app2 ...
    """
    if not args:
        logger = get_logger()
        logger.error("Usage: pget install [--script] [--edge] <app_name>[,app2...]")
        return False
    
    # Check for --script flag (accept anywhere in args)
    script_mode = False
    if '--script' in args:
        script_mode = True
        args = [a for a in args if a != '--script']
        if not args:
            logger = get_logger()
            logger.error("Usage: pget install --script <app_name>[,app2...]")
            return False
    
    # Check for --edge flag (accept anywhere in args)
    edge_mode = False
    if '--edge' in args:
        edge_mode = True
        args = [a for a in args if a != '--edge']
        if not args:
            logger = get_logger()
            logger.error("Usage: pget install --edge <app_name>[,app2...]")
            return False
    
    names = _parse_names(args)
    # Guard against stray flag tokens
    names = [n for n in names if n not in ('--script', '--edge')]
    if not names:
        logger = get_logger()
        logger.error("Usage: pget install [--script] [--edge] <app_name>[,app2...]")
        return False
    
    logger = get_logger()
    fetcher = GitHubFetcher()
    installer = Installer()
    overall_success = True
    
    for app_name in names:
        if app_name in IGNORED_REPOS:
            logger.info(f"Skipping non-installable repo '{app_name}' (marked as webpage)")
            overall_success = False
            continue

        # Special-case installing pget itself from the local repo to avoid stale releases
        if app_name == "pget":
            logger.info("Installing pget from local source")
            source_path = Path(__file__).resolve().parents[2]
            platform = get_platform_string()
            success = False
            
            # Honor --script flag for pget self-install
            if script_mode:
                logger.info("Installing as Python script (no compilation)")
                success = install_as_script(source_path, app_name, PGET_VERSION, str(source_path))
            else:
                # Check if Bazel is available
                bazel = shutil.which("bazelisk") or shutil.which("bazel")
                if not bazel:
                    logger.error("Bazel required for building pget binary")
                    logger.info("Bazel not found. Install as script instead?")
                    
                    try:
                        response = input("Install as script? [y/N]: ").strip().lower()
                        if response in ('y', 'yes'):
                            logger.info("Installing as Python script (no compilation)")
                            success = install_as_script(source_path, app_name, PGET_VERSION, str(source_path))
                        else:
                            logger.error("Installation cancelled")
                            logger.info("Install Bazel or use: python app/main.py install --script pget")
                            overall_success = False
                            continue
                    except (KeyboardInterrupt, EOFError):
                        logger.error("Installation cancelled")
                        logger.info("Install Bazel or use: python app/main.py install --script pget")
                        overall_success = False
                        continue
                else:
                    success = installer.install_with_bazel(
                        source_path=source_path,
                        app_name=app_name,
                        version=PGET_VERSION,
                        source_url=str(source_path),
                        platform=platform,
                    )
            
            overall_success = overall_success and success
            if app_name == "pget" and success:
                ensure_path_in_shell()
                logger.info("Added ~/.pget/bin to PATH. Open a new shell to use 'pget'.")
            continue

        # Check if already installed and get available version
        if installer.is_installed(app_name):
            current_version = installer.get_installed_version(app_name)
            
            # Determine installation type
            from ..utils.metadata import get_package_info
            pkg_info = get_package_info(app_name)
            install_type = pkg_info.get('platform', 'unknown') if pkg_info else 'unknown'
            
            type_msg = "script version" if install_type == 'script' else "binary version"
            
            # Check for newer version
            release = fetcher.get_latest_release(app_name)
            if release:
                latest_version = release.get("tag_name", "unknown")
                if latest_version != current_version and latest_version != "unknown":
                    logger.warning(f"A {type_msg} of {app_name} ({current_version}) is already installed")
                    logger.info(f"Version {latest_version} is available")
                    logger.info("Use 'pget update' to upgrade")
                else:
                    logger.warning(f"A {type_msg} of {app_name} ({current_version}) is already installed")
            else:
                logger.warning(f"A {type_msg} of {app_name} ({current_version}) is already installed")
            
            logger.info("Use 'pget remove' to uninstall first if you want to reinstall")
            overall_success = False
            continue
        
        logger.info(f"Installing {app_name}")
        if edge_mode:
            logger.info("Using --edge mode (latest main branch)")
        
        # Check if repo exists
        repo_info = fetcher.get_repo_info(app_name)
        if not repo_info:
            logger.error(f"Package '{app_name}' not found in pynosaur organization")
            overall_success = False
            continue
        
        # Check if repo has .program marker (indicates it's an installable app)
        from ..core.config import GITHUB_RAW, PYNOSAUR_ORG
        program_url = f"{GITHUB_RAW}/{PYNOSAUR_ORG}/{app_name}/main/.program"
        try:
            req = urllib.request.Request(program_url)
            urllib.request.urlopen(req, timeout=5)
        except (urllib.error.HTTPError, urllib.error.URLError):
            logger.error(f"'{app_name}' is not an installable program (missing .program marker)")
            logger.info("This repository may be a website or documentation-only repo")
            overall_success = False
            continue
        
        platform = get_platform_string()
        source_url = repo_info.get("html_url", "")
        
        success = False
        installed_version = None
        install_platform = None
        
        # Skip binary download if --script flag is set
        if not script_mode:
            # Try to download binary first (release asset)
            binary_result = fetcher.download_binary(app_name, platform)
            if binary_result and binary_result[0]:
                binary_path, version = binary_result
                
                # Also download source for documentation
                logger.debug("Downloading source for documentation")
                source_result = fetcher.download_app_directory(app_name, edge=edge_mode)
                source_path = source_result[0] if source_result else None
                
                # Install binary
                success = installer.install_binary(
                    binary_path=binary_path,
                    app_name=app_name,
                    version=version,
                    source_url=source_url,
                    platform=platform,
                )
                installed_version = version
                install_platform = platform
                
                # Install documentation if source was downloaded
                if success and source_path:
                    installer.install_doc_files(source_path, app_name)
        
        if not success:
            # Download source
            source_result = fetcher.download_app_directory(app_name, edge=edge_mode)
            if not source_result or not source_result[0]:
                logger.error(f"Failed to download {app_name}")
                overall_success = False
                continue
            
            source_path, version = source_result
            
            # Install as script if requested or no Bazel
            if script_mode:
                logger.info("Installing as Python script (no compilation)")
                success = install_as_script(source_path, app_name, version, source_url)
                installed_version = version
                install_platform = "script"
            else:
                # Check if Bazel is available
                bazel = shutil.which("bazelisk") or shutil.which("bazel")
                if not bazel:
                    logger.error("No release binary found; Bazel required for building")
                    logger.info("Bazel not found. Install as script instead?")
                    
                    # Prompt user
                    try:
                        response = input("Install as script? [y/N]: ").strip().lower()
                        if response in ('y', 'yes'):
                            success = install_as_script(source_path, app_name, version, source_url)
                            installed_version = version
                            install_platform = "script"
                            # Add PATH for pget install if script
                            if app_name == "pget":
                                ensure_path_in_shell()
                                logger.info("Added ~/.pget/bin to PATH. Open a new shell to use 'pget'.")
                            overall_success = overall_success and success
                            continue
                    except (KeyboardInterrupt, EOFError):
                        pass
                    
                    logger.error("Installation cancelled")
                    logger.info(f"Install Bazel or use: pget install --script {app_name}")
                    overall_success = False
                    continue
                
                # Build with Bazel
                logger.info("No release binary found; building with Bazel+Nuitka")
                success = installer.install_with_bazel(
                    source_path=source_path,
                    app_name=app_name,
                    version=version,
                    source_url=source_url,
                    platform=platform,
                )
                installed_version = version
                install_platform = platform
        
        # Add PATH for pget install
        if app_name == "pget" and success:
            ensure_path_in_shell()
            logger.info("Added ~/.pget/bin to PATH. Open a new shell to use 'pget'.")
        
        overall_success = overall_success and success
    
    return overall_success

