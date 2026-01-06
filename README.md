# Review Generator (综述生成器)

Python CLI + Flask UI to produce structured Markdown reviews from a topic, audience, outline preference, and optional local sources.

## Features
- CLI `reviewgen` with topic/audience/length/mode/keywords/outline/sources/lang/output options.
- Planner + template generator; inserts citation markers `[S1]` mapped to provided source files.
- Source preprocessing: load glob paths, clean, deduplicate, segment, extract keywords with TF-IDF.
- Works offline by default (local rule generator); optional LLM adapters (Hugging Face Inference or OpenAI placeholder).
- Web UI (Flask) for form-based generation at http://127.0.0.1:5000.
- Optional LLM adapters: local (default), Hugging Face Inference, OpenAI placeholder, DeepSeek.

## Installation
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

## CLI Usage
Basic timeline review in Chinese:
```bash
python -m reviewgen --topic "大模型评测" --audience researcher --mode timeline --keywords "LLM,benchmark,alignment" --lang zh --output ./out/review.md
```

Application-focused review with sources in English:
```bash
python -m reviewgen --topic "Graph Neural Networks" --audience industry --mode application --sources "./data/*.txt" --keywords "GNN,link prediction" --lang en --output ./out/gnn.md
```

## Web 界面
```bash
python webapp.py
# 浏览器打开 http://127.0.0.1:5000
```

## 可选 LLM 适配
- 默认：本地规则生成（无外部调用）。
- Hugging Face Inference（示例使用免费公共模型端点，需自定 endpoint；token 可选）：
  ```bash
  python -m reviewgen --topic "LLM Safety" --audience industry --mode application \
    --keywords "alignment,red teaming" \
    --llm huggingface --llm-endpoint https://api-inference.huggingface.co/models/gpt2 \
    --llm-timeout 12 --llm-token %HF_TOKEN%
  ```
- OpenAI 占位：`--llm openai --llm-token $OPENAI_API_KEY --llm-model gpt-3.5-turbo`（需自备 key，未内置）。
- DeepSeek：`--llm deepseek --llm-token $DEEPSEEK_API_KEY --llm-model deepseek-chat`（endpoint 默认为 https://api.deepseek.com）。
- 超时与失败：`--llm-timeout` 控制远端请求超时（秒，默认 8），网络失败或超时自动回退本地规则生成。

## Sample output (fragment)
```
# Graph Neural Networks — Review
_Audience_: industry | _Length target_: 1500 words | _Mode_: application | _Date_: 2024-01-02 | _Lang_: en

## Introduction
- Core focus: Introduction within Graph Neural Networks
- Key concepts: GNN, link prediction
- Trends/contributions: methods, data, applications

This section covers 'Introduction' within Graph Neural Networks. For industry readers, it highlights the evolution of GNN, link prediction, representative work, and practical use cases, summarizing method/data advances and open issues.
...
```

## Tests
```bash
pytest
```
