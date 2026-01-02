#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import shutil
import stat
import subprocess
from pathlib import Path
from ..utils.paths import (
    get_binary_path,
    find_existing_binary,
    get_doc_dir,
    get_app_dir,
    get_temp_cache_dir,
    ensure_dirs,
    ensure_path_in_shell,
)
from ..core.script_installer import PGET_SCRIPTS, uninstall_script
from ..utils.logger import get_logger
from ..utils.metadata import save_package_info, get_package_version, remove_package_info


class Installer:
    """Handles package installation."""
    
    def __init__(self):
        self.logger = get_logger()
        ensure_dirs()

    def install_doc_files(self, source_path, app_name):
        """Install app documentation files to helpers/<name>/doc/."""
        doc_source = source_path / "doc"
        if not doc_source.exists() or not doc_source.is_dir():
            self.logger.debug(f"No doc directory found for {app_name}")
            return
        
        # Ensure helper directory exists
        app_dir = get_app_dir(app_name)
        app_dir.mkdir(parents=True, exist_ok=True)
        
        doc_dest = get_doc_dir(app_name)
        
        # Remove old docs if they exist
        if doc_dest.exists():
            shutil.rmtree(doc_dest)
        
        # Copy doc directory
        shutil.copytree(doc_source, doc_dest)
        self.logger.debug(f"Installed documentation for {app_name}")
    
    def install_binary(self, binary_path, app_name, version, source_url, platform):
        """Install binary to ~/.pget/bin."""
        dest = get_binary_path(app_name)
        
        self.logger.progress(f"Installing {app_name} to {dest}")
        
        # Copy binary to bin directory
        shutil.copy(binary_path, dest)
        
        # Make executable
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        
        # Save metadata
        save_package_info(app_name, version, source_url, platform)
        
        self.logger.success(f"{app_name} installed successfully")
        ensure_path_in_shell()
        return True

    def install_with_bazel(self, source_path, app_name, version, source_url, platform):
        """Build and install using Bazel (required when no release binary)."""
        module_bazel = source_path / "MODULE.bazel"
        build_file = source_path / "BUILD"
        if not module_bazel.exists() and not build_file.exists():
            self.logger.error("Bazel build requested but MODULE.bazel/BUILD not found in source")
            return False

        bazel = shutil.which("bazelisk") or shutil.which("bazel")
        if not bazel:
            self.logger.error("Bazel is required but not found. Please install Bazel (or bazelisk) and retry.")
            return False

        target = f"//:{app_name}_bin"
        self.logger.info(f"Building {app_name} with Bazel+Nuitka ({target})")
        self.logger.info("This may take several minutes...")

        try:
            # Clean bazel cache to ensure fresh build
            self.logger.debug("Cleaning bazel cache for fresh build")
            subprocess.run(
                [bazel, "clean"],
                cwd=source_path,
                check=False,  # Don't fail if clean fails
                capture_output=True,
            )
            
            subprocess.run(
                [bazel, "build", target],
                cwd=source_path,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Bazel build failed with exit code {e.returncode}")
            return False

        built_path = source_path / "bazel-bin" / app_name
        
        if not built_path.exists():
            self.logger.error(f"Bazel artifact not found: {built_path}")
            return False

        dest = get_binary_path(app_name)
        
        self.logger.progress(f"Installing {app_name} to {dest}")
        shutil.copy(built_path, dest)
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        
        # Install documentation
        self.install_doc_files(source_path, app_name)
        
        # Save metadata
        save_package_info(app_name, version, source_url, platform)

        self.logger.success(f"{app_name} installed successfully (bazel build)")
        ensure_path_in_shell()
        return True
    
    def uninstall(self, app_name):
        """Uninstall a package - removes binary, helper directory, and temp cache."""
        binary = find_existing_binary(app_name)
        if not binary:
            self.logger.error(f"{app_name} is not installed")
            return False
        
        self.logger.progress(f"Uninstalling {app_name}")
        binary.unlink()
        
        # Remove entire helper directory (doc, data, config, cache, metadata)
        app_dir = get_app_dir(app_name)
        if app_dir.exists():
            shutil.rmtree(app_dir)
            self.logger.debug(f"Removed helper directory: {app_dir}")
        
        # Remove script directory if installed as script
        uninstall_script(app_name)
        
        # Clear temp download cache to prevent stale versions
        temp_cache = get_temp_cache_dir(app_name)
        if temp_cache.exists():
            shutil.rmtree(temp_cache)
            self.logger.debug(f"Cleared download cache: {temp_cache}")
        
        self.logger.success(f"{app_name} uninstalled successfully")
        return True
    
    def is_installed(self, app_name):
        """Check if package is installed."""
        return find_existing_binary(app_name) is not None
    
    def get_installed_version(self, app_name):
        """Get version of installed package."""
        return get_package_version(app_name)

