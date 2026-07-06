import json
import pytest
import os
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from forge.core.llm import _call_google

@patch("urllib.request.urlopen")
def test_call_google_rest_fallback(mock_urlopen, monkeypatch):
    # Ensure GEMINI_API_KEY is in environment
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-key")
    
    # Force SDK import failure to trigger HTTP fallback
    with patch.dict("sys.modules", {"google.generativeai": None}):
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Hello from Gemini HTTP fallback!"}
                        ]
                    }
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = _call_google(
            system="You are a helper.",
            user="Say hello.",
            model="gemini-1.5-flash",
            api_key=None,
            temperature=0.4
        )

        assert res == "Hello from Gemini HTTP fallback!"
        
        # Verify the requested URL contained correct model and api key query param
        args, kwargs = mock_urlopen.call_args
        request_obj = args[0]
        assert "models/gemini-1.5-flash" in request_obj.full_url
        assert "key=mock-gemini-key" in request_obj.full_url
        
        # Verify post payload
        posted_data = json.loads(request_obj.data.decode("utf-8"))
        assert posted_data["contents"][0]["parts"][0]["text"] == "Say hello."
        assert posted_data["systemInstruction"]["parts"][0]["text"] == "You are a helper."
        assert posted_data["generationConfig"]["temperature"] == 0.4


@patch("urllib.request.urlopen")
def test_call_google_rest_tool_call(mock_urlopen, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-key")
    
    with patch.dict("sys.modules", {"google.generativeai": None}):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "functionCall": {
                                    "name": "get_weather",
                                    "args": {"city": "Stockholm"}
                                }
                            }
                        ]
                    }
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        tools = [
            {
                "name": "get_weather",
                "description": "Get current weather",
                "parameters": {
                    "city": "The city name"
                }
            }
        ]

        res = _call_google(
            system="Help with tools.",
            user="What's the weather in Stockholm?",
            model="gemini-1.5-flash",
            api_key=None,
            tools=tools
        )

        assert isinstance(res, dict)
        assert res["tool_call"]["name"] == "get_weather"
        assert res["tool_call"]["arguments"] == {"city": "Stockholm"}


def test_call_google_missing_key(monkeypatch):
    # Ensure keys are absent
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    from forge.core.engine import ForgeError
    with pytest.raises(ForgeError, match="No Gemini API key found"):
        _call_google(system="sys", user="user", model="gemini-1.5-flash", api_key=None)


@patch("forge.core.llm._call_deepseek", return_value="redirection successful")
def test_deepseek_chat_redirection(mock_call, monkeypatch):
    from forge.core.llm import call_llm
    
    # Disable LLM caching to hit our provider call directly
    monkeypatch.setenv("FORGE_DISABLE_CACHE", "1")
    
    res = call_llm(
        system_prompt="sys",
        user_prompt="user",
        provider="deepseek",
        model="deepseek-chat"
    )
    
    assert res == "redirection successful"
    mock_call.assert_called_once()
    called_args, called_kwargs = mock_call.call_args
    # Third parameter should be "deepseek-v4-flash" instead of "deepseek-chat"
    assert called_args[2] == "deepseek-v4-flash"
