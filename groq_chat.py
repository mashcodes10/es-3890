#!/usr/bin/env python3
"""

Setup:
    export GROQ_API_KEY=gsk_...

Usage:
    python3 groq_chat.py "what is a commitment ledger?"
    python3 groq_chat.py                      # interactive chat, Ctrl-D to quit
    echo "summarize this" | python3 groq_chat.py
    python3 groq_chat.py -m openai/gpt-oss-120b "harder question"
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"


def ask(messages, model, api_key, temperature=0.7):
    """Send the message list to Groq and return the assistant's reply text."""
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
            "User-Agent": "groq-chat-cli/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        sys.exit(f"Groq API error {e.code}: {detail}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error: {e.reason}")

    return data["choices"][0]["message"]["content"]


def main():
    p = argparse.ArgumentParser(description="Talk to a Groq-hosted LLM.")
    p.add_argument("prompt", nargs="*", help="prompt text; omit for interactive mode")
    p.add_argument("-m", "--model", default=os.environ.get("GROQ_MODEL", DEFAULT_MODEL))
    p.add_argument("-s", "--system", default="You are a helpful assistant.")
    p.add_argument("-t", "--temperature", type=float, default=0.7)
    p.add_argument("--key", default=os.environ.get("GROQ_API_KEY"))
    args = p.parse_args()

    if not args.key:
        sys.exit("No API key. Set GROQ_API_KEY or pass --key.")

    messages = [{"role": "system", "content": args.system}]

    # One-shot: prompt on the command line, or piped in on stdin.
    prompt = " ".join(args.prompt)
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()

    if prompt:
        messages.append({"role": "user", "content": prompt})
        print(ask(messages, args.model, args.key, args.temperature))
        return

    # Interactive: keeps the conversation history so follow-ups have context.
    print(f"Groq chat ({args.model}). Ctrl-D or Ctrl-C to quit.")
    while True:
        try:
            line = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not line:
            continue
        messages.append({"role": "user", "content": line})
        reply = ask(messages, args.model, args.key, args.temperature)
        messages.append({"role": "assistant", "content": reply})
        print(f"\n{reply}")


if __name__ == "__main__":
    main()
