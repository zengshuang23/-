"""Utility helpers."""

from __future__ import annotations

import textwrap
from typing import Iterable, List


def truncate_text(text: str, length: int) -> str:
    """Truncate text softly at a given length."""
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0] + "..."


def chunk_list(items: Iterable[str], size: int) -> List[str]:
    """Split a list into chunks of size."""
    chunk: List[str] = []
    chunks: List[str] = []
    for item in items:
        chunk.append(item)
        if len(chunk) >= size:
            chunks.append(" ".join(chunk))
            chunk = []
    if chunk:
        chunks.append(" ".join(chunk))
    return chunks


def wrap_paragraph(text: str, width: int = 90) -> str:
    """Wrap text for readability."""
    return textwrap.fill(text, width=width)
