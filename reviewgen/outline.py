"""Outline planner for the review generator."""

from __future__ import annotations

from typing import List


DEFAULT_SECTIONS = [
    "Introduction",
    "Categorized Review",
    "Comparative Analysis",
    "Challenges and Limitations",
    "Future Directions",
    "References",
]


def generate_outline(mode: str, topic: str, keywords: List[str], custom_outline: str | None = None) -> List[str]:
    """Generate outline sections based on mode."""
    mode = mode.lower()
    if mode == "custom":
        if not custom_outline:
            raise ValueError("Custom outline is required for mode 'custom'")
        return [section.strip() for section in custom_outline.split(";") if section.strip()]

    if mode == "timeline":
        body = ["Early stage", "Middle stage", "Recent trends"]
    elif mode == "school":
        body = ["Methodological schools", "Representative work", "Key debates"]
    elif mode == "application":
        body = ["Applications", "Case studies", "Impact"]
    else:
        body = ["Key themes"]

    # Insert keywords into thematic sections for relevance.
    if keywords:
        body.append(f"Cross-cutting themes: {', '.join(keywords[:4])}")

    return ["Introduction"] + body + ["Comparative Analysis", "Challenges and Limitations", "Future Directions", "References"]
