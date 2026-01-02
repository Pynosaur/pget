#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.paths import PGET_BIN, get_binary_path, get_cache_path


class TestPaths(unittest.TestCase):
    """Test cases for path utilities."""
    
    def test_pget_bin(self):
        """Test PGET_BIN path."""
        expected = Path.home() / ".pget" / "bin"
        self.assertEqual(PGET_BIN, expected, "PGET_BIN should point to ~/.pget/bin")
    
    def test_binary_path(self):
        """Test binary path generation."""
        path = get_binary_path("testapp")
        expected = PGET_BIN / "testapp"
        self.assertEqual(path, expected, "Binary path should be PGET_BIN/app_name")
    
    def test_cache_path(self):
        """Test cache path generation (temp directory)."""
        path = get_cache_path("testapp", "testfile")
        path_str = str(path)
        self.assertIn("testapp", path_str, "Cache path should contain app name")
        self.assertIn("testfile", path_str, "Cache path should contain filename")


if __name__ == '__main__':
    unittest.main()

