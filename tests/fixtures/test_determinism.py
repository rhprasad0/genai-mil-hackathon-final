"""Snapshot determinism: two snapshot runs must produce byte-identical files."""

from __future__ import annotations

import filecmp
from pathlib import Path

from ops.seed.snapshot import write_snapshot


def test_snapshot_byte_stable(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    write_snapshot(a)
    write_snapshot(b)
    files_a = sorted(p.name for p in a.iterdir())
    files_b = sorted(p.name for p in b.iterdir())
    assert files_a == files_b
    diff = filecmp.dircmp(a, b)
    assert not diff.diff_files, f"snapshot byte-differs: {diff.diff_files}"
    assert not diff.left_only and not diff.right_only
