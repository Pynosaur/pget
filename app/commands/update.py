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


def _version_tuple(v):
    """Parse a version string into a comparable tuple, e.g. '0.1.6' -> (0, 1, 6)."""
    try:
        return tuple(int(x) for x in str(v).lstrip('v').split('.'))
    except (ValueError, AttributeError):
        return (0,)


def update_pget_self(
    logger,
    installer,
    fetcher,
    edge_mode=False,
    script_mode=False,
    build_mode=False,
):
    """Update pget itself (special handling for self-update)."""
    from ..core.script_installer import install_as_script
    from ..utils.platform import get_platform_string
    from pathlib import Path

    from ..utils.metadata import get_package_info

    current_version = installer.get_installed_version('pget')
    current_binary = find_existing_binary('pget') or get_binary_path('pget')

    # If pget was installed as a script, always use script mode for self-update
    pkg_info = get_package_info('pget')
    if not script_mode and pkg_info and pkg_info.get('platform') == 'script':
        script_mode = True

    # Determine latest version
    if edge_mode:
        latest_version = "main"
        logger.info(
            f'Updating pget from {current_version} to latest main (--edge mode)',
        )
    else:
        release = fetcher.get_latest_release('pget')
        if not release:
            logger.error("Could not fetch latest pget release")
            logger.info(f"Current version: {current_version}")
            logger.info("Try: pget update --script pget")
            return False

        latest_version = release.get("tag_name", "").lstrip('v')

        if _version_tuple(latest_version) <= _version_tuple(current_version):
            logger.info(f"pget is already at the latest version ({current_version})")
            return True

        logger.info(f"Updating pget from {current_version} to {latest_version}")

    # For script mode, download source FIRST, then uninstall, then install from
    # the downloaded source. We can't use install_run because it resolves source
    # from __file__ which points to the (about to be deleted) script directory.
    if script_mode or not current_binary.exists():
        # Download new source before uninstalling
        version_to_download = None if edge_mode else latest_version
        source_result = fetcher.download_app_directory(
            'pget',
            edge=edge_mode,
            version=version_to_download,
        )
        if not source_result or not source_result[0]:
            logger.error("Failed to download pget source for update")
            return False

        source_path, _ = source_result

        # Now safe to uninstall
        installer.uninstall('pget')

        # Install from downloaded source
        ok = install_as_script(
            source_path,
            'pget',
            latest_version if not edge_mode else 'main',
            'https://github.com/pynosaur/pget',
        )
        if ok:
            from ..utils.paths import (
                ensure_path_in_shell, ensure_system_path,
                link_to_system_bin,
            )
            ensure_path_in_shell()
            ensure_system_path()
            link_to_system_bin('pget')
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
                    installer._sanitize_binary(current_binary)

                    # Update metadata
                    from ..utils.metadata import save_package_info
                    save_package_info(
                        'pget',
                        latest_version,
                        f'https://github.com/pynosaur/pget',
                        platform,
                    )

                    # Refresh helper docs
                    source_result = fetcher.download_app_directory(
                        'pget',
                        version=latest_version,
                    )
                    if source_result and source_result[0]:
                        installer.install_doc_files(
                            source_result[0], 'pget',
                        )

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
    source_result = fetcher.download_app_directory(
        'pget',
        edge=use_edge,
        version=version_to_download,
    )
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


def _get_installed_names():
    """Return sorted list of all installed package names."""
    from ..utils.paths import PGET_BIN
    from ..core.script_installer import PGET_SCRIPTS, LEGACY_SCRIPTS

    names = set()
    for script_dir in (PGET_SCRIPTS, LEGACY_SCRIPTS):
        if script_dir.exists():
            for f in script_dir.iterdir():
                if f.is_dir():
                    names.add(f.name)
    if PGET_BIN.exists():
        for f in PGET_BIN.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                if not f.name.endswith(('.old', '.bak')):
                    names.add(f.name)
    result = sorted(names)
    if 'pget' in result:
        result.remove('pget')
        result.append('pget')
    return result


def run(args):
    """Update one or more packages to the latest version.

    Usage: pget update [--script|--build] [--edge] <app1>[,app2...]
            pget update [--script|--build] [--edge] app1 app2 ...
            pget update --all
            pget update -a
    """
    if not args:
        logger = get_logger()
        logger.error(
            'Usage: pget update [--all|-a] [--script|--build] [--edge] '
            '<app_name>[,app2...]',
        )
        return False

    # Check for --all / -a flag
    all_mode = False
    if '--all' in args or '-a' in args:
        all_mode = True
        args = [a for a in args if a not in ('--all', '-a')]

    # Check for --edge flag
    edge_mode = False
    if '--edge' in args:
        edge_mode = True
        args = [a for a in args if a != '--edge']

    # Check for --script flag
    script_mode = False
    if '--script' in args:
        script_mode = True
        args = [a for a in args if a != '--script']

    # Check for --build flag
    build_mode = False
    if '--build' in args:
        build_mode = True
        args = [a for a in args if a != '--build']

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

    logger = get_logger()

    if all_mode:
        names = _get_installed_names()
        if not names:
            logger.info("No packages installed")
            return True
    else:
        names = _parse_names(args)
        if not names:
            logger.error(
                'Usage: pget update [--all|-a] [--script|--build] [--edge] '
                '[--no-verify-ssl] <app_name>[,app2...]'
            )
            return False

    installer = Installer()
    fetcher = GitHubFetcher(verify_ssl=not no_verify_ssl)
    overall = True

    for app_name in names:
        # Special handling for self-update
        if app_name == 'pget':
            ok = update_pget_self(
                logger,
                installer,
                fetcher,
                edge_mode=edge_mode,
                script_mode=script_mode,
                build_mode=build_mode,
            )
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
            logger.info(
                f'Updating {app_name} from {current_version} to latest main (--edge '
                f'mode)'
            )
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
                    version_match = re.search(
                        '^VERSION:\\s*"([^"]+)"',
                        content,
                        re.MULTILINE,
                    )
                    if version_match:
                        latest_version = version_match.group(1)
                        logger.debug(f"Found version in doc: {latest_version}")

        # Compare versions
        if not latest_version:
            logger.error(f"Could not determine latest version for {app_name}")
            logger.info(f"Current version: {current_version}")
            overall = False
            continue

        if _version_tuple(latest_version) <= _version_tuple(current_version):
            logger.info(
                f'{app_name} is already at the latest version ({current_version})',
            )
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

