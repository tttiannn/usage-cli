#!/usr/bin/env python3
"""Install Usage CLI for the current user without changing shell settings."""
import argparse
import os
from pathlib import Path
import shlex
import sys


def install(destination, force=False):
    destination = Path(destination).expanduser().resolve()
    source = Path(__file__).resolve().parent / 'bin' / 'usage'
    runtime = destination / 'usage.py'
    if os.name == 'nt':
        launcher = destination / 'usage.cmd'
        python = sys.executable.replace('%', '%%')
        content = f'@echo off\r\nchcp 65001 >nul\r\n"{python}" "%~dp0usage.py" %*\r\n'.encode('utf-8')
    else:
        launcher = destination / 'usage'
        content = ('#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' ' + shlex.quote(str(runtime)) + ' "$@"\n').encode('utf-8')
    files = [(runtime, source.read_bytes()), (launcher, content)]
    for path, data in files:
        if (path.exists() or path.is_symlink()) and not force:
            if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
                raise RuntimeError(f'Refusing to overwrite {path}. Review it and use --force to replace it.')
    destination.mkdir(parents=True, exist_ok=True)
    for path, data in files:
        if path.is_symlink():
            path.unlink()
        path.write_bytes(data)
        path.chmod(0o755)
    return launcher


def main():
    default = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))) / 'Programs' / 'usage-cli' / 'bin' if os.name == 'nt' else Path.home() / '.local' / 'bin'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dir', type=Path, default=default, help='Install directory (default: per-user bin)')
    parser.add_argument('--force', action='store_true', help='Replace an existing installation after reviewing it')
    args = parser.parse_args()
    if sys.version_info < (3, 9):
        parser.error('Python 3.9 or newer is required')
    try:
        launcher = install(args.dir, args.force)
    except (OSError, RuntimeError) as error:
        parser.exit(1, f'Error: {error}\n')
    print(f'Installed {launcher}')
    print(f'Add this directory to PATH if needed: {launcher.parent}')
    print('Open a new terminal and run: usage --help')


if __name__ == '__main__':
    main()
