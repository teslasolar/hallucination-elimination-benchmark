"""Anthropic Claude provider adapter."""
import os, time
from konomi.triad.providers.registry import register


@register("anthropic")
def make_caller(model: str, **kwargs):
    import anthropic
    api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY", "")
    client = anthropic.Anthropic(api_key=api_key)

    def call(system_prompt: str, user_question: str) -> str:
        for attempt in range(3):
            try:
                msg = client.messages.create(
                    model=model, max_tokens=500, system=system_prompt,
                    messages=[{"role": "user", "content": user_question}],
                )
                return msg.content[0].text.strip()
            except Exception as e:
                err = str(e).lower()
                if ("overloaded" in err or "rate" in err) and attempt < 2:
                    time.sleep(2 ** attempt * 5)
                elif attempt == 2:
                    return f"ERROR: {e}"
                else:
                    time.sleep(2 ** attempt)
        return "ERROR: max retries exceeded"
    return call
