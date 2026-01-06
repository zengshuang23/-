import reviewgen.outline as ol


def test_custom_outline_parses_sections():
    sections = ol.generate_outline("custom", "topic", [], "A;B;C")
    assert sections == ["A", "B", "C"]


def test_timeline_outline_contains_intro_and_refs():
    sections = ol.generate_outline("timeline", "AI", ["x", "y"], None)
    assert sections[0] == "Introduction"
    assert "References" in sections
