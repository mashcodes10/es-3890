#!/usr/bin/env python3
"""
Web chat UI for Groq-hosted LLMs.

Usage:
    python3 app.py            # then open http://127.0.0.1:5002

Reads GROQ_API_KEY (and optionally GROQ_MODEL) from the environment or .env.
Conversation text is not written to application logs.
"""

import json
import os
import urllib.error
import urllib.request

from flask import Flask, jsonify, render_template, request
from markdown_it import MarkdownIt

from groq_chat import API_URL, DEFAULT_MODEL
from backend import ask_groq

MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]
SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "system_prompt.txt")
with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as prompt_file:
    SYSTEM_PROMPT = prompt_file.read().strip()
MARKDOWN = MarkdownIt("commonmark", {"html": False, "breaks": True})



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


@app.route("/week6-sketch")
def week6_sketch():
    return render_template("week6_sketch.html")


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

    try:
        reply = ask(messages, model, api_key)
    except GroqError as e:
        return jsonify(error=str(e)), 502
    # Keep pasted context out of application logs.
    return jsonify(reply=reply, reply_html=MARKDOWN.render(reply))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)
