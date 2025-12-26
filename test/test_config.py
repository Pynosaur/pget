#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import PYNOSAUR_ORG, GITHUB_API, GITHUB_RAW


class TestConfig(unittest.TestCase):
    """Test cases for configuration constants."""
    
    def test_constants(self):
        """Test configuration constants."""
        self.assertEqual(PYNOSAUR_ORG, 'pynosaur', "PYNOSAUR_ORG should be 'pynosaur'")
        self.assertEqual(GITHUB_API, 'https://api.github.com', "GITHUB_API should be GitHub API URL")
        self.assertEqual(GITHUB_RAW, 'https://raw.githubusercontent.com', "GITHUB_RAW should be GitHub raw URL")


if __name__ == '__main__':
    unittest.main()

