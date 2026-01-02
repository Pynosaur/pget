# pget

**Pure Python package manager for the pynosaur ecosystem**

pget is a minimalist package manager for lightweight Python CLI tools. It installs standalone executables to `~/.pget/bin`, making it easy to distribute and install simple command-line utilities without pip or virtual environments.

```bash
pget install yday
```

## Table of Contents

- [What is pget?](#what-is-pget)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Features](#features)
- [Commands](#commands)
- [Example Apps](#example-apps)
- [Requirements](#requirements)
- [License](#license)
- [App Development Guidelines](#app-development-guidelines)

## What is pget?

pget is a package manager designed specifically for standalone Python CLI applications in the pynosaur ecosystem. Unlike pip which manages libraries and dependencies, pget focuses on distributing self-contained executable tools.

**Why pget?**

- No dependency conflicts - each app is a standalone binary compiled with Nuitka
- Works without pip, virtualenv, or conda
- Perfect for simple CLI utilities that do one thing well
- Automatically downloads pre-built binaries for your platform
- Falls back to building from source when needed
- Everything lives in `~/.pget/bin` (including pget itself) - clean and isolated

**Use Cases:**

- System utilities and CLI tools
- Developer productivity tools
- Simple data processing scripts
- Cross-platform command-line applications

## Installation

### Option 1: Clone and Run (Quick Start)

No build required - start using pget immediately:

```bash
git clone https://github.com/pynosaur/pget.git
cd pget
python app/main.py --help
```

With this option, use `python app/main.py` for all commands.

### Option 2: Build Standalone Binary (Recommended)

Build once, then use the `pget` command anywhere. Requires Bazel or Bazelisk:

```bash
git clone https://github.com/pynosaur/pget.git
cd pget
bazel build //:pget_bin
mkdir -p ~/.pget/bin
cp bazel-bin/pget ~/.pget/bin/
export PATH="$HOME/.pget/bin:$PATH"  # Add to your shell rc file
```

Now you can use `pget` directly from anywhere (instead of `python app/main.py`).

**Note:** The `~/.pget/bin` directory is where pget installs all apps, including itself. Make sure this directory is in your PATH.

## Quick Start

If running from source, use `python app/main.py`. If you built the standalone binary, use `pget` directly.

```bash
# Search for available packages
pget search

# Install an app (e.g., yday - prints current day of year)
pget install yday

# List installed packages
pget list

# Use the installed app
yday
# Output: 360

# Update an app
pget update yday

# Remove an app
pget remove yday
```

**Note:** If running from source without building, replace `pget` with `python app/main.py` in all commands above.

## Features

- **Pure Python** - No external dependencies, uses only standard library
- **Cross-platform** - Works on macOS, Linux, and Windows
- **Smart Installation** - Downloads pre-built binaries when available, builds from source as fallback
- **Simple CLI** - Familiar package manager commands (install, remove, list, update, search)
- **Self-contained** - Everything lives in `~/.pget/bin` (including pget itself), automatically added to your PATH
- **Standalone Binaries** - Apps compiled with Nuitka for fast startup and no runtime dependencies
- **System-aware installs** - Attempts system-wide install (`/usr/local/bin`) with sudo, falling back to user installs if not permitted

## Commands

**Note:** The examples below use `pget` (standalone binary). If running from source, use `python app/main.py` instead.

### install

Install a package from the pynosaur organization:

```bash
pget install <app_name>
```

Example output:
```
Installing yday
Looking for binary: yday-darwin-arm64
Downloading yday (2.1 MB)
Installing yday to /Users/username/.pget/bin/yday
yday installed successfully
```

### remove

Uninstall a previously installed package:

```bash
pget remove <app_name>
```

### list

Show all installed packages:

```bash
pget list
```

Example output:
```
Installed packages in /Users/username/.pget/bin:

  pget                 0.1.0
  yday                 0.1.0
```

### update

Update a package to the latest version:

```bash
pget update <app_name>
```

### search

Search for available packages in the pynosaur organization:

```bash
# List all packages
pget search

# Search with a query
pget search date
```

Example output:
```
Name                 Description
yday                 Prints the current day of the year (1-366)
pget                 Pure Python package manager for pynosaur ecosystem
```

### Global Options

- `-h, --help` - Show help message
- `-v, --version` - Show version information
- `--verbose` - Enable verbose output

## Example Apps

Apps currently available in the pynosaur ecosystem:

- **yday** - Display current day of year (1-366). Simple utility for date calculations.
- **pget** - The package manager itself. Demonstrates self-hosting capability.

To see all available apps, run:
```bash
pget search
```

## Requirements

- Python 3.6 or higher
- Internet connection (for downloading packages)
- Bazel or Bazelisk (optional, only needed for building from source when no binary is available)

**Platform Support:**
- macOS (ARM64 and x86_64)
- Linux (x86_64 and ARM64)
- Windows (x86_64)

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## App Development Guidelines

This section is for developers who want to create apps compatible with pget. Following these guidelines ensures your app can be easily installed and distributed through the pynosaur ecosystem.

### Repository Requirements

1. **GitHub Organization**: Apps must be in the `pynosaur` GitHub organization
2. **Repository Name**: Should match the app name (e.g., `yday`, `pget`)
3. **Standard Structure**: Must follow the directory structure:
   ```
   <app_name>/
   ├── app/
   │   ├── __init__.py
   │   └── main.py          # Main entry point
   ├── doc/
   │   └── <app_name>.yaml  # App metadata
   ├── test/
   │   └── test_*.py        # Test files
   ├── BUILD                # Bazel build file (required for source builds)
   ├── MODULE.bazel         # Bazel module file (required for source builds)
   └── README.md            # Documentation
   ```

### Code Requirements

#### Main Entry Point (`app/main.py`)

- **Shebang**: Must start with `#!/usr/bin/env python3`
- **Executable**: Should be directly runnable as a CLI tool
- **Standard Flags**: Should support:
  - `--help` or `-h`: Display help message
  - `--version` or `-v`: Display version information
- **Exit Codes**: Return proper exit codes (0 for success, non-zero for errors)
- **Module Support**: Should work both as:
  - Direct script: `python app/main.py`
  - Module: `python -m app.main`

#### Version Information

- Define `__version__` in `app/__init__.py`:
  ```python
  __version__ = "0.1.0"
  ```

#### Example Structure

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from app import __version__

def main():
    args = sys.argv[1:]
    
    if not args:
        # Default behavior
        return 0
    
    if args[0] in ("-h", "--help"):
        print("Usage: app_name [options]")
        return 0
    
    if args[0] in ("-v", "--version"):
        print(__version__)
        return 0
    
    # Your app logic here
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Build System (Bazel)

#### Required Files

1. **MODULE.bazel**: Bazel module configuration
   ```python
   module(
       name = "<app_name>",
       version = "0.1.0",
   )
   
   bazel_dep(name = "rules_python", version = "0.40.0")
   
   python = use_extension("@rules_python//python/extensions:python.bzl", "python")
   python.toolchain(python_version = "3.11")
   ```

2. **BUILD**: Bazel build rules
   ```python
   genrule(
       name = "<app_name>_bin",
       srcs = glob(["app/**/*.py"]),
       outs = ["<app_name>"],
       cmd = """
           /opt/homebrew/bin/nuitka \
               --onefile \
               --onefile-tempdir-spec=/tmp/nuitka-<app_name> \
               --no-progressbar \
               --assume-yes-for-downloads \
               --output-dir=$$(dirname $(location <app_name>)) \
               --output-filename=<app_name> \
               $(location app/main.py)
       """,
       local = 1,
       visibility = ["//visibility:public"],
   )
   ```

#### Build Target

- **Target Name**: Must be `//:<app_name>_bin`
- **Output**: Should produce a single executable binary named `<app_name>`
- **Compilation**: Uses Nuitka with `--onefile` flag for standalone binaries

### Binary Distribution

#### Release Binaries

For faster installation, provide pre-compiled binaries in GitHub releases:

1. **Naming Convention**: `{app_name}-{platform}`
   - Examples: `yday-darwin-arm64`, `yday-linux-x86_64`, `yday-windows-x86_64`

2. **Supported Platforms**:
   - `darwin-arm64` (Apple Silicon macOS)
   - `darwin-x86_64` (Intel macOS)
   - `linux-x86_64` (Linux x86_64)
   - `linux-arm64` (Linux ARM64)
   - `windows-x86_64` (Windows x86_64)

3. **Release Process**:
   - Create a GitHub release with tag (e.g., `v0.1.0`)
   - Upload binary assets with the correct naming convention
   - Upload a source tarball (e.g., `<app_name>-source.tar.gz`)

#### Source Build Fallback

If no release binary is available, pget will:
1. Download the source code from the repository
2. Look for `MODULE.bazel` or `BUILD` file
3. Build using Bazel with the target `//:{app_name}_bin`
4. Install the resulting binary

**Note**: Users need Bazel (or bazelisk) installed for source builds.

### Documentation

#### README.md

Should include:
- Description of what the app does
- Usage examples
- Installation instructions
- Requirements

#### doc/{app_name}.yaml (Optional)

Metadata file for app information (ALL CAPS field names):
```yaml
NAME: <app_name>
VERSION: "0.1.0"
DESCRIPTION: >
  Brief description of the app
USAGE:
  - "<app_name>"
  - "<app_name> --help"
  - "<app_name> --version"
OPTIONS:
  - "-h, --help        Show help message"
  - "-v, --version     Show version information"
OUTPUT: Description of output
AUTHOR: "@username"
DATE: "YYYY-MM-DD"
NOTES: []
```

### Testing

- Place test files in `test/` directory
- Use standard Python testing (unittest, pytest, etc.)
- Test files should be named `test_*.py`

### Program Types

pget is designed for **CLI (Command Line Interface) tools**:

- **CLI utilities**: Command-line tools that perform specific tasks
- **Single-purpose tools**: Focused tools that do one thing well
- **Cross-platform tools**: Should work on macOS, Linux, and Windows
- **Standalone executables**: Self-contained binaries (via Nuitka)

**Not suitable for**:
- GUI applications (unless they also have CLI interface)
- Web servers or long-running services
- Libraries or packages meant for import only
- Tools requiring complex runtime dependencies

### Installation Flow

When a user runs `pget install <app_name>`:

1. **Check Repository**: Verifies app exists in `pynosaur` organization
2. **Try Binary Download**: Looks for release binary matching user's platform
3. **Fallback to Source**: If no binary, downloads source and builds with Bazel
4. **Install Binary**: Copies binary to `~/.pget/bin/`
5. **Install Documentation**: Copies `doc/` to `~/.pget/helpers/<app_name>/doc/`
6. **Create Metadata**: Saves install info to `~/.pget/helpers/<app_name>/.pget-metadata.json`
7. **Make Executable**: Sets executable permissions
8. **Update PATH**: Ensures `~/.pget/bin` is in user's PATH

### Data Storage and Directory Structure

Apps installed by pget use a hybrid directory structure:

```
~/.pget/
├── bin/                    # All executables (in PATH)
│   └── <app_name>
└── helpers/                # Per-app helper files and data
    └── <app_name>/
        ├── .pget-metadata.json  # Install metadata (created by pget)
        ├── doc/                 # Documentation (created by pget)
        │   └── <app_name>.yaml
        ├── data/                # Optional: create if needed
        ├── config/              # Optional: create if needed
        └── cache/               # Optional: create if needed
```

#### Directory Purposes

- **`bin/`** - All executables, added to PATH
- **`helpers/<name>/doc/`** - App documentation (managed by pget)
- **`helpers/<name>/data/`** - Persistent storage (databases, saved state)
- **`helpers/<name>/config/`** - User configuration files
- **`helpers/<name>/cache/`** - Temporary/cached data (can be deleted)

#### Using Data Directories in Your App

Apps that need persistent storage should use the standard directories:

```python
from pathlib import Path

APP_NAME = "myapp"
PGET_HELPERS = Path.home() / ".pget" / "helpers"

# App directories
APP_ROOT = PGET_HELPERS / APP_NAME
DATA_DIR = APP_ROOT / "data"
CONFIG_DIR = APP_ROOT / "config"
CACHE_DIR = APP_ROOT / "cache"

def ensure_dirs():
    """Create app directories as needed."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def save_database():
    ensure_dirs()
    db_path = DATA_DIR / "database.json"
    # ... save to db_path
```

**Important**: Apps must create `data/`, `config/`, and `cache/` directories themselves when needed. Only `doc/` is created by pget during installation.

### Best Practices

1. **Keep it simple**: Focus on doing one thing well
2. **Pure Python**: Prefer standard library, minimize external dependencies
3. **Error handling**: Provide clear error messages
4. **Documentation**: Include helpful `--help` output
5. **Testing**: Write tests for core functionality
6. **Versioning**: Use semantic versioning (e.g., `0.1.0`)
7. **Releases**: Tag releases and provide binaries for common platforms

### Quick Start for App Developers

Creating a new pget-compatible app:

1. **Create repository structure**
   ```bash
   mkdir myapp
   cd myapp
   mkdir -p app doc test
   ```

2. **Create `app/__init__.py`**
   ```python
   __version__ = "0.1.0"
   ```

3. **Create `app/main.py`**
   ```python
   #!/usr/bin/env python3
   import sys
   from app import __version__
   
   def main():
       args = sys.argv[1:]
       if args and args[0] in ("-h", "--help"):
           print("Usage: myapp [options]")
           return 0
       if args and args[0] in ("-v", "--version"):
           print(__version__)
           return 0
       
       # Your app logic here
       print("Hello, Friend?")
       return 0
   
   if __name__ == "__main__":
       sys.exit(main())
   ```

4. **Create `MODULE.bazel`** (copy from yday example)

5. **Create `BUILD`** (copy from yday example, update app name)

6. **Test locally**
   ```bash
   python app/main.py
   ```

7. **Build with Bazel**
   ```bash
   bazel build //:myapp_bin
   ```

8. **Create GitHub release with binary assets**

For a complete working example, see the [yday](https://github.com/pynosaur/yday) repository.

---

## Contributing

Ahoy there! Code, code:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

- Report issues on [GitHub Issues](https://github.com/pynosaur/pget/issues)
- For app development questions, refer to the [App Development Guidelines](#app-development-guidelines) above

## Project Status

pget is in active development. The core functionality is stable and ready for use, but APIs may change as the project evolves.
