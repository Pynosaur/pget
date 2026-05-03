#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import sys


class Logger:
    """Simple logger for pget."""

    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    RESET = "\033[0m"

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.command = ""
        self._color = sys.stderr.isatty()

    def set_command(self, command):
        """Set the active command name for log prefixes."""
        self.command = command

    def _prefix(self, color):
        if not self._color:
            return f"pget {self.command}: " if self.command else "pget: "
        cmd = f" {self.GREEN}{self.command}{self.RESET}" if self.command else ""
        return f"{color}pget{self.RESET}{cmd}: "

    def info(self, message):
        """Print info message."""
        print(f"{self._prefix(self.YELLOW)}{message}")

    def success(self, message):
        """Print success message."""
        print(f"{self._prefix(self.GREEN)}{message}")

    def error(self, message):
        print(f"{self._prefix(self.RED)}{message}", file=sys.stderr)

    def warning(self, message):
        print(f"{self._prefix(self.YELLOW)}{message}")

    def debug(self, message):
        """Print debug message (only in verbose mode)."""
        if self.verbose:
            print(f"{self._prefix(self.YELLOW)}{message}")

    def progress(self, message):
        """Print progress message."""
        if self.verbose:
            print(f"{self._prefix(self.YELLOW)}{message}")


# Global logger instance
_logger = Logger()


def get_logger():
    """Get global logger instance."""
    return _logger


def set_verbose(verbose):
    """Set verbose mode."""
    _logger.verbose = verbose

