#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PGP verification helpers for pget.

We rely on the system `gpg` binary (OpenPGP) and pinned public keys that ship
with pget. Verification is done in an isolated keyring built at runtime from
those pinned keys, so the user's default keyring is never touched.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from ..utils.logger import get_logger

TRUSTED_KEYS_DIR = Path(__file__).parent / "keys"


class PGPError(RuntimeError):
    """Raised when PGP verification fails."""


def _require_gpg():
    gpg = shutil.which("gpg")
    if not gpg:
        raise PGPError("gpg is required for signature verification but was not found in PATH")
    return gpg


def _load_trusted_keys():
    """Return list of trusted key file paths (.asc) bundled with pget."""
    if not TRUSTED_KEYS_DIR.exists():
        raise PGPError(f"Trusted keys directory missing: {TRUSTED_KEYS_DIR}")
    keys = [p for p in TRUSTED_KEYS_DIR.glob("*.asc") if p.is_file()]
    if not keys:
        raise PGPError(f"No trusted public keys found in {TRUSTED_KEYS_DIR}")
    return keys


def verify_detached_signature(data_path: Path, signature_path: Path):
    """
    Verify a detached signature using the bundled trusted keys.

    Returns:
        fingerprint (str): the validated key fingerprint.
    Raises:
        PGPError if verification fails.
    """
    logger = get_logger()
    gpg = _require_gpg()
    keys = _load_trusted_keys()

    with tempfile.TemporaryDirectory(prefix="pget-gpg-") as temp_dir:
        keyring = Path(temp_dir) / "trusted.gpg"

        # Import trusted keys into isolated keyring
        for key_file in keys:
            try:
                subprocess.run(
                    [
                        gpg,
                        "--batch",
                        "--no-tty",
                        "--no-default-keyring",
                        "--keyring",
                        str(keyring),
                        "--import",
                        str(key_file),
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.CalledProcessError as exc:
                raise PGPError(f"Failed to import trusted key {key_file.name}: {exc}") from exc

        # Verify signature; capture status lines for fingerprint extraction
        proc = subprocess.run(
            [
                gpg,
                "--batch",
                "--no-tty",
                "--status-fd",
                "1",
                "--no-default-keyring",
                "--keyring",
                str(keyring),
                "--verify",
                str(signature_path),
                str(data_path),
            ],
            text=True,
            capture_output=True,
        )

        status_output = proc.stdout or ""
        if proc.returncode != 0:
            logger.debug(f"gpg verify stderr: {proc.stderr}")
            raise PGPError("Signature verification failed (gpg returned non-zero)")

        # Extract fingerprint from VALIDSIG line
        fingerprint = None
        for line in status_output.splitlines():
            # Example: [GNUPG:] VALIDSIG <fingerprint> <other fields>
            if line.startswith("[GNUPG:] VALIDSIG "):
                parts = line.split()
                if len(parts) >= 3:
                    fingerprint = parts[2]
                    break

        if not fingerprint:
            raise PGPError("Signature verified but fingerprint could not be determined")

        return fingerprint




