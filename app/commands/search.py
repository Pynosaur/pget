#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import json
import urllib.error
import urllib.request
from ..core.config import PYNOSAUR_ORG, GITHUB_API, GITHUB_RAW
from ..utils.logger import get_logger


def _has_program_marker(org, repo_name, api_base, raw_base):
    """Check if repo has .program marker file."""
    # Check via raw.githubusercontent.com (faster, no API rate limit)
    url = f"{raw_base}/{org}/{repo_name}/main/.program"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except (urllib.error.HTTPError, urllib.error.URLError):
        return False


def run(args):
    """Search for packages in pynosaur organization.
    
    Usage: pget search [query]
    """
    logger = get_logger()
    
    org = PYNOSAUR_ORG
    api_base = GITHUB_API
    raw_base = GITHUB_RAW
    
    # List all repos in pynosaur org
    url = f"{api_base}/orgs/{org}/repos?per_page=100"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            repos = json.loads(response.read().decode())
    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch packages: {e.reason}")
        return False
    
    if not repos:
        logger.info("No packages found")
        return True
    
    # Filter by query if provided
    query = args[0].lower() if args else None
    
    if query:
        repos = [r for r in repos if query in r["name"].lower() or 
                 query in r.get("description", "").lower()]
    
    # Filter repos with .program marker
    installable_repos = []
    for repo in repos:
        if _has_program_marker(org, repo["name"], api_base, raw_base):
            installable_repos.append(repo)
    
    if not installable_repos:
        logger.info(f"No installable packages found{' matching ' + query if query else ''}")
        return True
    
    print(f"{'Name':<20} {'Description':<60}")
    
    for repo in sorted(installable_repos, key=lambda r: r["name"]):
        name = repo["name"]
        description = repo.get("description", "") or ""
        
        if len(description) > 57:
            description = description[:57] + "..."
        
        print(f"{name:<20} {description:<60}")
    
    return True

