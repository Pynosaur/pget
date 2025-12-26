#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pget Helper - Utility for apps to access their pget directories

Apps can copy this file or implement the same logic to access their
data, config, and cache directories within the pget ecosystem.

Example usage in your app:
    from pget_helper import PgetApp
    
    app = PgetApp("myapp")
    db_path = app.data_dir / "database.json"
    config_path = app.config_dir / "settings.json"
"""

from pathlib import Path
import sys


class PgetApp:
    """Helper class for pget apps to access their directories."""
    
    def __init__(self, app_name=None):
        """Initialize with app name (auto-detects if not provided)."""
        if app_name is None:
            # Try to infer from script name
            app_name = Path(sys.argv[0]).stem
        
        self.app_name = app_name
        self.pget_root = Path.home() / ".pget"
        self.app_root = self.pget_root / "helpers" / app_name
        
        # Standard directories
        self.data_dir = self.app_root / "data"
        self.config_dir = self.app_root / "config"
        self.cache_dir = self.app_root / "cache"
        self.doc_dir = self.app_root / "doc"
    
    def ensure_dirs(self, data=True, config=True, cache=True):
        """Create app directories as needed.
        
        Args:
            data: Create data directory (default: True)
            config: Create config directory (default: True)
            cache: Create cache directory (default: True)
        """
        if data:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        if config:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        if cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def clear_cache(self):
        """Clear the cache directory."""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_data_file(self, filename):
        """Get path to a file in the data directory."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / filename
    
    def get_config_file(self, filename):
        """Get path to a file in the config directory."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        return self.config_dir / filename
    
    def get_cache_file(self, filename):
        """Get path to a file in the cache directory."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir / filename


# Convenience function for simple usage
def get_app_dirs(app_name=None):
    """Get standard pget directory paths for an app.
    
    Returns:
        dict with keys: base, data, config, cache, doc
    """
    if app_name is None:
        app_name = Path(sys.argv[0]).stem
    
    base = Path.home() / ".pget" / "helpers" / app_name
    
    return {
        'base': base,
        'data': base / 'data',
        'config': base / 'config',
        'cache': base / 'cache',
        'doc': base / 'doc',
    }

