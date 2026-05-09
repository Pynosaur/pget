#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-01-03

from ..core.config import PYNOSAUR_ORG, GITHUB_API
from ..core.fetcher import GitHubFetcher
from ..utils.logger import get_logger


def run(args):
    """List available versions for a package.

    Usage: pget versions <app_name>
    """
    if not args:
        logger = get_logger()
        logger.error("Usage: pget versions <app_name>")
        return False

    app_name = args[0]
    logger = get_logger()
    fetcher = GitHubFetcher()

    url = (
        f"{GITHUB_API}/repos/{PYNOSAUR_ORG}"
        f"/{app_name}/releases?per_page=100"
    )
    releases = fetcher.fetch_json(url)

    if releases is None:
        logger.error(f"Package '{app_name}' not found or network error")
        return False

    if not releases:
        logger.info(f"No releases found for {app_name}")
        return True

    print(f"Available versions for {app_name}:")
    print()

    for release in releases:
        tag = release.get("tag_name", "")
        name = release.get("name", "")
        published = release.get("published_at", "")[:10]  # YYYY-MM-DD
        is_latest = release.get("id") == releases[0].get("id")

        latest_mark = " (latest)" if is_latest else ""
        print(f"  {tag:<15} {published}  {name}{latest_mark}")

    print()
    print(f"Install specific version: pget install {app_name}@<version>")
    print(
        f"Example: pget install "
        f"{app_name}@{releases[0].get('tag_name', '').lstrip('v')}"
    )

    return True

