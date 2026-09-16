# Installation

Pick the row that matches you. If none of them obviously apply, use
[uv](#uv-any-platform) - it works everywhere and does not need Python installed
first.

## uv, any platform

[uv](https://docs.astral.sh/uv/) is a single fast tool that manages Python for
you. Install it:

=== "macOS and Linux"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows"

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

Then either run it once without installing:

```bash
uvx notion-bg-gen
```

Or install it so `notion-bg` is always available:

```bash
uv tool install notion-bg-gen
```

## Homebrew, macOS

```bash
brew install dj-skn/tap/notion-bg
```

## pipx

If you already use [pipx](https://pipx.pypa.io/):

```bash
pipx install notion-bg-gen
```

## pip

Works, but installs into whichever Python environment is currently active:

```bash
pip install notion-bg-gen
```

## A downloaded binary, no Python needed

Grab the file for your system from the
[latest release](https://github.com/dj-skn/notion-bg-gen/releases/latest):

| Your computer | File |
|---|---|
| Mac with Apple Silicon (M1 and later) | `macos-arm64.tar.gz` |
| Linux, 64-bit | `linux-x86_64.tar.gz` |
| Windows, 64-bit | `windows-x86_64.zip` |

Unpack it and run `notion-bg` from inside the folder.

!!! warning "macOS will block it the first time"

    The binaries are not signed with an Apple Developer certificate, so macOS
    says the app "cannot be opened because the developer cannot be verified".
    This is expected for open-source downloads.

    To allow it: **right-click** the `notion-bg` file in Finder, choose **Open**,
    then confirm. You only do this once. Or from a terminal:

    ```bash
    xattr -d com.apple.quarantine ./notion-bg
    ```

    If you would rather avoid this entirely, install through Homebrew or uv
    instead - neither is affected.

## Checking it worked

```bash
notion-bg --version
```

If the terminal says "command not found", the install location is probably not
on your `PATH`. `uv tool update-shell` fixes that for uv; for pipx it is
`pipx ensurepath`. Close and reopen the terminal afterwards.

## Requirements

Python 3.10 or newer, if you are installing from PyPI. The standalone binaries
bundle their own and need nothing.

## Removing it

```bash
uv tool uninstall notion-bg-gen     # or: pipx uninstall notion-bg-gen
brew uninstall notion-bg            # Homebrew
```

Your palettes stay behind in the config directory; `notion-bg config path`
prints where that is.
