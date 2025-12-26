#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import sys
import platform


def get_os():
    """Get operating system name."""
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        return system


def get_arch():
    """Get system architecture."""
    machine = platform.machine().lower()
    
    # Normalize architecture names
    if machine in ("x86_64", "amd64"):
        return "x86_64"
    elif machine in ("arm64", "aarch64"):
        return "arm64"
    elif machine in ("i386", "i686"):
        return "i386"
    else:
        return machine


def get_platform_string():
    """Get platform string in format: os-arch (e.g., darwin-arm64)."""
    return f"{get_os()}-{get_arch()}"


def get_python_version():
    """Get Python version as string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

