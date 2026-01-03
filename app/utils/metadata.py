#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import json
import re
from pathlib import Path
from .paths import get_doc_dir, get_app_dir


def get_metadata_file(app_name):
    """Get path to app's metadata file in the app root directory."""
    return get_app_dir(app_name) / ".pget-metadata.json"


def save_package_info(app_name, version, source_url=None, platform=None):
    """Save package installation metadata."""
    metadata_file = get_metadata_file(app_name)
    metadata = {
        'version': version,
        'source_url': source_url,
        'platform': platform,
    }
    
    try:
        # Ensure doc directory exists
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with metadata_file.open('w') as f:
            json.dump(metadata, f, indent=2)
    except OSError:
        # Best effort; don't crash
        pass


def get_package_info(app_name):
    """Get package installation metadata."""
    metadata_file = get_metadata_file(app_name)
    
    if not metadata_file.exists():
        return None
    
    try:
        with metadata_file.open('r') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def get_package_version(app_name):
    """Get installed package version from metadata or doc file."""
    # Try metadata file first (more reliable for binary installs)
    pkg_info = get_package_info(app_name)
    if pkg_info and 'version' in pkg_info:
        version = pkg_info['version']
        # Strip 'v' prefix if present
        if version and version.startswith('v'):
            return version[1:]
        return version
    
    # Fallback to doc file
    doc_dir = get_doc_dir(app_name)
    doc_file = doc_dir / f"{app_name}.yaml"
    
    if not doc_file.exists():
        return 'unknown'
    
    try:
        content = doc_file.read_text()
        # Extract VERSION from YAML doc
        match = re.search(r'^VERSION:\s*"([^"]+)"', content, re.MULTILINE)
        if match:
            return match.group(1)
    except (OSError, UnicodeDecodeError):
        pass
    
    return 'unknown'


def remove_package_info(app_name):
    """Remove package metadata."""
    metadata_file = get_metadata_file(app_name)
    if metadata_file.exists():
        try:
            metadata_file.unlink()
        except OSError:
            pass

