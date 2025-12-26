#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.platform import get_os, get_arch, get_platform_string


class TestPlatform(unittest.TestCase):
    """Test cases for platform detection utilities."""
    
    def test_get_os(self):
        """Test OS detection."""
        os_name = get_os()
        valid_oses = ('darwin', 'linux', 'windows')
        self.assertIn(os_name, valid_oses, f"Unknown OS: {os_name}")
    
    def test_get_arch(self):
        """Test architecture detection."""
        arch = get_arch()
        valid_arches = ('x86_64', 'arm64', 'i386')
        self.assertIn(arch, valid_arches, f"Unknown architecture: {arch}")
    
    def test_get_platform_string(self):
        """Test platform string generation."""
        platform_str = get_platform_string()
        self.assertIn('-', platform_str, "Platform string should contain '-'")
        parts = platform_str.split('-')
        self.assertEqual(len(parts), 2, "Platform string should be 'os-arch'")


if __name__ == '__main__':
    unittest.main()

