import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple


GITHUB_ORG = "Pynosaur"


def get_pget_home() -> Path:
    env_override = os.environ.get("PGET_HOME")
    if env_override:
        return Path(env_override).expanduser().resolve()
    return Path.home() / ".pget"


def get_apps_dir() -> Path:
    return get_pget_home() / "apps"


def get_bin_dir() -> Path:
    return get_pget_home() / "bin"


def ensure_base_dirs() -> None:
    get_apps_dir().mkdir(parents=True, exist_ok=True)
    get_bin_dir().mkdir(parents=True, exist_ok=True)


def get_app_dir(app_name: str) -> Path:
    return get_apps_dir() / app_name


def is_app_installed(app_name: str) -> bool:
    return get_app_dir(app_name).exists()


def _build_repo_zip_url(org: str, repo: str, ref: str) -> str:
    return f"https://github.com/{org}/{repo}/archive/refs/heads/{ref}.zip"


def _http_get(url: str, headers: Optional[dict] = None) -> Tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request) as response:
            return response.getcode(), response.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b""
    except urllib.error.URLError:
        return 0, b""


def download_repo_zip(org: str, repo: str, refs: Optional[List[str]] = None) -> Tuple[str, bytes]:
    candidate_refs = refs or ["main", "master"]
    for ref in candidate_refs:
        url = _build_repo_zip_url(org, repo, ref)
        status, data = _http_get(url, headers={"User-Agent": "pget/0.1"})
        if status == 200 and data:
            return ref, data
    raise RuntimeError(f"Failed to download {org}/{repo} zip for refs {candidate_refs}")


def extract_zip_to_app_dir(app_name: str, zip_bytes: bytes) -> Path:
    ensure_base_dirs()
    app_dir = get_app_dir(app_name)
    if app_dir.exists():
        shutil.rmtree(app_dir)
    app_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_zip = Path(tmpdir) / "repo.zip"
        tmp_extract = Path(tmpdir) / "extract"
        tmp_extract.mkdir(parents=True, exist_ok=True)
        tmp_zip.write_bytes(zip_bytes)
        with zipfile.ZipFile(tmp_zip) as zf:
            zf.extractall(tmp_extract)
        # GitHub zips contain a single top-level directory like repo-ref/
        entries = list(tmp_extract.iterdir())
        if not entries:
            raise RuntimeError("Empty archive")
        top = entries[0]
        if top.is_dir():
            for item in top.iterdir():
                dest = app_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
        else:
            shutil.copy2(top, app_dir / top.name)
    return app_dir


def create_python_wrapper(app_name: str) -> Path:
    ensure_base_dirs()
    app_dir = get_app_dir(app_name)
    if not app_dir.exists():
        raise RuntimeError(f"App not installed: {app_name}")
    bin_dir = get_bin_dir()
    wrapper_path = bin_dir / app_name
    python_code = _generate_wrapper_python(app_name)
    wrapper_path.write_text(python_code)
    wrapper_path.chmod(0o755)
    return wrapper_path


def remove_app(app_name: str) -> None:
    app_dir = get_app_dir(app_name)
    if app_dir.exists():
        shutil.rmtree(app_dir)
    wrapper_path = get_bin_dir() / app_name
    if wrapper_path.exists():
        wrapper_path.unlink()


def _generate_wrapper_python(app_name: str) -> str:
    lines: List[str] = []
    lines.append("#!/usr/bin/env python3")
    lines.append("import os, sys, importlib")
    lines.append("from pathlib import Path")
    lines.append("APP_NAME = %r" % app_name)
    lines.append("HOME = Path(os.environ.get('PGET_HOME', str(Path.home() / '.pget')))")
    lines.append("APP_DIR = HOME / 'apps' / APP_NAME")
    lines.append("sys.path.insert(0, str(APP_DIR))")
    lines.append("candidates = [")
    # Prefer explicit known entrypoints first
    lines.append("    (f'{APP_NAME}.app.cli', 'main'),")
    lines.append("    (f'{APP_NAME}.cli', 'main'),")
    lines.append("    ('cli', 'main'),")
    lines.append("    ('main', 'main'),")
    lines.append("]")
    lines.append("last_err = None")
    lines.append("for mod_name, func_name in candidates:")
    lines.append("    try:")
    lines.append("        mod = importlib.import_module(mod_name)")
    lines.append("        func = getattr(mod, func_name)")
    lines.append("        sys.exit(func())")
    lines.append("    except Exception as e:")
    lines.append("        last_err = e")
    lines.append("raise SystemExit(f'Could not find entrypoint for {APP_NAME}: {last_err}')")
    return "\n".join(lines) + "\n"


def list_installed_apps() -> List[str]:
    if not get_apps_dir().exists():
        return []
    return sorted([p.name for p in get_apps_dir().iterdir() if p.is_dir()])


def list_cloud_apps(org: str = GITHUB_ORG) -> List[str]:
    # Prefer GitHub API, fall back to empty list on failure
    api_url = f"https://api.github.com/orgs/{org}/repos?per_page=100&type=public"
    status, body = _http_get(api_url, headers={"User-Agent": "pget/0.1"})
    if status == 200 and body:
        try:
            data = json.loads(body.decode("utf-8"))
            names = [item.get("name", "") for item in data if isinstance(item, dict)]
            # Hide meta-repos like .github
            names = [n for n in names if n and not n.startswith('.')]
            return sorted(names)
        except Exception:
            return []
    return []


