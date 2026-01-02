#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import sys


class Logger:
    """Simple logger for pget."""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
    
    def info(self, message):
        """Print info message."""
        print(f"[INFO] {message}")
    
    def success(self, message):
        """Print success message."""
        print(f"[OK] {message}")
    
    def error(self, message):
        """Print error message."""
        print(f"[ERROR] {message}", file=sys.stderr)
    
    def warning(self, message):
        """Print warning message."""
        print(f"[WARN] {message}")
    
    def debug(self, message):
        """Print debug message (only in verbose mode)."""
        if self.verbose:
            print(f"[DEBUG] {message}")
    
    def progress(self, message):
        """Print progress message."""
        if self.verbose:
            print(f"[PROGRESS] {message}")


# Global logger instance
_logger = Logger()


def get_logger():
    """Get global logger instance."""
    return _logger


def set_verbose(verbose):
    """Set verbose mode."""
    _logger.verbose = verbose

