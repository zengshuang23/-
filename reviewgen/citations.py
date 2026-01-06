"""Citation utilities for mapping sources to labels."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence


def map_sources(paths: Sequence[Path | str]) -> Dict[str, str]:
    """Map source paths to citation labels [S1], [S2], ..."""
    mapping: Dict[str, str] = {}
    for idx, path in enumerate(paths, start=1):
        label = f"[S{idx}]"
        mapping[label] = Path(path).name
    return mapping


def rotate_citations(mapping: Dict[str, str], count: int) -> List[str]:
    """Return a list of labels to be attached to sections in a round-robin way."""
    labels = list(mapping.keys())
    if not labels:
        return []
    result: List[str] = []
    for i in range(count):
        result.append(labels[i % len(labels)])
    return result


def format_references(mapping: Dict[str, str]) -> str:
    """Format reference list."""
    lines = []
    for label, name in mapping.items():
        lines.append(f"{label} {name}")
    return "\n".join(lines)
