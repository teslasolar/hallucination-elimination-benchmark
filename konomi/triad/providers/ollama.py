"""Ollama local model provider adapter."""
import os
import requests as req
from konomi.triad.providers.registry import register


@register("ollama")
def make_caller(model: str, **kwargs):
    base_url = kwargs.get("url") or os.getenv("OLLAMA_URL", "http://localhost:11434")
    temperature = kwargs.get("temperature", 0.0)
    timeout = kwargs.get("timeout", 120)

    def call(system_prompt: str, user_question: str) -> str:
        try:
            resp = req.post(f"{base_url}/api/generate", json={
                "model": model,
                "system": system_prompt,
                "prompt": user_question,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": 500},
            }, timeout=timeout)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except Exception as e:
            return f"ERROR: {e}"
    return call
