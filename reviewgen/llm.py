"""LLM adapter interfaces.

Provides:
- LocalRuleLLM: offline, rule-based text generator (default).
- HFInferenceLLM: optional free Hugging Face Inference API client (requires endpoint/token).
- OpenAIClient: placeholder adapter (no key included).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Dict, Optional

import requests


class LLMClient(ABC):
    """Abstract LLM client."""

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        """Generate text given a prompt."""


class LocalRuleLLM(LLMClient):
    """Default offline generator using simple templates."""

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        # For deterministic offline behavior, we simply truncate the prompt tail.
        snippet = prompt.split("\n")[-1]
        return f"{snippet} —— 本段由本地规则生成，无外部LLM调用。"


class HFInferenceLLM(LLMClient):
    """Hugging Face Inference API client (can point to free public models)."""

    def __init__(self, endpoint: str, token: Optional[str] = None, timeout: int = 8):
        self.endpoint = endpoint
        self.token = token
        self.timeout = timeout

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}}
        resp = requests.post(self.endpoint, headers=headers, data=json.dumps(payload), timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        # HF text-generation returns list of dicts with 'generated_text'
        if isinstance(data, list) and data and "generated_text" in data[0]:
            return data[0]["generated_text"]
        return str(data)


class OpenAIClient(LLMClient):
    """Placeholder OpenAI adapter; requires user to supply api_base/api_key."""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        timeout: int = 8,
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        # Deliberately lightweight placeholder without full dependency.
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }
        resp = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data: Dict = resp.json()
        choice = data.get("choices", [{}])[0]
        return choice.get("message", {}).get("content", "")


class DeepSeekClient(LLMClient):
    """DeepSeek API adapter (OpenAI-compatible chat completions)."""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        timeout: int = 8,
    ):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        try:
            resp = requests.post(
                f"{self.api_base}/chat/completions", headers=headers, json=payload, timeout=self.timeout
            )
        except Exception as exc:  # pragma: no cover - debug aid
            print(f"[DeepSeekClient] request error: {exc}")
            raise
        print(f"[DeepSeekClient] status={resp.status_code}")  # pragma: no cover - debug aid
        if resp.text:
            print(f"[DeepSeekClient] body={resp.text[:400]}")  # pragma: no cover - debug aid
        resp.raise_for_status()
        data: Dict = resp.json()
        choice = data.get("choices", [{}])[0]
        return choice.get("message", {}).get("content", "")


def build_llm_client(
    provider: str,
    *,
    endpoint: Optional[str] = None,
    model: Optional[str] = None,
    token: Optional[str] = None,
    timeout: int = 8,
) -> LLMClient:
    """Factory to build an LLM client."""
    if provider == "huggingface":
        if not endpoint:
            raise ValueError("HF Inference endpoint is required for huggingface provider")
        return HFInferenceLLM(endpoint=endpoint, token=token, timeout=timeout)
    if provider == "openai":
        if not token:
            raise ValueError("OpenAI api_key is required for openai provider")
        return OpenAIClient(api_key=token, model=model or "gpt-3.5-turbo", timeout=timeout)
    if provider == "deepseek":
        if not token:
            raise ValueError("DeepSeek api_key is required for deepseek provider")
        base = endpoint or "https://api.deepseek.com"
        return DeepSeekClient(api_key=token, api_base=base, model=model or "deepseek-chat", timeout=timeout)
    return LocalRuleLLM()
