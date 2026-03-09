"""Provider registry — returns a call_model function for any supported provider."""
import os

PROVIDERS = {}


def register(name):
    def decorator(fn):
        PROVIDERS[name] = fn
        return fn
    return decorator


def get_provider(name: str, model: str, **kwargs):
    """Return a call_model(system, user) -> str function."""
    if name not in PROVIDERS:
        # Try importing the module to trigger registration
        try:
            __import__(f"konomi.triad.providers.{name}")
        except ImportError:
            pass
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDERS.keys())}")
    return PROVIDERS[name](model, **kwargs)


def list_providers():
    # Import all to populate registry
    for p in ["anthropic", "openai", "gemini", "ollama", "perplexity"]:
        try:
            __import__(f"konomi.triad.providers.{p}")
        except ImportError:
            pass
    return list(PROVIDERS.keys())
