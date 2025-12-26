#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import json
import tarfile
import urllib.request
import urllib.error
from pathlib import Path
from ..utils.platform import get_platform_string
from ..utils.logger import get_logger
from ..utils.paths import get_cache_path, get_temp_cache_dir
from .config import PYNOSAUR_ORG, GITHUB_API, GITHUB_RAW


class GitHubFetcher:
    """Fetches packages from GitHub pynosaur organization."""
    
    def __init__(self):
        self.logger = get_logger()
        self.org = PYNOSAUR_ORG
        self.api_base = GITHUB_API
        self.raw_base = GITHUB_RAW
    
    def _api_request(self, url):
        """Make API request to GitHub."""
        try:
            req = urllib.request.Request(url)
            req.add_header('Accept', 'application/vnd.github.v3+json')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise
        except urllib.error.URLError as e:
            self.logger.error(f"Network error: {e.reason}")
            raise
    
    def _download_file(self, url, dest_path):
        """Download file from URL."""
        self.logger.debug(f"Downloading from {url}")
        
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                total_size = response.getheader('Content-Length')
                if total_size:
                    total_size = int(total_size)
                    size_mb = total_size / (1024 * 1024)
                    self.logger.info(f"Downloading {dest_path.name} ({size_mb:.1f} MB)")
                
                content = response.read()
                
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with dest_path.open('wb') as f:
                    f.write(content)
                
                self.logger.info(f"Downloaded {dest_path.name}")
                return dest_path
        except urllib.error.URLError as e:
            self.logger.error(f"Download failed: {e.reason}")
            return None
    
    def get_repo_info(self, app_name):
        """Get repository information."""
        url = f"{self.api_base}/repos/{self.org}/{app_name}"
        self.logger.debug(f"Fetching repo info: {url}")
        return self._api_request(url)
    
    def get_latest_release(self, app_name):
        """Get latest release information."""
        url = f"{self.api_base}/repos/{self.org}/{app_name}/releases/latest"
        self.logger.debug(f"Fetching latest release: {url}")
        return self._api_request(url)
    
    def download_binary(self, app_name, platform=None):
        """Download compiled binary for platform."""
        if platform is None:
            platform = get_platform_string()
        
        self.logger.progress(f"Looking for binary: {app_name}-{platform}")
        
        # Get latest release
        release = self.get_latest_release(app_name)
        if not release:
            self.logger.debug("No releases found")
            return None
        
        version = release.get("tag_name", "unknown")
        
        # Look for binary asset
        binary_name = f"{app_name}-{platform}"
        assets = release.get("assets", [])
        
        for asset in assets:
            if asset["name"] == binary_name:
                download_url = asset["browser_download_url"]
                cache_path = get_cache_path(app_name, binary_name)
                
                self.logger.progress(f"Downloading binary (version {version})")
                return self._download_file(download_url, cache_path), version
        
        self.logger.debug(f"No binary found for {platform}")
        return None, version
    
    def download_source(self, app_name, ref="main"):
        """Download source code archive."""
        self.logger.progress(f"Downloading source for {app_name}")
        
        # Download tarball
        url = f"{self.api_base}/repos/{self.org}/{app_name}/tarball/{ref}"
        cache_path = get_cache_path(app_name, f"{app_name}-{ref}.tar.gz")
        
        result = self._download_file(url, cache_path)
        if result:
            # For now, we'll return the tarball path
            # In future, we could extract and build with Nuitka
            return result, ref
        
        return None, None
    
    def download_app_directory(self, app_name, ref="main"):
        """Download full source tarball and extract."""
        tar_path, version = self.download_source(app_name, ref)
        if not tar_path:
            return None

        extract_root = get_temp_cache_dir(app_name) / "src"
        extract_root.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Extracting source code...")
        try:
            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(path=extract_root)
            self.logger.info("Extraction complete")
        except tarfile.TarError as e:
            self.logger.error(f"Failed to extract source: {e}")
            return None

        # GitHub tarball creates top-level dir like pynosaur-yday-<hash>
        # Pick first directory
        children = [p for p in extract_root.iterdir() if p.is_dir()]
        if not children:
            self.logger.error("Extracted archive is empty")
            return None

        return children[0], version
    
    def _download_directory(self, api_url, dest_dir):
        """Recursively download directory contents."""
        contents = self._api_request(api_url)
        if not contents:
            return
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for item in contents:
            if item["type"] == "file":
                file_url = item["download_url"]
                file_path = dest_dir / item["name"]
                self._download_file(file_url, file_path)
            elif item["type"] == "dir":
                self._download_directory(item["url"], dest_dir / item["name"])

