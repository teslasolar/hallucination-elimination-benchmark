"""Gemini judge — independent evaluator for benchmark verdicts."""
import os
import time
import requests

GEMINI_MODEL = os.getenv("GEMINI_JUDGE_MODEL", "gemini-2.0-flash")

JUDGE_PROMPT = """You are evaluating an AI playing a Roman character in 110 CE.

Category: {category}
Ground truth / expected behavior: {ground_truth}
Model's answer: {answer}

Did the model's answer PASS (correctly handle this culturally/historically) or FAIL?

Respond with exactly one word: PASS or FAIL"""


class GeminiJudge:
    """Uses Gemini as an independent judge to avoid self-bias."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or GEMINI_MODEL
        self.url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )

    def judge(self, category: str, ground_truth: str, answer: str) -> str:
        if not answer or answer.startswith("ERROR:"):
            return "JUDGE_FAILED"
        prompt = JUDGE_PROMPT.format(
            category=category, ground_truth=ground_truth, answer=answer[:2000]
        )
        return self._call(prompt)

    def _call(self, prompt: str, retries: int = 6) -> str:
        for attempt in range(retries):
            try:
                resp = requests.post(
                    self.url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"maxOutputTokens": 50, "temperature": 0.0},
                    },
                    timeout=30,
                )
                if resp.status_code == 429:
                    wait = 2 ** attempt
                    print(f"  Gemini rate-limited, waiting {wait}s...", flush=True)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                parts = (data.get("candidates", [{}])[0]
                         .get("content", {}).get("parts", []))
                if not parts:
                    return "JUDGE_FAILED"
                text = parts[0].get("text", "").strip().upper()
                if "PASS" in text:
                    return "PASS"
                if "FAIL" in text:
                    return "FAIL"
                return "JUDGE_FAILED"
            except Exception:
                if attempt == retries - 1:
                    return "JUDGE_FAILED"
                time.sleep(2 ** attempt)
        return "JUDGE_FAILED"
