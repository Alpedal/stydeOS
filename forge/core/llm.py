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

# ponytail: per-call token tracking, latest call's usage stored here
_last_token_usage: dict = {}


def _load_hermes_env() -> None:
    """Load API keys from local hermes .env if they are missing in os.environ."""
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("ANTHROPIC_API_KEY") or not os.environ.get("DEEPSEEK_API_KEY") or not os.environ.get("GEMINI_API_KEY") or not os.environ.get("GOOGLE_API_KEY"):
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
             tools: Optional[list] = None,
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None,
             top_p: Optional[float] = None) -> "str | dict":
    """Call an LLM and return the response text (or a tool-call dict).

    Provider: 'openai', 'anthropic', 'deepseek', or 'google' / 'gemini'.
    Includes exponential backoff on transient errors (429, 5xx) and disk-based caching.

    If tools is provided and the model returns a tool call, returns:
      {"tool_call": {"name": ..., "arguments": {...}}}
    Otherwise returns a plain str.
    """
    _load_hermes_env()

    _last_token_usage.clear()

    if provider.lower() == "deepseek" and model == "deepseek-chat":
        model = "deepseek-v4-flash"

    # Try retrieving from disk cache first
    from forge.core.llm_cache import get_cached_response, set_cached_response
    root = Path(__file__).resolve().parent.parent.parent
    cached = get_cached_response(
        root=root,
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        tools=tools,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p
    )
    if cached is not None:
        return cached

    prov = provider.lower()
    if prov == "openai":
        res = _call_openai(system_prompt, user_prompt, model, api_key, tools, temperature, max_tokens, top_p)
    elif prov == "anthropic":
        res = _call_anthropic(system_prompt, user_prompt, model, api_key, tools, temperature, max_tokens, top_p)
    elif prov == "deepseek":
        res = _call_deepseek(system_prompt, user_prompt, model, api_key, tools, temperature, max_tokens, top_p)
    elif prov in ("google", "gemini"):
        res = _call_google(system_prompt, user_prompt, model, api_key, tools, temperature, max_tokens, top_p)
    else:
        from forge.core.engine import ForgeError
        raise ForgeError(f"Unknown provider: {provider}")

    # Save to disk cache
    set_cached_response(
        root=root,
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response=res,
        tools=tools,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p
    )
    return res


# --- Provider implementations ---

def _call_openai(system: str, user: str, model: str, api_key: Optional[str],
                 tools: Optional[list] = None,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None,
                 top_p: Optional[float] = None) -> "str | dict":
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

    # Configuration params (strip unsupported ones for reasoning models)
    is_reasoning = _is_reasoning_model(model)
    if not is_reasoning:
        params["temperature"] = temperature if temperature is not None else 0.7
        if top_p is not None:
            params["top_p"] = top_p
    if max_tokens is not None:
        if is_reasoning:
            params["max_completion_tokens"] = max_tokens
        else:
            params["max_tokens"] = max_tokens

    if tools:
        params["tools"] = _tools_to_openai_schema(tools)
        params["tool_choice"] = "auto"

    def _do():
        try:
            resp = _client_cache[ck].chat.completions.create(**params)
            msg = resp.choices[0].message
            _capture_usage(resp)
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
                _capture_usage(resp)
                if msg.tool_calls:
                    tc = msg.tool_calls[0]
                    return {"tool_call": {"name": tc.function.name, "arguments": json.loads(tc.function.arguments)}}
                return msg.content
            raise

    return _llm_call_with_retry(_do)


def _call_anthropic(system: str, user: str, model: str, api_key: Optional[str],
                    tools: Optional[list] = None,
                    temperature: Optional[float] = None,
                    max_tokens: Optional[int] = None,
                    top_p: Optional[float] = None) -> "str | dict":
    import anthropic

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    ck = _cache_key("anthropic", base_url, key)

    if ck not in _client_cache:
        _client_cache[ck] = anthropic.Anthropic(api_key=key)

    create_kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens if max_tokens is not None else 4096,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if temperature is not None:
        create_kwargs["temperature"] = temperature
    if top_p is not None:
        create_kwargs["top_p"] = top_p
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
                   tools: Optional[list] = None,
                   temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None,
                   top_p: Optional[float] = None) -> "str | dict":
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

    # Configuration params (strip unsupported ones for reasoning models)
    is_reasoning = _is_reasoning_model(model)
    if not is_reasoning:
        params["temperature"] = temperature if temperature is not None else 0.7
        if top_p is not None:
            params["top_p"] = top_p
    if max_tokens is not None:
        if is_reasoning:
            params["max_completion_tokens"] = max_tokens
        else:
            params["max_tokens"] = max_tokens

    if tools:
        params["tools"] = _tools_to_openai_schema(tools)
        params["tool_choice"] = "auto"

    def _do():
        try:
            resp = _client_cache[ck].chat.completions.create(**params)
            msg = resp.choices[0].message
            _capture_usage(resp)
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
                _capture_usage(resp)
                if msg.tool_calls:
                    tc = msg.tool_calls[0]
                    return {"tool_call": {"name": tc.function.name, "arguments": json.loads(tc.function.arguments)}}
                return msg.content
            raise

    return _llm_call_with_retry(_do)


def _call_google(system: str, user: str, model: str, api_key: Optional[str],
                 tools: Optional[list] = None,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None,
                 top_p: Optional[float] = None) -> "str | dict":
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        from forge.core.engine import ForgeError
        raise ForgeError("No Gemini API key found (please set GEMINI_API_KEY or GOOGLE_API_KEY)")

    # Normalize model name
    raw_model = model
    if not raw_model.startswith("models/"):
        raw_model = f"models/{raw_model}"

    try:
        import google.generativeai as genai
        # Try utilizing official SDK
        genai.configure(api_key=key)
        model_name = raw_model
        ck = _cache_key("google", model_name, key)
        if ck not in _client_cache:
            _client_cache[ck] = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system
            )
        config_args = {}
        if temperature is not None:
            config_args["temperature"] = temperature
        if max_tokens is not None:
            config_args["max_output_tokens"] = max_tokens
        if top_p is not None:
            config_args["top_p"] = top_p

        def _do_sdk():
            config = genai.types.GenerationConfig(**config_args) if config_args else None
            resp = _client_cache[ck].generate_content(user, generation_config=config)
            if not resp.candidates:
                return ""
            for part in resp.candidates[0].content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    return {"tool_call": {"name": fc.name, "arguments": dict(fc.args)}}
            return resp.text

        return _llm_call_with_retry(_do_sdk)

    except ImportError:
        # Fallback to direct HTTP REST API calls using standard library
        import urllib.request
        import urllib.error

        url = f"https://generativelanguage.googleapis.com/v1beta/{raw_model}:generateContent?key={key}"
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": user}]
                }
            ]
        }
        if system:
            payload["systemInstruction"] = {
                "parts": [{"text": system}]
            }
            
        generation_config = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens
        if top_p is not None:
            generation_config["topP"] = top_p
            
        if generation_config:
            payload["generationConfig"] = generation_config

        if tools:
            gemini_tools = []
            for t in tools:
                props = {}
                for param_name, param_type in t.get("parameters", {}).items():
                    props[param_name] = {
                        "type": "STRING",
                        "description": param_type if isinstance(param_type, str) else ""
                    }
                gemini_tools.append({
                    "functionDeclarations": [{
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": {
                            "type": "OBJECT",
                            "properties": props,
                            "required": list(props.keys())
                        }
                    }]
                })
            payload["tools"] = gemini_tools

        data_bytes = json.dumps(payload).encode("utf-8")
        
        def _do_http():
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    resp_data = json.loads(response.read().decode("utf-8"))
                
                candidates = resp_data.get("candidates", [])
                if not candidates:
                    return ""
                
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    return ""
                
                for part in parts:
                    if "functionCall" in part:
                        fc = part["functionCall"]
                        return {"tool_call": {"name": fc["name"], "arguments": fc.get("args", {})}}
                    if "text" in part:
                        return part["text"]
                return ""
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8")
                raise RuntimeError(f"Gemini API returned error {e.code}: {err_body}")

        return _llm_call_with_retry(_do_http)


# --- Token tracking & cost estimation (ponytail: global state, simple) ---

# ponytail: per-model pricing ($/1M tokens)
_PRICES = {
    "deepseek-chat":       (0.27, 1.10),
    "deepseek-reasoner":   (0.55, 2.19),
    "gpt-4o":              (2.50, 10.00),
    "gpt-4o-mini":         (0.15, 0.60),
    "claude-sonnet-4-20250514": (3.00, 15.00),
    "claude-3-5-haiku":    (0.80, 4.00),
    "gemini-2.5-flash":    (0.15, 0.60),
    "gemini-2.5-pro":      (1.25, 10.00),
}

def _capture_usage(resp) -> None:
    """Extract token usage from API response into _last_token_usage."""
    try:
        u = resp.usage
        _last_token_usage["prompt_tokens"] = u.prompt_tokens
        _last_token_usage["completion_tokens"] = u.completion_tokens
    except Exception:
        pass

def get_last_token_usage() -> dict:
    """Return token usage from the most recent API call."""
    return dict(_last_token_usage)

def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate USD cost based on model pricing."""
    default = (2.50, 10.00)
    input_price, output_price = _PRICES.get(model, default)
    for key, (ip, op) in _PRICES.items():
        if key in model:
            input_price, output_price = ip, op
            break
    return round((prompt_tokens / 1_000_000) * input_price + (completion_tokens / 1_000_000) * output_price, 6)

