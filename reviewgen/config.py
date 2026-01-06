"""Configuration objects for the review generator."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ReviewConfig:
    """User-facing configuration for generating a review."""

    topic: str
    audience: str = "general"
    length: int = 1500
    mode: str = "timeline"  # timeline|school|application|custom
    keywords: List[str] = field(default_factory=list)
    outline: Optional[str] = None
    sources: List[Path] = field(default_factory=list)
    lang: str = "zh"
    output: Optional[Path] = None
    llm: str = "local"  # local|huggingface|openai|deepseek
    llm_endpoint: Optional[str] = None
    llm_model: Optional[str] = None
    llm_token: Optional[str] = None
    llm_timeout: int = 8

    def validate(self) -> None:
        """Validate basic fields."""
        valid_audience = {"researcher", "student", "industry", "general"}
        valid_mode = {"timeline", "school", "application", "custom"}
        valid_lang = {"zh", "en"}
        valid_llm = {"local", "huggingface", "openai", "deepseek"}
        if self.audience not in valid_audience:
            raise ValueError(f"audience must be one of {valid_audience}")
        if self.mode not in valid_mode:
            raise ValueError(f"mode must be one of {valid_mode}")
        if self.lang not in valid_lang:
            raise ValueError(f"lang must be one of {valid_lang}")
        if self.mode == "custom" and not self.outline:
            raise ValueError("outline is required when mode is 'custom'")
        if self.llm not in valid_llm:
            raise ValueError(f"llm must be one of {valid_llm}")
        if self.llm_timeout <= 0:
            raise ValueError("llm_timeout must be positive")
