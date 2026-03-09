"""Provider adapters — thin wrappers around LLM APIs."""
from konomi.triad.providers.registry import get_provider, list_providers

__all__ = ["get_provider", "list_providers"]
