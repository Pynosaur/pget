#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-25

"""
Lightweight YAML parser for pget app documentation.
No external dependencies - uses only Python standard library.
"""

import re
import sys
from pathlib import Path


def read_app_doc(app_name):
    """Read app documentation from bundled YAML file.
    
    Searches in order:
    1. Nuitka onefile extraction dir (sys._MEIPASS/doc/)
    2. Source repository (../../doc/)
    3. Relative to current directory (doc/)
    
    Returns:
        dict: Parsed YAML with ALL CAPS keys, or {} if not found
    """
    search_paths = [
        Path(__file__).parent.parent.parent / "doc" / f"{app_name}.yaml",  # Source repo
        Path("doc") / f"{app_name}.yaml",  # Relative (bundled)
    ]
    
    # Nuitka onefile bundles files in a temp directory
    if hasattr(sys, '_MEIPASS'):
        search_paths.insert(0, Path(sys._MEIPASS) / "doc" / f"{app_name}.yaml")
    
    for path in search_paths:
        if path.exists():
            try:
                return parse_yaml(path.read_text())
            except (OSError, UnicodeDecodeError):
                continue
    
    return {}


def parse_yaml(content):
    """Parse simple YAML with ALL CAPS keys.
    
    Supports:
    - Key: value
    - Key: > (multiline)
    - Key:
        - list
        - items
    
    Args:
        content: YAML string content
        
    Returns:
        dict: Parsed YAML with original list structures preserved
    """
    doc = {}
    current_key = None
    current_list = None
    multiline_text = None
    
    for line in content.split('\n'):
        stripped = line.strip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue
        
        # Match KEY: value pattern
        key_match = re.match(r'^([A-Z_]+):\s*(.*)$', line)
        if key_match:
            # Save previous key
            _save_current(doc, current_key, current_list, multiline_text)
            
            current_key = key_match.group(1)
            value = key_match.group(2).strip()
            
            if value == '>':
                # Multiline string mode
                multiline_text = []
                current_list = None
            elif value:
                # Single value
                doc[current_key] = value.strip('"').strip("'")
                current_key = None
                current_list = None
                multiline_text = None
            else:
                # List mode (values on next lines)
                current_list = []
                multiline_text = None
        
        # Match list item (- value)
        elif stripped.startswith('-') and current_key:
            if current_list is None:
                current_list = []
            item = stripped[1:].strip().strip('"').strip("'")
            current_list.append(item)
        
        # Multiline continuation (indented text)
        elif multiline_text is not None and line.startswith('  '):
            multiline_text.append(stripped)
    
    # Save final key
    _save_current(doc, current_key, current_list, multiline_text)
    
    return doc


def _save_current(doc, key, list_val, multiline_val):
    """Helper to save current key-value pair."""
    if key is None:
        return
    
    if multiline_val is not None:
        doc[key] = ' '.join(multiline_val)
    elif list_val is not None:
        doc[key] = list_val
    elif key not in doc:
        doc[key] = ''


def get_field(doc, field, default=''):
    """Safely get field from doc with default."""
    return doc.get(field, default)


def get_list_field(doc, field):
    """Get field as list, converting if necessary."""
    value = doc.get(field, [])
    return value if isinstance(value, list) else [value] if value else []
