from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Tuple

router = APIRouter()

@router.websocket("/voice")
async def voice_stream(websocket: WebSocket) -> None:
    """WebSocket endpoint for bidirectional voice streaming."""
    await websocket.accept()
    # Access ADK service from app state
    adk_service = getattr(websocket.app.state, "adk_service", None)
    try:
        # First message expected to be auth token
        await websocket.receive_text()
        while True:
            audio_in = await websocket.receive_bytes()
            if adk_service is None:
                # Fallback to text when service unavailable
                await websocket.send_text("Voice service unavailable")
                continue
            success, result = await adk_service.stream_voice(audio_in)
            if success:
                await websocket.send_bytes(result)
            else:
                await websocket.send_text(result)
    except WebSocketDisconnect:
        return
