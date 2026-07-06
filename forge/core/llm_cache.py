"""Forge v2 disk cache for LLM calls.

Speeds up repetitive iterations and benchmark evaluations while saving API quota.
Can be disabled globally by setting the environment variable FORGE_DISABLE_CACHE=1.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger("forge.core.llm_cache")


def _get_cache_dir(root: Path) -> Path:
    """Get the path to the cache directory, creating it if necessary."""
    cache_dir = root / ".forge_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _make_hash_key(provider: str, model: str, system_prompt: str, user_prompt: str,
                   tools: Optional[list], temperature: Optional[float],
                   max_tokens: Optional[int], top_p: Optional[float]) -> str:
    """Create a unique SHA256 key based on request parameters."""
    # Convert tools to a stable, sorted representation if list
    tools_repr = ""
    if tools:
        try:
            tools_repr = json.dumps(tools, sort_keys=True)
        except Exception:
            tools_repr = str(tools)

    payload = {
        "provider": provider,
        "model": model,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "tools": tools_repr,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
    }
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def get_cached_response(root: Path, provider: str, model: str, system_prompt: str, user_prompt: str,
                        tools: Optional[list] = None, temperature: Optional[float] = None,
                        max_tokens: Optional[int] = None, top_p: Optional[float] = None) -> Optional[Any]:
    """Retrieve a cached LLM response if present on disk, otherwise return None."""
    if os.environ.get("FORGE_DISABLE_CACHE") == "1":
        return None

    key = _make_hash_key(provider, model, system_prompt, user_prompt, tools, temperature, max_tokens, top_p)
    cache_file = _get_cache_dir(root) / f"{key}.json"

    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            logger.debug("Cache hit for key %s", key)
            return data.get("response")
        except Exception as e:
            logger.warning("Failed to read cache file %s: %s", cache_file, e)

    return None


def set_cached_response(root: Path, provider: str, model: str, system_prompt: str, user_prompt: str,
                        response: Any, tools: Optional[list] = None, temperature: Optional[float] = None,
                        max_tokens: Optional[int] = None, top_p: Optional[float] = None) -> None:
    """Save an LLM response to disk."""
    if os.environ.get("FORGE_DISABLE_CACHE") == "1":
        return

    key = _make_hash_key(provider, model, system_prompt, user_prompt, tools, temperature, max_tokens, top_p)
    cache_file = _get_cache_dir(root) / f"{key}.json"

    try:
        data = {
            "metadata": {
                "provider": provider,
                "model": model,
                "created_at": Path(cache_file).stat().st_mtime if cache_file.exists() else None
            },
            "response": response
        }
        # Write atomically using a temporary file
        tmp_file = cache_file.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp_file, cache_file)
        logger.debug("Cached response saved under key %s", key)
    except Exception as e:
        logger.warning("Failed to write cache file %s: %s", cache_file, e)


def clear_cache(root: Path) -> int:
    """Delete all cached JSON entries. Returns count of removed items."""
    cache_dir = root / ".forge_cache"
    if not cache_dir.exists():
        return 0

    count = 0
    for item in cache_dir.glob("*.json"):
        try:
            item.unlink()
            count += 1
        except Exception as e:
            logger.warning("Failed to delete cache file %s: %s", item, e)
    return count
