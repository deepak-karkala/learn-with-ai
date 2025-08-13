"""Tests for voice streaming WebSocket endpoint."""

import asyncio
import json
import base64
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


class DummyQueue:
    def send_realtime(self, blob):
        pass
    
    def close(self):
        pass


class AudioRunner:
    def __init__(self):
        self.session_service = DummySessionService()

    def run_live(self, *, session, live_request_queue, run_config):
        async def generator():
            blob = Blob(data=b"audio_out", mime_type="audio/pcm;rate=24000")
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
        monkeypatch.setattr(service, "_get_or_create_queue", AsyncMock(return_value=DummyQueue()))
        app.state.adk_service = service

        with self.client.websocket_connect("/api/voice") as websocket:
            # Send JSON message as per Gemini Live API format
            audio_message = {
                "mime_type": "audio/pcm;rate=16000",
                "data": base64.b64encode(b"audio_in").decode('utf-8')
            }
            websocket.send_text(json.dumps(audio_message))
            
            # Receive JSON response
            response_text = websocket.receive_text()
            response_data = json.loads(response_text)
            
            assert response_data["mime_type"] == "audio/pcm"
            assert "data" in response_data
            # Decode and verify audio data
            audio_data = base64.b64decode(response_data["data"])
            assert audio_data == b"audio_out"

    def test_voice_streaming_fallback(self, monkeypatch):
        service = ADKService()
        monkeypatch.setattr(service, "_get_or_create_runner", AsyncMock(return_value=TextRunner()))
        monkeypatch.setattr(service, "_get_or_create_queue", AsyncMock(return_value=DummyQueue()))
        app.state.adk_service = service

        with self.client.websocket_connect("/api/voice") as websocket:
            # Send JSON message as per Gemini Live API format
            audio_message = {
                "mime_type": "audio/pcm;rate=16000",
                "data": base64.b64encode(b"audio_in").decode('utf-8')
            }
            websocket.send_text(json.dumps(audio_message))
            
            # Receive JSON text response
            response_text = websocket.receive_text()
            response_data = json.loads(response_text)
            
            assert response_data["mime_type"] == "text/plain"
            assert "fallback" in response_data["data"]
