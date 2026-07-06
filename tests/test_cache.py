"""Tests for forge.core.llm_cache — local LLM disk caching."""

import os
from pathlib import Path
import pytest

from forge.core.llm_cache import (
    get_cached_response,
    set_cached_response,
    clear_cache,
    _make_hash_key,
)


@pytest.fixture
def tmp_root(tmp_path):
    return tmp_path


class TestLlmCache:
    def test_cache_set_and_get(self, tmp_root):
        provider = "openai"
        model = "gpt-4o"
        system = "You are helpful."
        user = "Hello"
        response = "Hi there!"

        # Cache miss
        assert get_cached_response(tmp_root, provider, model, system, user) is None

        # Write to cache
        set_cached_response(tmp_root, provider, model, system, user, response)

        # Cache hit
        assert get_cached_response(tmp_root, provider, model, system, user) == response

    def test_cache_bypassed_when_disabled(self, tmp_root, monkeypatch):
        provider = "openai"
        model = "gpt-4o"
        system = "You are helpful."
        user = "Hello"
        response = "Hi there!"

        # Enable disable-cache flag
        monkeypatch.setenv("FORGE_DISABLE_CACHE", "1")

        set_cached_response(tmp_root, provider, model, system, user, response)
        assert get_cached_response(tmp_root, provider, model, system, user) is None

    def test_cache_different_parameters_yield_different_keys(self, tmp_root):
        provider = "openai"
        model = "gpt-4o"
        system = "You are helpful."
        user = "Hello"

        key1 = _make_hash_key(provider, model, system, user, tools=None, temperature=0.7, max_tokens=None, top_p=None)
        key2 = _make_hash_key(provider, model, system, user, tools=None, temperature=0.2, max_tokens=None, top_p=None)
        assert key1 != key2

        key3 = _make_hash_key(provider, model, system, user, tools=[{"name": "test"}], temperature=0.7, max_tokens=None, top_p=None)
        assert key1 != key3

    def test_clear_cache(self, tmp_root):
        provider = "openai"
        model = "gpt-4o"
        system = "You are helpful."
        user = "Hello"
        response = "Hi there!"

        set_cached_response(tmp_root, provider, model, system, user, response)
        assert (tmp_root / ".forge_cache").exists()

        # Clear
        removed = clear_cache(tmp_root)
        assert removed == 1
        assert get_cached_response(tmp_root, provider, model, system, user) is None
