#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2025-12-24

import sys
import traceback
from pathlib import Path

# Allow running both as module (`python -m app.main`) and as script (`python app/main.py`)
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    __package__ = "app"

from app.commands import install, remove, update, search
from app.commands import list as list_cmd
from app.utils.logger import get_logger, set_verbose
from app.utils.paths import PGET_BIN
from app.utils.doc_reader import read_app_doc, get_field, get_list_field
from app import __version__


COMMANDS = {
    'install': install.run,
    'remove': remove.run,
    'list': list_cmd.run,
    'update': update.run,
    'search': search.run,
}


def print_help():
    """Print help message from documentation."""
    doc = read_app_doc("pget")
    
    if not doc:
        print("pget - Pure Python package manager for pynosaur")
        print("Run with --help for more information")
        return
    
    # Header
    print(f"{get_field(doc, 'NAME', 'pget')} - {get_field(doc, 'DESCRIPTION')}")
    print()
    
    # Usage section
    _print_section("USAGE", get_list_field(doc, 'USAGE'))
    
    # Commands section
    _print_section("COMMANDS", get_list_field(doc, 'COMMANDS'))
    
    # Options section
    _print_section("OPTIONS", get_list_field(doc, 'OPTIONS'))
    
    # Installation
    print("INSTALLATION:")
    print(f"    Packages are installed to: {PGET_BIN}")
    print(f"    Add this directory to your PATH to use installed apps")
    print()
    
    # Examples section
    _print_section("EXAMPLES", get_list_field(doc, 'EXAMPLES'))


def _print_section(title, items):
    """Print a documentation section with items."""
    if not items:
        return
    print(f"{title}:")
    for item in items:
        print(f"    {item}")
    print()


def print_version():
    """Print version information from documentation."""
    doc = read_app_doc("pget")
    version = get_field(doc, 'VERSION', __version__)
    name = get_field(doc, 'NAME', 'pget')
    print(f"{name} version {version}")


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]
    
    # Handle no arguments
    if not args:
        print_help()
        return 0
    
    # Handle global options
    if args[0] in ('-h', '--help', 'help'):
        print_help()
        return 0
    
    if args[0] in ('--version', '-v'):
        print_version()
        return 0
    
    # Check for verbose flag
    if '--verbose' in args:
        set_verbose(True)
        args = [a for a in args if a != '--verbose']
    
    # Check for edge flag globally (pass through to install command)
    edge_mode = False
    if '--edge' in args:
        edge_mode = True
        args = [a for a in args if a != '--edge']
    
    # Check for script flag globally (pass through to install command)
    script_mode = False
    if '--script' in args:
        script_mode = True
        args = [a for a in args if a != '--script']
    
    # Check for build flag globally (pass through to install command)
    build_mode = False
    if '--build' in args:
        build_mode = True
        args = [a for a in args if a != '--build']
    
    # Get command
    if not args:
        print_help()
        return 0
    
    command = args[0]
    command_args = args[1:]
    
    # Re-add command-specific flags to command_args if they were present
    if command in ('install', 'update'):
        if edge_mode:
            command_args = ['--edge'] + command_args
        if script_mode:
            command_args = ['--script'] + command_args
        if build_mode:
            command_args = ['--build'] + command_args
    
    # Execute command
    if command in COMMANDS:
        try:
            success = COMMANDS[command](command_args)
            return 0 if success else 1
        except KeyboardInterrupt:
            logger = get_logger()
            logger.warning("Operation cancelled")
            return 130
        except Exception as e:
            logger = get_logger()
            logger.error(f"Unexpected error: {e}")
            if get_logger().verbose:
                traceback.print_exc()
            return 1
    else:
        logger = get_logger()
        logger.error(f"Unknown command: {command}")
        logger.info(f"Did you mean: pget install {command}?")
        return 1


if __name__ == "__main__":
    sys.exit(main())

