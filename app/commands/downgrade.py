#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-05-02

import json
import urllib.request
import urllib.error

from ..core.config import PYNOSAUR_ORG, GITHUB_API
from ..core.fetcher import GitHubFetcher
from ..core.installer import Installer
from ..utils.logger import get_logger
from ..utils.metadata import get_package_info


def _version_tuple(v):
    try:
        return tuple(int(x) for x in str(v).lstrip('v').split('.'))
    except (ValueError, AttributeError):
        return (0,)


def _list_older_versions(app_name, current_version):
    """Fetch and display versions older than the current installed version."""
    logger = get_logger()
    url = f"{GITHUB_API}/repos/{PYNOSAUR_ORG}/{app_name}/releases?per_page=100"

    try:
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        with urllib.request.urlopen(req, timeout=30) as response:
            releases = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.error(f"Package '{app_name}' not found")
        else:
            logger.error(f"Failed to fetch releases: {e}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"Network error: {e.reason}")
        return False

    current = _version_tuple(current_version)
    older = [
        r for r in releases
        if _version_tuple(r.get("tag_name", "")) < current
    ]

    if not older:
        logger.info(
            f"No older versions available for {app_name} "
            f"(current: {current_version})"
        )
        return True

    print(f"Installed version of {app_name}: {current_version}")
    print(f"Available older versions:")
    print()
    for release in older:
        tag = release.get("tag_name", "")
        published = release.get("published_at", "")[:10]
        name = release.get("name", "")
        print(f"  {tag:<15} {published}  {name}")
    print()
    print(f"Downgrade: pget downgrade {app_name}@<version>")
    example_tag = older[0].get("tag_name", "").lstrip("v")
    print(f"Example:   pget downgrade {app_name}@{example_tag}")
    return True


def run(args):
    """Downgrade one or more packages to a specific older version.

    Usage: pget downgrade <app>@<version> [app2@version2 ...]
            pget downgrade <app> <version>
    """
    if not args:
        logger = get_logger()
        logger.error("Usage: pget downgrade <app>@<version> [app2@version2 ...]")
        return False

    # Check for --no-verify-ssl flag
    no_verify_ssl = False
    if '--no-verify-ssl' in args:
        no_verify_ssl = True
        args = [a for a in args if a != '--no-verify-ssl']

    # Check for --script flag
    script_mode = False
    if '--script' in args:
        script_mode = True
        args = [a for a in args if a != '--script']

    # Parse app@version pairs; also accept two-arg form: pget downgrade app 0.1.4
    targets = []
    i = 0
    while i < len(args):
        part = args[i].strip()
        if '@' in part:
            app_name, version = part.split('@', 1)
            targets.append((app_name.strip(), version.strip()))
        elif i + 1 < len(args) and not args[i + 1].startswith('-'):
            # next arg looks like a version
            targets.append((part, args[i + 1].strip()))
            i += 1
        else:
            # No version specified — show available older versions
            logger = get_logger()
            installer = Installer()
            if not installer.is_installed(part):
                logger.error(f"{part} is not installed")
                return False
            current_version = installer.get_installed_version(part)
            return _list_older_versions(part, current_version)
        i += 1

    if not targets:
        logger = get_logger()
        logger.error("Usage: pget downgrade <app>@<version> [app2@version2 ...]")
        return False

    logger = get_logger()
    installer = Installer()
    fetcher = GitHubFetcher(verify_ssl=not no_verify_ssl)
    overall_success = True

    for app_name, target_version in targets:
        if not installer.is_installed(app_name):
            logger.error(f"{app_name} is not installed")
            overall_success = False
            continue

        current_version = installer.get_installed_version(app_name)

        if _version_tuple(target_version) >= _version_tuple(current_version):
            logger.error(
                f"{app_name} {target_version} is not older than the current version "
                f"({current_version})"
            )
            logger.info(
                f"Use 'pget update {app_name}' to upgrade, or "
                f"'pget install {app_name}@{target_version}' to reinstall same version"
            )
            overall_success = False
            continue

        logger.info(
            f"Downgrading {app_name} from {current_version} to {target_version}"
        )

        # For pget self-downgrade, honour existing install type
        effective_script = script_mode
        if app_name == 'pget' and not script_mode:
            pkg_info = get_package_info('pget')
            if pkg_info and pkg_info.get('platform') == 'script':
                effective_script = True

        installer.uninstall(app_name)

        from .install import run as install_run
        install_args = []
        if effective_script:
            install_args.append('--script')
        if no_verify_ssl:
            install_args.append('--no-verify-ssl')
        install_args.append(f"{app_name}@{target_version}")

        ok = install_run(install_args)
        if not ok:
            logger.error(f"Failed to downgrade {app_name} to {target_version}")
        overall_success = overall_success and ok

    return overall_success
