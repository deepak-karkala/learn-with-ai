from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/voice")
async def voice_stream(websocket: WebSocket) -> None:
    """WebSocket endpoint for bidirectional voice streaming."""
    await websocket.accept()
    # Access ADK service from app state
    adk_service = getattr(websocket.app.state, "adk_service", None)

    try:
        while True:
            message = await websocket.receive()

            # Client disconnected
            if message.get("type") == "websocket.disconnect":
                break

            # Ignore text frames (e.g., auth tokens or keep-alives)
            if message.get("text") is not None:
                continue

            audio_in = message.get("bytes")
            if not audio_in:
                continue

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
