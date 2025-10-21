import argparse
import sys
from typing import List

from .core import (
    GITHUB_ORG,
    create_python_wrapper,
    download_repo_zip,
    extract_zip_to_app_dir,
    list_installed_apps,
)


def _cmd_install(app: str) -> int:
    ref, zip_bytes = download_repo_zip(GITHUB_ORG, app)
    extract_zip_to_app_dir(app, zip_bytes)
    create_python_wrapper(app)
    print(f"Installed {app} from {GITHUB_ORG}/{app}@{ref}")
    print("Ensure ~/.pget/bin is on your PATH")
    return 0


def _cmd_remove(app: str) -> int:
    from .core import remove_app

    remove_app(app)
    print(f"Removed {app}")
    return 0


def _cmd_list(cloud: bool) -> int:
    if cloud:
        try:
            from .core import list_cloud_apps

            apps: List[str] = list_cloud_apps()
            for name in apps:
                print(name)
        except Exception as e:
            print(f"Failed to list cloud apps: {e}", file=sys.stderr)
            return 1
        return 0
    apps = list_installed_apps()
    for name in apps:
        print(name)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pget", description="Pure-Python package installer")
    sub = parser.add_subparsers(dest="command", required=True)

    p_install = sub.add_parser("install", help="Install an app")
    p_install.add_argument("app", help="App name to install (repo under org)")

    p_remove = sub.add_parser("remove", help="Remove an installed app")
    p_remove.add_argument("app", help="App name to remove")

    p_list = sub.add_parser("list", help="List installed apps or cloud apps with -u")
    p_list.add_argument("-u", "--upstream", action="store_true", help="List apps available in cloud")

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "install":
        return _cmd_install(args.app)
    if args.command == "remove":
        return _cmd_remove(args.app)
    if args.command == "list":
        return _cmd_list(bool(args.upstream))
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


