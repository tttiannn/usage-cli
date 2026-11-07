# Usage CLI

A small English-language terminal wrapper around [ccusage](https://github.com/ccusage/ccusage). Displays complete token counts in a readable vertical layout, with optional daily and model details.

## Requirements

- macOS or Linux (uses POSIX process groups and file locks; Windows is not supported).
- Python 3.9 or newer at `/usr/bin/python3`.
- `ccusage` on your PATH; developed with version 20.0.45.
- `curl` for optional pricing downloads.

Install ccusage using its [installation instructions](https://ccusage.com/guide/installation), then install this wrapper:

```sh
sh install.sh
```

The installer copies `bin/usage` to `~/.local/bin/usage`. It refuses to overwrite a different file unless you pass `--force`. If necessary, add this line to your shell configuration and open a new terminal:

```sh
export PATH="$PATH:$HOME/.local/bin"
```

Check for a name conflict with `type -a usage`. Appending the directory to PATH preserves the priority of existing commands; aliases and functions can also take priority over this executable.

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

Report output is limited to 32 MiB, pricing downloads to 20 MiB, and each ccusage report call to 180 seconds. Each child command runs in its own process group, which is cleaned up on completion, timeout, or handled interruption. Force-killing the wrapper with `SIGKILL` bypasses Python cleanup.

## Development

```sh
python3 -m unittest discover -s tests -v
sh -n install.sh
```

Tests use synthetic data and do not require ccusage, a network connection, or personal usage logs. Local reports, downloaded catalogs, scratch files, and secrets are excluded from the repository.

## Uninstall

```sh
rm "$HOME/.local/bin/usage"
# Optional: remove downloaded prices
rm -rf "$HOME/.cache/usage"
```

This leaves ccusage itself installed.
