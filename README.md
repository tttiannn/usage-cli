# Usage CLI

A small English-language terminal wrapper around [ccusage](https://github.com/ccusage/ccusage). Displays complete token counts in a readable vertical layout, with optional daily and model details.

## Requirements

- Windows 10/11, macOS, or Linux.
- Python 3.9 or newer (3.11+ recommended).
- Node.js LTS and npm, used to install and run ccusage.
- Git to clone this repository, or download and extract the repository ZIP.
- `curl` on PATH for optional pricing downloads. Modern Windows and macOS include it; on Debian/Ubuntu use `sudo apt install curl`.

The wrapper uses Python's standard library only. It was developed against ccusage 20.0.45; newer ccusage releases may change report schemas.

## Install on Windows

1. Install [Python](https://www.python.org/downloads/windows/), [Node.js LTS](https://nodejs.org/en/download), and [Git](https://git-scm.com/downloads/win). Enable the Python launcher / PATH option when offered. Open a new PowerShell window.
2. Verify prerequisites and install ccusage. Use `npm.cmd` in PowerShell to avoid script execution-policy errors:

```powershell
py -3 --version
node --version
npm.cmd install -g ccusage
ccusage.cmd --version
git clone https://github.com/tttiannn/usage-cli.git
cd usage-cli
py -3 install.py
```

If `py` is unavailable but `python --version` shows Python 3.9+, replace `py -3` with `python`. If `ccusage.cmd` is not found after installation, reopen the terminal and check that npm's global directory is on PATH (`npm.cmd prefix -g`).

3. Add the wrapper's directory to the **user** PATH once (no administrator rights required):

```powershell
$usageBin = Join-Path $env:LOCALAPPDATA 'Programs\usage-cli\bin'
$userPath = [string][Environment]::GetEnvironmentVariable('Path', 'User')
if (($userPath -split ';') -notcontains $usageBin) {
    [Environment]::SetEnvironmentVariable('Path', (($userPath.TrimEnd(';') + ';' + $usageBin).TrimStart(';')), 'User')
}
$env:Path = $env:Path.TrimEnd(';') + ';' + $usageBin
usage --help
usage week -v
```

Alternatively, add `%LOCALAPPDATA%\Programs\usage-cli\bin` through Windows' Environment Variables dialog. The installer creates `usage.cmd` and `usage.py` there. The launcher uses the Python interpreter selected at installation time.

## Install on macOS

Install Python 3, Node.js LTS/npm, and Git using your preferred installer. With [Homebrew](https://brew.sh/), the dependencies are available as `python`, `node`, and `git`.

```sh
python3 --version
node --version
npm install -g ccusage
git clone https://github.com/tttiannn/usage-cli.git
cd usage-cli
python3 install.py
```

If necessary, add the following to `~/.zshrc`, then open a new terminal:

```sh
export PATH="$PATH:$HOME/.local/bin"
```

Then run `usage --help`. `sh install.sh` is a convenience entry for the same installer.

## Install on Linux

Install Python 3.9+, Git, curl, and Node.js LTS/npm using your distribution or the official installers. On Debian/Ubuntu, `sudo apt install python3 git curl` provides the first three; verify your Python version and use the [Node.js installer instructions](https://nodejs.org/en/download) for Node LTS. Prefer a user-managed Node installation if global npm installs otherwise require administrator permissions.

```sh
python3 --version
node --version
npm install -g ccusage
git clone https://github.com/tttiannn/usage-cli.git
cd usage-cli
python3 install.py
```

If needed, add `export PATH="$PATH:$HOME/.local/bin"` to your shell startup file (`~/.bashrc` for Bash, `~/.zshrc` for Zsh). Open a new terminal and run `usage --help`.

## Installation behavior and updates

The installer does not modify PATH or shell profiles, and refuses to overwrite different existing files. Inspect an existing installation before using `python3 install.py --force` (Windows: `py -3 install.py --force`). To update, run `git pull --ff-only` in the cloned repository, then rerun the installer with `--force`. Rerun installation after moving/removing its Python interpreter.

Use `python3 install.py --dir /your/chosen/bin` or `py -3 install.py --dir 'C:\your\chosen\bin'` for a custom destination. Both `usage` (Unix) / `usage.cmd` (Windows) and the accompanying `usage.py` must stay together.

Check for name conflicts with `type -a usage` on macOS/Linux or `Get-Command usage -All` in PowerShell. Appending to PATH preserves existing command priority; aliases and functions can also take priority.

## Examples

```sh
usage                         # Today, Codex by default
usage week                    # Last 7 days including today
usage month                   # Last 30 days including today
usage --days 3                # Last 3 days; -days 3 and -d 3 also work
usage week -v                 # Daily and per-model details
usage month --models          # Compact per-model token totals
usage week --daily            # Compact daily totals
usage --since 2026-10-01 --until 2026-10-31
usage --source claude
usage --source all
usage --fresh                 # Force pricing refresh (--online is an alias)
usage --offline               # Do not attempt a pricing refresh
usage --json                  # ccusage report JSON instead of formatted output
usage --help
```

`--details` and `-v` are equivalent. Reasoning is a subset of output tokens, not an extra amount to add to the total. A model's cost is shown as `N/A` when pricing is missing or the two ccusage report snapshots do not match. Rerun if active usage changed between reads.

## Pricing and networking

The wrapper checks prices when you run it; it does not install a daemon or scheduled task. Each successfully refreshed source is cached for seven days. Failed refreshes retain existing prices and have a six-hour retry delay. A forced refresh bypasses those intervals.

Sources:

- LiteLLM's public price catalog, distributed through jsDelivr first, with GitHub Raw as fallback.
- The public models.dev catalog.
- ccusage's bundled prices for models not covered by the downloaded data.

Downloads use HTTPS and compression. Automatic downloads have a three-second timeout per URL; forced downloads have a fifteen-second timeout per URL. Failed routes may be followed by a fallback route. CDN data may lag the upstream repository. These are community-maintained catalogs, not a live billing API from your model provider.

Cached rates are passed through ccusage's pricing configuration; ccusage computes the cost. Explicit user overrides in the discovered ccusage config retain priority. Timestamp-dependent DeepSeek v4 entries are excluded from downloaded overrides to preserve ccusage's built-in schedule. Costs are estimates, and downloaded rates are not a complete historical pricing archive.

Cache files are stored under `~/.cache/usage/`. A file lock prevents simultaneous refreshes; cache writes are atomic. A temporary merged ccusage configuration is removed when the report finishes.

## Privacy and resource use

This wrapper downloads public price data and reads local reports through ccusage. It does not send usage logs or credentials to the pricing sources. Pricing servers receive ordinary download request metadata, such as your IP address. `curl` uses its normal proxy configuration.

Report output is limited to 32 MiB, pricing downloads to 20 MiB, and each ccusage report call to 180 seconds. On macOS/Linux, each child runs in a private process group. On Windows, a gated launcher is assigned to a kill-on-close Job Object before it starts the command. Commands and descendants are cleaned up on completion, timeout, or handled interruption. The wrapper uses bounded pipe-reading threads, which stop after each command. OS-level force-kills can bypass Python cleanup (especially POSIX `SIGKILL`). A restrictive Windows job policy can prevent startup; it fails rather than running without process containment.

## Development

```sh
python3 -m unittest discover -s tests -v
sh -n install.sh
```

Tests use synthetic data and do not require ccusage, a network connection, or personal usage logs. Local reports, downloaded catalogs, scratch files, and secrets are excluded from the repository.

## Uninstall

macOS/Linux:

```sh
rm "$HOME/.local/bin/usage" "$HOME/.local/bin/usage.py"
# Optional: remove downloaded prices
rm -rf "$HOME/.cache/usage"
```

Windows (PowerShell):

```powershell
Remove-Item "$env:LOCALAPPDATA\Programs\usage-cli\bin\usage.cmd"
Remove-Item "$env:LOCALAPPDATA\Programs\usage-cli\bin\usage.py"
# Optional: remove downloaded prices
Remove-Item "$HOME\.cache\usage" -Recurse
```

Remove the wrapper directory from your user PATH if desired. These steps leave ccusage itself installed.

## Validation

The CI matrix covers Windows, macOS and Linux with Python 3.9 and 3.13. Tests cover price-cache expiration, failure cooldown, file locking, config cleanup, bounded output, process-tree cleanup, and installation in paths containing spaces. The CI configuration is not proof of a passing run: check the repository Actions page for results. Account-level GitHub billing restrictions can prevent hosted jobs from starting.
