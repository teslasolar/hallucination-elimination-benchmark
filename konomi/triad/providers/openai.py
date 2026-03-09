"""OpenAI provider adapter."""
import os, time
from konomi.triad.providers.registry import register


@register("openai")
def make_caller(model: str, **kwargs):
    from openai import OpenAI
    api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY", "")
    client = OpenAI(api_key=api_key)

    def call(system_prompt: str, user_question: str) -> str:
        for attempt in range(3):
            try:
                resp = client.chat.completions.create(
                    model=model, max_tokens=500,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_question},
                    ],
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                err = str(e).lower()
                if "rate" in err and attempt < 2:
                    time.sleep(2 ** attempt * 5)
                elif attempt == 2:
                    return f"ERROR: {e}"
                else:
                    time.sleep(2 ** attempt)
        return "ERROR: max retries exceeded"
    return call
