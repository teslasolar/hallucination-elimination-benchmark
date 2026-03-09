"""Google Gemini provider adapter."""
import os, time, requests as req
from konomi.triad.providers.registry import register


@register("gemini")
def make_caller(model: str, **kwargs):
    api_key = kwargs.get("api_key") or os.getenv("GEMINI_API_KEY", "")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={api_key}")

    def call(system_prompt: str, user_question: str) -> str:
        for attempt in range(4):
            try:
                resp = req.post(url, json={
                    "system_instruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"parts": [{"text": user_question}]}],
                    "generationConfig": {"maxOutputTokens": 500, "temperature": 0.0},
                }, timeout=60)
                if resp.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                parts = (resp.json().get("candidates", [{}])[0]
                         .get("content", {}).get("parts", []))
                return parts[0]["text"].strip() if parts else "ERROR: empty response"
            except Exception as e:
                if attempt == 3:
                    return f"ERROR: {e}"
                time.sleep(2 ** attempt)
        return "ERROR: max retries exceeded"
    return call
