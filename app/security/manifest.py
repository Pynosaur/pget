#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Release manifest validation utilities."""

import hashlib
import json
import re
from pathlib import Path

from ..utils.logger import get_logger
from .pgp import PGPError, verify_detached_signature

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class ManifestError(RuntimeError):
    """Raised when manifest validation fails."""


def sha256_file(path: Path) -> str:
    """Compute SHA256 for a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_manifest_schema(manifest: dict):
    if not isinstance(manifest, dict):
        raise ManifestError("Manifest is not an object")

    assets = manifest.get("assets")
    if not isinstance(assets, dict) or not assets:
        raise ManifestError("Manifest missing 'assets' map")

    for name, digest in assets.items():
        if not isinstance(name, str):
            raise ManifestError("Manifest asset name is not a string")
        if not isinstance(digest, str) or not SHA256_RE.match(digest):
            raise ManifestError(f"Manifest asset '{name}' has invalid sha256")


def verify_manifest(manifest_path: Path, signature_path: Path):
    """
    Verify manifest signature and schema.

    Returns:
        manifest (dict), signer_fingerprint (str)
    Raises:
        ManifestError / PGPError on failure.
    """
    fingerprint = verify_detached_signature(manifest_path, signature_path)

    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception as exc:
        raise ManifestError(f"Failed to parse manifest: {exc}") from exc

    _validate_manifest_schema(manifest)
    return manifest, fingerprint


def ensure_asset_checksum(manifest: dict, asset_name: str, file_path: Path):
    """
    Validate the sha256 of a downloaded asset against the manifest.

    Raises ManifestError on mismatch or missing entry.
    """
    logger = get_logger()

    assets = manifest.get("assets", {})
    expected = assets.get(asset_name)
    if not expected:
        raise ManifestError(f"Asset '{asset_name}' missing from manifest")

    actual = sha256_file(file_path)
    if actual != expected:
        logger.error(f"Checksum mismatch for {asset_name}: expected {expected}, got {actual}")
        raise ManifestError(f"Checksum mismatch for {asset_name}")

    logger.debug(f"Checksum verified for {asset_name} ({actual})")




