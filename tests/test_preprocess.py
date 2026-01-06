from pathlib import Path

import reviewgen.preprocess as pp


def test_basic_clean_removes_extra_space():
    text = "  Hello   world\\n\\n"
    assert pp.basic_clean(text) == "Hello world"


def test_deduplicate_preserves_order():
    texts = ["a", "b", "a", "c"]
    assert pp.deduplicate(texts) == ["a", "b", "c"]


def test_segment_text_splits_long_sentences():
    text = "Sentence one. Sentence two is quite long and should be split accordingly. End."
    chunks = pp.segment_text(text, max_len=30)
    assert len(chunks) >= 2


def test_extract_keywords_returns_top_terms():
    texts = ["machine learning improves models", "deep learning improves representations"]
    keywords = pp.extract_keywords(texts, top_k=3)
    assert keywords  # non-empty
