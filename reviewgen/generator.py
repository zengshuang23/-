"""Core generator: plan + template to produce a review in Markdown."""

from __future__ import annotations

import datetime as _dt
from typing import Dict, List, Sequence

from jinja2 import Template

from .citations import format_references, map_sources, rotate_citations
from .outline import generate_outline
from .preprocess import extract_keywords
from .utils import wrap_paragraph
from .llm import LLMClient, LocalRuleLLM


def _build_section(title: str, bullets: List[str], paragraph: str) -> str:
    bullet_block = "\n".join(f"- {b}" for b in bullets)
    return f"## {title}\n\n{bullet_block}\n\n{wrap_paragraph(paragraph)}\n"


def generate_review(
    *,
    topic: str,
    audience: str,
    length: int,
    mode: str,
    keywords: List[str],
    outline: List[str],
    sources: Sequence[str],
    source_names: Sequence[str] | None,
    lang: str,
    llm_client: LLMClient | None = None,
) -> str:
    """Generate the review markdown."""
    if source_names:
        mapping = map_sources(source_names)
    elif sources:
        mapping = map_sources([f"Source_{i}" for i, _ in enumerate(sources, start=1)])
    else:
        mapping = {}
    citation_labels = rotate_citations(mapping, max(len(outline), 1))
    now = _dt.date.today().isoformat()

    # Fallback keywords if none provided and no sources.
    auto_keywords = extract_keywords(list(sources)) if not keywords else keywords
    all_keywords = keywords or auto_keywords

    template = Template(
        """# {{ topic }} — Review
_Audience_: {{ audience }} | _Length target_: {{ length }} words | _Mode_: {{ mode }} | _Date_: {{ now }} | _Lang_: {{ lang }}

{% for sec in sections %}
{{ sec }}
{% endfor %}
{% if references %}
## References
{{ references }}
{% else %}
**未使用外部资料 / No external sources used.**
{% endif %}
"""
    )

    sections: List[str] = []
    for idx, title in enumerate(outline):
        label = citation_labels[idx] if idx < len(citation_labels) else ""
        bullets = _build_bullets(title, topic, all_keywords, label, lang)
        paragraph = _build_paragraph(
            title, topic, audience, all_keywords, label, lang, llm_client=llm_client or LocalRuleLLM()
        )
        sections.append(_build_section(title, bullets, paragraph))

    references = format_references(mapping) if mapping else ""
    return template.render(
        topic=topic,
        audience=audience,
        length=length,
        mode=mode,
        now=now,
        lang=lang,
        sections=sections,
        references=references,
    )


def _build_bullets(title: str, topic: str, keywords: List[str], label: str, lang: str) -> List[str]:
    """Craft simple bullet points."""
    kws = ", ".join(keywords[:3]) if keywords else topic
    marker = f" {label}" if label else ""
    if lang == "zh":
        return [
            f"核心议题：{title} 与 {topic}{marker}",
            f"关键概念：{kws}",
            "趋势/贡献：方法、数据、应用",
        ]
    return [
        f"Core focus: {title} within {topic}{marker}",
        f"Key concepts: {kws}",
        "Trends/contributions: methods, data, applications",
    ]


def _build_paragraph(
    title: str,
    topic: str,
    audience: str,
    keywords: List[str],
    label: str,
    lang: str,
    llm_client: LLMClient,
) -> str:
    """Craft a paragraph using LLM client if provided; fallback to rule-based template."""
    base_prompt = (
        f"Write a concise paragraph (~120 words) for a literature review section.\n"
        f"Section: {title}\nTopic: {topic}\nAudience: {audience}\nKeywords: {', '.join(keywords[:8]) or topic}\n"
        f"Language: {'Chinese' if lang == 'zh' else 'English'}\n"
        f"Include citation marker if provided: {label or 'None'}\n"
        "Emphasize evolution, representative work, applications, and open issues.\n"
    )
    try:
        text = llm_client.generate(base_prompt, max_tokens=180)
        if text:
            return text
    except Exception:
        # Fall back silently.
        pass
    return _fallback_paragraph(title, topic, audience, keywords, label, lang)


def _fallback_paragraph(title: str, topic: str, audience: str, keywords: List[str], label: str, lang: str) -> str:
    """Rule-based paragraph used when LLM generation fails or is skipped."""
    kws = ", ".join(keywords[:5]) if keywords else topic
    citation = f" ({label})" if label else ""
    if lang == "zh":
        return (
            f"本节聚焦 {topic} 领域中的「{title}」。"
            f" 面向 {audience} 受众，我们强调 {kws} 的演进、代表性工作与应用场景{citation}。"
            " 同时概括方法与数据的改进，并指出仍待解决的开放问题。"
        )
    return (
        f"This section covers '{title}' within {topic}."
        f" For {audience} readers, it highlights the evolution of {kws}{citation},"
        " representative work, and practical use cases, summarizing method/data advances and open issues."
    )


def plan_and_generate(
    *,
    topic: str,
    audience: str,
    length: int,
    mode: str,
    keywords: List[str],
    custom_outline: str | None,
    sources: Sequence[str],
    source_names: Sequence[str] | None,
    lang: str,
    llm_client: LLMClient | None = None,
) -> str:
    """Entry point to generate a review using outline + template."""
    outline = generate_outline(mode, topic, keywords, custom_outline)
    return generate_review(
        topic=topic,
        audience=audience,
        length=length,
        mode=mode,
        keywords=keywords,
        outline=outline,
        sources=sources,
        source_names=source_names,
        lang=lang,
        llm_client=llm_client,
    )
