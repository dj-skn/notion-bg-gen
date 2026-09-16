# Security policy

## Supported versions

The latest release on PyPI receives security fixes.

## Reporting a vulnerability

Please report security issues privately through
[GitHub's private vulnerability reporting](https://github.com/dj-skn/notion-bg-gen/security/advisories/new)
rather than opening a public issue.

You can expect an acknowledgement within a week. If the report is confirmed, a
fix and an advisory will follow.

## Scope

This tool reads a TOML config file, loads font files you point it at, and writes
image files. The most likely issues are in how those inputs are handled, or in
the image and font libraries it depends on. Dependency advisories are picked up
automatically by Dependabot.

This tool does not talk to the network, and it does not connect to Notion or
require any Notion credentials.
