#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import json
import urllib.error
import urllib.request
from ..core.config import PYNOSAUR_ORG, GITHUB_API, IGNORED_REPOS
from ..utils.logger import get_logger


def run(args):
    """Search for packages in pynosaur organization.
    
    Usage: pget search [query]
    """
    logger = get_logger()
    
    org = PYNOSAUR_ORG
    api_base = GITHUB_API
    
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
    
    if not repos:
        logger.info(f"No packages found matching '{query}'")
        return True
    
    print(f"{'Name':<20} {'Description':<60}")
    
    for repo in sorted(repos, key=lambda r: r["name"]):
        name = repo["name"]
        if name in IGNORED_REPOS:
            continue
        description = repo.get("description", "") or ""
        
        if len(description) > 57:
            description = description[:57] + "..."
        
        print(f"{name:<20} {description:<60}")
    
    return True

