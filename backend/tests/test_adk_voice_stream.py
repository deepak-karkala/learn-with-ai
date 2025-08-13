"""Integration tests for ADKService.stream_voice"""

import asyncio
from unittest.mock import AsyncMock

from app.services.adk_service import ADKService
from google.genai.types import Blob, Content, Part


class DummySession:
    pass


class DummySessionService:
    async def create_session(self, app_name: str, user_id: str, state: dict, session_id: str | None = None):
        return DummySession()


class DummyQueue:
    def send_realtime(self, blob):
        pass
    
    def close(self):
        pass


class AudioRunner:
    """Runner that yields an audio response"""

    def __init__(self):
        self.session_service = DummySessionService()

    def run_live(self, *, session, live_request_queue, run_config):
        async def generator():
            blob = Blob(data=b"audio_out", mime_type="audio/wav")
            content = Content(parts=[Part(inline_data=blob)])
            event = type("Event", (), {"content": content, "turn_complete": True})
            yield event
        return generator()


class TextRunner(AudioRunner):
    """Runner that yields only text"""

    def run_live(self, *, session, live_request_queue, run_config):
        async def generator():
            content = Content(parts=[Part.from_text(text="no audio")])
            event = type("Event", (), {"content": content, "turn_complete": True})
            yield event
        return generator()


def test_stream_voice_returns_audio(monkeypatch):
    service = ADKService()
    monkeypatch.setattr(service, "_get_or_create_runner", AsyncMock(return_value=AudioRunner()))
    monkeypatch.setattr(service, "_get_or_create_queue", AsyncMock(return_value=DummyQueue()))
    success, payload = asyncio.run(service.stream_voice(b"audio_in"))
    assert success is True
    assert payload == b"audio_out"


def test_stream_voice_fallback_to_text(monkeypatch):
    service = ADKService()
    monkeypatch.setattr(service, "_get_or_create_runner", AsyncMock(return_value=TextRunner()))
    monkeypatch.setattr(service, "_get_or_create_queue", AsyncMock(return_value=DummyQueue()))
    success, payload = asyncio.run(service.stream_voice(b"audio_in"))
    assert success is False
    assert "no audio" in payload
