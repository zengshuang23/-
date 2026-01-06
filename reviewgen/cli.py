"""Command line interface for review generator."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .config import ReviewConfig
from .generator import plan_and_generate
from .preprocess import preprocess_sources


def parse_args(argv: List[str] | None = None) -> ReviewConfig:
    parser = argparse.ArgumentParser(prog="reviewgen", description="Generate a structured review in Markdown.")
    parser.add_argument("--topic", required=True, help="Topic of the review")
    parser.add_argument("--audience", choices=["researcher", "student", "industry", "general"], default="general")
    parser.add_argument("--length", type=int, default=1500, help="Target length in words")
    parser.add_argument("--mode", choices=["timeline", "school", "application", "custom"], default="timeline")
    parser.add_argument("--keywords", default="", help="Comma-separated keywords")
    parser.add_argument("--outline", default=None, help="Custom outline (semicolon separated) when mode=custom")
    parser.add_argument("--sources", nargs="*", default=[], help="Paths or glob patterns to source text files")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh")
    parser.add_argument("--output", default=None, help="Output path for markdown file")
    parser.add_argument(
        "--llm", choices=["local", "huggingface", "openai", "deepseek"], default="local", help="LLM provider"
    )
    parser.add_argument(
        "--llm-endpoint",
        dest="llm_endpoint",
        default=None,
        help="LLM HTTP endpoint (for huggingface/deepseek overrides)",
    )
    parser.add_argument("--llm-model", dest="llm_model", default=None, help="LLM model name (provider-specific)")
    parser.add_argument("--llm-token", dest="llm_token", default=None, help="LLM token/api key (optional)")
    parser.add_argument("--llm-timeout", dest="llm_timeout", type=int, default=8, help="LLM request timeout (seconds)")
    args = parser.parse_args(argv)

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    source_paths = [Path(p) for p in args.sources]
    cfg = ReviewConfig(
        topic=args.topic,
        audience=args.audience,
        length=args.length,
        mode=args.mode,
        keywords=keywords,
        outline=args.outline,
        sources=source_paths,
        lang=args.lang,
        output=Path(args.output) if args.output else None,
        llm=args.llm,
        llm_endpoint=args.llm_endpoint,
        llm_model=args.llm_model,
        llm_token=args.llm_token,
        llm_timeout=args.llm_timeout,
    )
    cfg.validate()
    return cfg


def run(cfg: ReviewConfig) -> str:
    segments, unique_texts, source_names = preprocess_sources(cfg.sources)
    sources_used = unique_texts if unique_texts else []
    llm_client = None
    if cfg.llm != "local":
        from .llm import build_llm_client

        llm_client = build_llm_client(
            cfg.llm, endpoint=cfg.llm_endpoint, model=cfg.llm_model, token=cfg.llm_token, timeout=cfg.llm_timeout
        )
    content = plan_and_generate(
        topic=cfg.topic,
        audience=cfg.audience,
        length=cfg.length,
        mode=cfg.mode,
        keywords=cfg.keywords,
        custom_outline=cfg.outline,
        sources=sources_used,
        source_names=source_names,
        lang=cfg.lang,
        llm_client=llm_client,
    )
    if cfg.output:
        cfg.output.parent.mkdir(parents=True, exist_ok=True)
        cfg.output.write_text(content, encoding="utf-8")
    return content


def main() -> None:
    cfg = parse_args()
    markdown = run(cfg)
    print(markdown)


if __name__ == "__main__":
    main()
