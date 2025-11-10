"""Utilities for managing bundled snippet assets."""

from __future__ import annotations

from pathlib import Path
import shutil


def sync_snippet_tree(source: Path, destination: Path) -> None:
    """Copy snippets from ``source`` to ``destination`` if they are missing.

    The directory structure under ``source`` is preserved. Existing files in the
    destination are left untouched so that user uploads are never overwritten.
    """

    if not source.exists():
        return

    for path in source.rglob("*"):
        if not path.is_file():
            continue

        relative_path = path.relative_to(source)
        target_path = destination / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if target_path.exists():
            continue

        shutil.copy2(path, target_path)


__all__ = ["sync_snippet_tree"]
