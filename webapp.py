"""Simple Flask front-end for the review generator."""

from __future__ import annotations

from typing import List

from flask import Flask, render_template_string, request

from reviewgen.preprocess import basic_clean
from reviewgen.generator import plan_and_generate
from reviewgen.outline import generate_outline
from reviewgen.llm import build_llm_client


app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Review Generator</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; max-width: 960px; }
    label { display: block; margin-top: 0.8rem; font-weight: bold; }
    input, select, textarea { width: 100%; padding: 0.5rem; margin-top: 0.2rem; }
    textarea { height: 120px; }
    .row { display: flex; gap: 1rem; }
    .row > div { flex: 1; }
    .card { padding: 1rem; border: 1px solid #ccc; border-radius: 8px; margin-top: 1rem; background: #fafafa; }
    pre { white-space: pre-wrap; background: #111; color: #eee; padding: 1rem; border-radius: 8px; }
    button { padding: 0.6rem 1.2rem; margin-top: 1rem; }
    .error { color: #b00020; margin-top: 1rem; }
  </style>
</head>
<body>
  <h1>Review Generator</h1>
  <form method="post" enctype="multipart/form-data">
    <div class="row">
      <div>
        <label>Topic</label>
        <input name="topic" required value="{{ form.topic }}">
      </div>
      <div>
        <label>Audience</label>
        <select name="audience">
          {% for a in ['researcher','student','industry','general'] %}
            <option value="{{a}}" {% if form.audience==a %}selected{% endif %}>{{a}}</option>
          {% endfor %}
        </select>
      </div>
    </div>
    <div class="row">
      <div>
        <label>Mode</label>
        <select name="mode">
          {% for m,label in [('timeline','Timeline'),('school','School'),('application','Application'),('custom','Custom')] %}
            <option value="{{m}}" {% if form.mode==m %}selected{% endif %}>{{label}}</option>
          {% endfor %}
        </select>
      </div>
      <div>
        <label>Target length (words)</label>
        <input name="length" type="number" value="{{ form.length }}">
      </div>
      <div>
        <label>Language</label>
        <select name="lang">
          {% for l in ['zh','en'] %}
            <option value="{{l}}" {% if form.lang==l %}selected{% endif %}>{{l}}</option>
          {% endfor %}
        </select>
      </div>
    </div>
    <label>Keywords (comma separated)</label>
    <input name="keywords" value="{{ form.keywords }}">

    <label>Custom outline (when mode=custom, use semicolons)</label>
    <input name="outline" value="{{ form.outline }}">

    <label>Paste sources (one block per line)</label>
    <textarea name="sources_text">{{ form.sources_text }}</textarea>

    <label>Upload source files (optional, text files)</label>
    <input type="file" name="sources_files" multiple>

    <div class="row">
      <div>
        <label>LLM Provider</label>
        <select name="llm">
          {% for p in ['local','huggingface','openai','deepseek'] %}
            <option value="{{p}}" {% if form.llm==p %}selected{% endif %}>{{p}}</option>
          {% endfor %}
        </select>
      </div>
      <div>
        <label>LLM Model</label>
        <input name="llm_model" value="{{ form.llm_model }}">
      </div>
      <div>
        <label>LLM Timeout (s)</label>
        <input name="llm_timeout" type="number" value="{{ form.llm_timeout }}">
      </div>
    </div>
    <label>LLM Endpoint (for huggingface/deepseek override)</label>
    <input name="llm_endpoint" value="{{ form.llm_endpoint }}">
    <label>LLM Token (not stored)</label>
    <input name="llm_token" type="password" autocomplete="off">

    <button type="submit">Generate</button>
  </form>

  {% if error %}
    <div class="error">{{ error }}</div>
  {% endif %}
  {% if result %}
    <div class="card">
      <h2>Result</h2>
      <pre>{{ result }}</pre>
    </div>
  {% endif %}
</body>
</html>
"""


def _collect_sources_from_form(req) -> tuple[list[str], list[str]]:
    """Collect source texts and names from form."""
    texts: List[str] = []
    names: List[str] = []

    pasted = req.form.get("sources_text", "").splitlines()
    for idx, line in enumerate(pasted, start=1):
        cleaned = basic_clean(line)
        if cleaned:
            texts.append(cleaned)
            names.append(f"pasted_{idx}.txt")

    files = req.files.getlist("sources_files")
    for f in files:
        try:
            content = f.read().decode("utf-8")
        except Exception:
            continue
        cleaned = basic_clean(content)
        if cleaned:
            texts.append(cleaned)
            names.append(f.filename or f"upload_{len(names)+1}.txt")

    # Deduplicate texts while keeping aligned names.
    seen = set()
    unique_texts: List[str] = []
    unique_names: List[str] = []
    for text, name in zip(texts, names):
        if text not in seen:
            seen.add(text)
            unique_texts.append(text)
            unique_names.append(name)
    return unique_texts, unique_names


@app.route("/", methods=["GET", "POST"])
def index():
    form_defaults = {
        "topic": request.form.get("topic", "多模态大模型"),
        "audience": request.form.get("audience", "researcher"),
        "mode": request.form.get("mode", "timeline"),
        "length": request.form.get("length", "1500"),
        "keywords": request.form.get("keywords", "LLM,benchmark,alignment"),
        "outline": request.form.get("outline", ""),
        "lang": request.form.get("lang", "zh"),
        "sources_text": request.form.get("sources_text", ""),
        "llm": request.form.get("llm", "local"),
        "llm_model": request.form.get("llm_model", ""),
        "llm_timeout": request.form.get("llm_timeout", "8"),
        "llm_endpoint": request.form.get("llm_endpoint", ""),
    }
    result = None
    error = None

    if request.method == "POST":
        try:
            length = int(request.form.get("length", "1500") or 1500)
        except ValueError:
            length = 1500

        try:
            llm_timeout = int(request.form.get("llm_timeout", "8") or 8)
        except ValueError:
            llm_timeout = 8

        keywords = [k.strip() for k in request.form.get("keywords", "").split(",") if k.strip()]
        sources_texts, source_names = _collect_sources_from_form(request)

        llm_provider = request.form.get("llm", "local")
        llm_token = request.form.get("llm_token") or None
        llm_model = request.form.get("llm_model") or None
        llm_endpoint = request.form.get("llm_endpoint") or None
        llm_client = None
        if llm_provider != "local":
            try:
                llm_client = build_llm_client(
                    llm_provider, endpoint=llm_endpoint, model=llm_model, token=llm_token, timeout=llm_timeout
                )
            except Exception as exc:
                error = f"LLM init failed: {exc}"

        outline = generate_outline(
            request.form.get("mode", "timeline"),
            request.form.get("topic", ""),
            keywords,
            request.form.get("outline") or None,
        )
        try:
            result = plan_and_generate(
                topic=request.form.get("topic", ""),
                audience=request.form.get("audience", "general"),
                length=length,
                mode=request.form.get("mode", "timeline"),
                keywords=keywords,
                custom_outline=request.form.get("outline") or None,
                sources=sources_texts,
                source_names=source_names,
                lang=request.form.get("lang", "zh"),
                llm_client=llm_client,
            )
        except Exception as exc:
            error = error or f"Generation failed: {exc}"
    return render_template_string(TEMPLATE, form=form_defaults, result=result, error=error)


if __name__ == "__main__":
    app.run(debug=True)
