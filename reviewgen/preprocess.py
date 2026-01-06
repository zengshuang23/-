"""Preprocess source texts for the review generator."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer


def load_texts(paths: Sequence[Path]) -> List[Tuple[Path, str]]:
    """Load raw texts from given paths.

    Supports glob patterns; silently skips missing files.
    Returns (path, text) tuples.
    """
    items: List[Tuple[Path, str]] = []
    for path in paths:
        for resolved in Path().glob(str(path)):
            if resolved.is_file():
                try:
                    items.append((resolved, resolved.read_text(encoding="utf-8")))
                except OSError:
                    continue
    return items


def basic_clean(text: str) -> str:
    """Basic cleaning: strip, normalize whitespace."""
    text = text.replace("\ufeff", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def deduplicate(texts: Iterable[str]) -> List[str]:
    """Deduplicate while preserving order."""
    seen = set()
    unique: List[str] = []
    for t in texts:
        key = t.strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(key)
    return unique


def segment_text(text: str, max_len: int = 400) -> List[str]:
    """Split text into chunks for downstream processing."""
    sentences = re.split(r"(?<=[。.!?])\s+", text)
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0
    for sent in sentences:
        if not sent:
            continue
        if current_len + len(sent) > max_len and current:
            chunks.append(" ".join(current))
            current = [sent]
            current_len = len(sent)
        else:
            current.append(sent)
            current_len += len(sent)
    if current:
        chunks.append(" ".join(current))
    return chunks


def extract_keywords(texts: List[str], top_k: int = 8) -> List[str]:
    """Extract keywords using a simple TF-IDF approach."""
    if not texts:
        return []
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=512)
    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return []
    scores = matrix.sum(axis=0).A1
    vocab = vectorizer.get_feature_names_out()
    ranked = sorted(zip(vocab, scores), key=lambda x: x[1], reverse=True)
    return [w for w, _ in ranked[:top_k]]


def preprocess_sources(paths: Sequence[Path]) -> Tuple[List[str], List[str], List[str]]:
    """Load, clean, deduplicate, and segment sources.

    Returns:
        segments: flattened list of segments.
        unique_texts: deduplicated cleaned documents.
        source_names: filenames corresponding to unique_texts order.
    """
    raw_items = load_texts(paths)
    cleaned_items: List[Tuple[Path, str]] = [(p, basic_clean(t)) for p, t in raw_items]
    seen = set()
    unique_texts: List[str] = []
    source_names: List[str] = []
    for path, text in cleaned_items:
        if text and text not in seen:
            seen.add(text)
            unique_texts.append(text)
            source_names.append(path.name)

    segments: List[str] = []
    for t in unique_texts:
        segments.extend(segment_text(t))
    return segments, unique_texts, source_names
