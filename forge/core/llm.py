"""Forge v2 — LLM provider abstraction layer.

Handles all calls to external LLM APIs (OpenAI, Anthropic, DeepSeek, Google/Gemini).
Includes client caching, exponential backoff retries, tool-calling support,
and automatic stripping of unsupported parameters for reasoning models.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("forge.core.llm")


# ponytail: global client cache — keyed by (provider, base_url, api_key_prefix)
_client_cache: dict = {}


def _load_hermes_env() -> None:
    """Load API keys from local hermes .env if they are missing in os.environ."""
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("ANTHROPIC_API_KEY") or not os.environ.get("DEEPSEEK_API_KEY"):
        env_path = Path("C:/Users/hund/AppData/Local/hermes/.env")
        if env_path.exists():
            try:
                import dotenv
                dotenv.load_dotenv(env_path)
            except ImportError:
                pass


def _cache_key(provider: str, base_url: Optional[str], api_key: Optional[str]) -> str:
    key_prefix = (api_key or "")[:8]
    return f"{provider}:{base_url}:{key_prefix}"


def _is_reasoning_model(model: str) -> bool:
    """Return True for models that do not accept a temperature parameter."""
    low = model.lower()
    return "reasoner" in low or "-r1" in low or low.endswith("r1")


def _llm_call_with_retry(fn, max_retries: int = 3) -> str:
    """Call fn() with exponential backoff on transient API errors."""
    delay = 1.0
    last_exc: Exception = RuntimeError("No attempts made")
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            exc_str = str(exc)
            if any(code in exc_str for code in ("429", "500", "502", "503", "524")):
                last_exc = exc
                logger.warning(
                    "Transient API error (attempt %d/%d): %s — retrying in %.1fs",
                    attempt + 1, max_retries, exc_str, delay
                )
                time.sleep(delay)
                delay *= 2
            else:
                raise
    raise last_exc


# --- Tool schema converters ---

def _tools_to_openai_schema(tools: list) -> list:
    """Convert tools.yaml-style list to OpenAI function calling schema."""
    result = []
    for tool in tools:
        params = tool.get("parameters", {})
        properties = {}
        for param_name, param_type in params.items():
            if isinstance(param_type, str):
                properties[param_name] = {"type": "string", "description": param_type}
            else:
                properties[param_name] = {"type": "string"}
        result.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": list(properties.keys()),
                },
            }
        })
    return result


def _tools_to_anthropic_schema(tools: list) -> list:
    """Convert tools.yaml-style list to Anthropic tool schema."""
    result = []
    for tool in tools:
        params = tool.get("parameters", {})
        properties = {}
        for param_name, param_type in params.items():
            if isinstance(param_type, str):
                properties[param_name] = {"type": "string", "description": param_type}
            else:
                properties[param_name] = {"type": "string"}
        result.append({
            "name": tool["name"],
            "description": tool.get("description", ""),
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": list(properties.keys()),
            },
        })
    return result


# --- Public API ---

def call_llm(system_prompt: str, user_prompt: str,
             provider: str = "openai", model: str = "gpt-4o",
             api_key: Optional[str] = None,
             tools: Optional[list] = None) -> "str | dict":
    """Call an LLM and return the response text (or a tool-call dict).

    Provider: 'openai', 'anthropic', 'deepseek', or 'google' / 'gemini'.
    Includes exponential backoff on transient errors (429, 5xx).

    If tools is provided and the model returns a tool call, returns:
      {"tool_call": {"name": ..., "arguments": {...}}}
    Otherwise returns a plain str.
    """
    _load_hermes_env()

    prov = provider.lower()
    if prov == "openai":
        return _call_openai(system_prompt, user_prompt, model, api_key, tools)
    elif prov == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, model, api_key, tools)
    elif prov == "deepseek":
        return _call_deepseek(system_prompt, user_prompt, model, api_key, tools)
    elif prov in ("google", "gemini"):
        return _call_google(system_prompt, user_prompt, model, api_key, tools)
    else:
        from forge.core.engine import ForgeError
        raise ForgeError(f"Unknown provider: {provider}")


# --- Provider implementations ---

def _call_openai(system: str, user: str, model: str, api_key: Optional[str],
                 tools: Optional[list] = None) -> "str | dict":
    import openai

    key = api_key or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    ck = _cache_key("openai", base_url, key)

    if ck not in _client_cache:
        _client_cache[ck] = openai.OpenAI(api_key=key)

    params: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if not _is_reasoning_model(model):
        params["temperature"] = 0.7
    if tools:
        params["tools"] = _tools_to_openai_schema(tools)
        params["tool_choice"] = "auto"

    def _do():
        try:
            resp = _client_cache[ck].chat.completions.create(**params)
            msg = resp.choices[0].message
            if msg.tool_calls:
                tc = msg.tool_calls[0]
                return {"tool_call": {"name": tc.function.name, "arguments": json.loads(tc.function.arguments)}}
            return msg.content
        except (openai.APIConnectionError, openai.APITimeoutError) as e:
            if base_url:
                logger.warning("OpenAI proxy %s failed (%s). Falling back to official API.", base_url, e)
                fallback = openai.OpenAI(api_key=key, base_url="https://api.openai.com/v1")
                _client_cache[ck] = fallback
                resp = fallback.chat.completions.create(**params)
                msg = resp.choices[0].message
                if msg.tool_calls:
                    tc = msg.tool_calls[0]
                    return {"tool_call": {"name": tc.function.name, "arguments": json.loads(tc.function.arguments)}}
                return msg.content
            raise

    return _llm_call_with_retry(_do)


def _call_anthropic(system: str, user: str, model: str, api_key: Optional[str],
                    tools: Optional[list] = None) -> "str | dict":
    import anthropic

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    ck = _cache_key("anthropic", base_url, key)

    if ck not in _client_cache:
        _client_cache[ck] = anthropic.Anthropic(api_key=key)

    create_kwargs: dict = {
        "model": model,
        "max_tokens": 4096,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if tools:
        create_kwargs["tools"] = _tools_to_anthropic_schema(tools)

    def _do():
        try:
            resp = _client_cache[ck].messages.create(**create_kwargs)
            for block in resp.content:
                if block.type == "tool_use":
                    return {"tool_call": {"name": block.name, "arguments": block.input}}
            return resp.content[0].text
        except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
            if base_url:
                logger.warning("Anthropic proxy %s failed (%s). Falling back to official API.", base_url, e)
                fallback = anthropic.Anthropic(api_key=key, base_url="https://api.anthropic.com")
                _client_cache[ck] = fallback
                resp = fallback.messages.create(**create_kwargs)
                for block in resp.content:
                    if block.type == "tool_use":
                        return {"tool_call": {"name": block.name, "arguments": block.input}}
                return resp.content[0].text
            raise

    return _llm_call_with_retry(_do)


def _call_deepseek(system: str, user: str, model: str, api_key: Optional[str],
                   tools: Optional[list] = None) -> "str | dict":
    import openai

    key = api_key or os.environ.get("DEEPSEEK_API_KEY")
    base_url = os.environ.get("DEEPSEEK_API_BASE")
    ck = _cache_key("deepseek", base_url, key)

    if ck not in _client_cache:
        _client_cache[ck] = openai.OpenAI(api_key=key, base_url=base_url)

    params: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if not _is_reasoning_model(model):
        params["temperature"] = 0.7
    if tools:
        params["tools"] = _tools_to_openai_schema(tools)
        params["tool_choice"] = "auto"

    def _do():
        try:
            resp = _client_cache[ck].chat.completions.create(**params)
            msg = resp.choices[0].message
            if msg.tool_calls:
                tc = msg.tool_calls[0]
                return {"tool_call": {"name": tc.function.name, "arguments": json.loads(tc.function.arguments)}}
            return msg.content
        except (openai.APIConnectionError, openai.APITimeoutError) as e:
            if base_url:
                logger.warning("DeepSeek proxy %s failed (%s). Falling back to official API.", base_url, e)
                fallback = openai.OpenAI(api_key=key, base_url="https://api.deepseek.com/v1")
                _client_cache[ck] = fallback
                resp = fallback.chat.completions.create(**params)
                msg = resp.choices[0].message
                if msg.tool_calls:
                    tc = msg.tool_calls[0]
                    return {"tool_call": {"name": tc.function.name, "arguments": json.loads(tc.function.arguments)}}
                return msg.content
            raise

    return _llm_call_with_retry(_do)


def _call_google(system: str, user: str, model: str, api_key: Optional[str],
                 tools: Optional[list] = None) -> "str | dict":
    import google.generativeai as genai

    genai.configure(api_key=api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))

    model_name = model if model.startswith("models/") else f"models/{model}"
    ck = _cache_key("google", model_name, api_key)

    if ck not in _client_cache:
        _client_cache[ck] = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system
        )

    def _do():
        resp = _client_cache[ck].generate_content(user)
        for part in resp.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                return {"tool_call": {"name": fc.name, "arguments": dict(fc.args)}}
        return resp.text

    return _llm_call_with_retry(_do)
