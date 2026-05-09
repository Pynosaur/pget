#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

from ..core.config import PYNOSAUR_ORG, GITHUB_API, GITHUB_RAW
from ..core.fetcher import GitHubFetcher
from ..utils.logger import get_logger


def run(args):
    """Search for packages in pynosaur organization.

    Usage: pget search [query]
    """
    logger = get_logger()
    fetcher = GitHubFetcher()

    url = f"{GITHUB_API}/orgs/{PYNOSAUR_ORG}/repos?per_page=100"
    repos = fetcher.fetch_json(url)

    if repos is None:
        logger.error("Failed to fetch packages")
        return False

    if not repos:
        logger.info("No packages found")
        return True

    query = args[0].lower() if args else None

    if query:
        repos = [
            r for r in repos
            if query in r["name"].lower()
            or query in r.get("description", "").lower()
        ]

    installable_repos = []
    for repo in repos:
        marker_url = (
            f"{GITHUB_RAW}/{PYNOSAUR_ORG}"
            f"/{repo['name']}/main/.program"
        )
        if fetcher.url_exists(marker_url):
            installable_repos.append(repo)

    if not installable_repos:
        logger.info(
            f"No installable packages found{(' matching ' + query if query else '')}",
        )
        return True

    print(f"{'Name':<20} {'Description':<60}")

    for repo in sorted(installable_repos, key=lambda r: r["name"]):
        name = repo["name"]
        description = repo.get("description", "") or ""

        if len(description) > 57:
            description = description[:57] + "..."

        print(f"{name:<20} {description:<60}")

    return True

