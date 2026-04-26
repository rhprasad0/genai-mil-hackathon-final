"""Convenience wrapper: ``python -m ops.seed.reset`` == ``load --reset``.

The application plan refers to this command as ``reset_demo``. It is not
exposed as an MCP tool. There is no flag that bypasses the connection
guard.
"""

from __future__ import annotations

import sys

from ops.seed.load import main as load_main


def main(argv: list[str] | None = None) -> int:
    return load_main(["--reset", *(argv or [])])


if __name__ == "__main__":
    sys.exit(main())
