"""PyInstaller entry point.

A frozen build needs a real module to start from rather than a console script,
because the generated wrappers are not present in the bundle.
"""

from notion_bg_gen.cli import main

if __name__ == "__main__":
    main()
