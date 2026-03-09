"""Perplexity provider adapter."""
import os, time, requests as req
from konomi.triad.providers.registry import register


@register("perplexity")
def make_caller(model: str, **kwargs):
    api_key = kwargs.get("api_key") or os.getenv("PERPLEXITY_API_KEY", "")
    url = "https://api.perplexity.ai/chat/completions"

    def call(system_prompt: str, user_question: str) -> str:
        for attempt in range(3):
            try:
                resp = req.post(url, headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }, json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_question},
                    ],
                    "max_tokens": 500,
                }, timeout=60)
                if resp.status_code == 402:
                    return "ERROR: out of credits (402)"
                if resp.status_code == 429:
                    time.sleep(2 ** attempt * 2)
                    continue
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                if attempt == 2:
                    return f"ERROR: {e}"
                time.sleep(2 ** attempt)
        return "ERROR: max retries exceeded"
    return call
