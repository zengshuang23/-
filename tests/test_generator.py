from reviewgen import generator


def test_generate_review_mentions_no_external_sources_when_empty():
    outline = ["Introduction", "Body"]
    text = generator.generate_review(
        topic="Test Topic",
        audience="general",
        length=500,
        mode="timeline",
        keywords=["k1", "k2"],
        outline=outline,
        sources=[],
        source_names=[],
        lang="en",
    )
    assert "No external sources" in text


def test_generate_review_includes_citation_markers_when_sources():
    outline = ["Section A"]
    text = generator.generate_review(
        topic="Topic",
        audience="student",
        length=200,
        mode="application",
        keywords=["a"],
        outline=outline,
        sources=["./sample.txt"],
        source_names=["sample.txt"],
        lang="en",
    )
    assert "[S1]" in text
