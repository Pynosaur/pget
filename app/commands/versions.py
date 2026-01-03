#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-01-03

import json
import urllib.request
import urllib.error
from ..core.config import PYNOSAUR_ORG, GITHUB_API
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
    
    org = PYNOSAUR_ORG
    api_base = GITHUB_API
    
    # Get all releases for the app
    url = f"{api_base}/repos/{org}/{app_name}/releases?per_page=100"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            releases = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.error(f"Package '{app_name}' not found")
            return False
        logger.error(f"Failed to fetch releases: {e}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"Network error: {e.reason}")
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
    print(f"Example: pget install {app_name}@{releases[0].get('tag_name', '').lstrip('v')}")
    
    return True

