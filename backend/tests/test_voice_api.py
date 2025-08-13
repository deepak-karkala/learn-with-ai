"""Tests for voice streaming WebSocket endpoint."""

import asyncio
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.services.adk_service import ADKService
from google.genai.types import Blob, Content, Part


class DummySession:
    pass


class DummySessionService:
    async def create_session(self, app_name: str, user_id: str, state: dict, session_id: str | None = None):
        return DummySession()


class AudioRunner:
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
    def run_live(self, *, session, live_request_queue, run_config):
        async def generator():
            content = Content(parts=[Part.from_text(text="fallback")])
            event = type("Event", (), {"content": content, "turn_complete": True})
            yield event
        return generator()


class TestVoiceAPI:
    """Test cases for the /api/voice WebSocket endpoint."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_voice_streaming(self, monkeypatch):
        service = ADKService()
        monkeypatch.setattr(service, "_get_or_create_runner", AsyncMock(return_value=AudioRunner()))
        app.state.adk_service = service

        with self.client.websocket_connect("/api/voice") as websocket:
            websocket.send_text("auth_token_here")
            websocket.send_bytes(b"audio_in")
            response = websocket.receive_bytes()
            assert response == b"audio_out"

    def test_voice_streaming_fallback(self, monkeypatch):
        service = ADKService()
        monkeypatch.setattr(service, "_get_or_create_runner", AsyncMock(return_value=TextRunner()))
        app.state.adk_service = service

        with self.client.websocket_connect("/api/voice") as websocket:
            websocket.send_text("auth_token_here")
            websocket.send_bytes(b"audio_in")
            text = websocket.receive_text()
            assert "fallback" in text
