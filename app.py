#!/usr/bin/env python3
"""
Web chat UI for Groq-hosted LLMs.

Usage:
    python3 app.py            # then open http://127.0.0.1:5000

Reads GROQ_API_KEY (and optionally GROQ_MODEL) from the environment or .env.
Every prompt and its reply (or error) is appended to prompts.jsonl.
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime

from flask import Flask, jsonify, render_template, request

from groq_chat import API_URL, DEFAULT_MODEL
from backend import ask_groq

MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]
SYSTEM_PROMPT = "You are a helpful assistant."
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts.jsonl")


def load_dotenv(path=".env"):
    """Minimal .env loader so we don't need python-dotenv."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def log_prompt(model, prompt, reply=None, error=None):
    """Append one exchange to prompts.jsonl, one JSON object per line."""
    entry = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "prompt": prompt,
        "reply": reply,
        "error": error,
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        app.logger.warning("Could not write prompt log: %s", e)


load_dotenv()
app = Flask(__name__)


class GroqError(Exception):
    pass


def ask(messages, model, api_key, temperature=0.7):
    """Like groq_chat.ask, but raises instead of exiting the process."""
    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Groq sits behind Cloudflare, which 403s the default urllib agent.
            "User-Agent": "groq-chat-web/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise GroqError(f"Groq API error {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise GroqError(f"Network error: {e.reason}")

    return data["choices"][0]["message"]["content"]


@app.route("/")
def index():
    default = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)
    models = MODELS if default in MODELS else [default] + MODELS
    return render_template("chat.html", models=models, default_model=default)


@app.route("/echo", methods=["GET", "POST"])
@app.route("/assignment", methods=["GET", "POST"])
def assignment():
    echo_mode = request.path == "/echo"
    text = request.form.get("text", "").strip() if request.method == "POST" else ""
    response = ""
    error = ""
    if request.method == "POST":
        if not text:
            error = "Enter some text first."
        elif echo_mode:
            response = text
        else:
            try:
                response = ask_groq(text)
            except RuntimeError as exc:
                error = str(exc)
    return render_template("index.html", text=text, response=response,
                           error=error, echo_mode=echo_mode)


@app.route("/api/chat", methods=["POST"])
def chat():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return jsonify(error="No API key. Set GROQ_API_KEY or add it to .env."), 500

    payload = request.get_json(silent=True) or {}
    history = payload.get("messages") or []
    model = payload.get("model") or os.environ.get("GROQ_MODEL", DEFAULT_MODEL)

    # The browser holds the conversation; only accept user/assistant turns from it.
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m["role"], "content": str(m["content"])}
        for m in history
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and "content" in m
    ]
    if len(messages) < 2:
        return jsonify(error="No messages to send."), 400

    prompt = messages[-1]["content"] if messages[-1]["role"] == "user" else None

    try:
        reply = ask(messages, model, api_key)
    except GroqError as e:
        log_prompt(model, prompt, error=str(e))
        return jsonify(error=str(e)), 502
    log_prompt(model, prompt, reply=reply)
    return jsonify(reply=reply)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)
