"""Reuse last week's Groq API call for the assignment form."""
import os
from groq_chat import ask, DEFAULT_MODEL


def ask_groq(text):
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Add your Groq API key to the local .env file.")
    try:
        return ask([{"role": "user", "content": text}],
                   os.environ.get("GROQ_MODEL", DEFAULT_MODEL), api_key)
    except SystemExit:
        raise RuntimeError("Groq could not complete the request. Check the key and connection.") from None
