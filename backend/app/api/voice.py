import asyncio
import base64
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai.types import (
    AudioTranscriptionConfig,
    RealtimeInputConfig,
    Blob,
    GenerateContentResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/voice")
async def voice_stream(websocket: WebSocket):
    """WebSocket endpoint for bidirectional voice streaming using ADK Live API."""
    await websocket.accept()
    adk_service = getattr(websocket.app.state, "adk_service", None)
    if not adk_service or not adk_service.agent:
        logger.error("ADK service or agent not available.")
        await websocket.close(code=1011, reason="Voice service unavailable")
        return

    user_id = "voice_user"  # This can be replaced with actual user auth
    session_id = f"{user_id}_session_{int(asyncio.get_event_loop().time())}"
    
    runner = await adk_service._get_or_create_runner(user_id)
    session = await runner.session_service.create_session(
        app_name=adk_service.app_name, user_id=user_id, state={}, session_id=session_id
    )
    
    # Configure for ADK Live API with voice-enabled model (fix for 1007 error)
    run_config = RunConfig(
        response_modalities=["AUDIO"],  # Audio only - text comes via output_audio_transcription
        input_audio_transcription=AudioTranscriptionConfig(),
        output_audio_transcription=AudioTranscriptionConfig(),  # This enables text transcription
        realtime_input_config=RealtimeInputConfig(),
        streaming_mode=StreamingMode.BIDI,
    )

    live_request_queue = await adk_service._get_or_create_queue(session_id)
    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )

    async def client_to_agent_messaging():
        try:
            # No explicit activity control - let automatic activity detection handle it
            while True:
                # Receive JSON message from client (as per ADK docs)
                message_text = await websocket.receive_text()
                message = json.loads(message_text)
                logger.info(f"Received message: {message['mime_type']}")
                
                if message["mime_type"].startswith("audio/pcm"):
                    # Decode Base64 PCM audio data
                    audio_data = base64.b64decode(message["data"])
                    logger.info(f"Decoded PCM audio ({message['mime_type']}): {len(audio_data)} bytes")
                    
                    # Create blob and send to ADK Live API with the exact MIME type
                    blob = Blob(data=audio_data, mime_type=message["mime_type"])
                    live_request_queue.send_realtime(blob)
                    
                elif message["mime_type"] == "text/plain":
                    # Handle text message (if needed)
                    logger.info(f"Received text: {message['data']}")
                    # Could send text to ADK here if needed
                
        except WebSocketDisconnect:
            logger.info(f"Client disconnected from session {session_id}")
        except Exception as e:
            logger.error(f"Error in client-to-agent messaging: {e}")
        finally:
            # Just close the queue - no explicit activity end needed
            live_request_queue.close()

    async def agent_to_client_messaging():
        """Agent to client communication"""
        try:
            async for event in live_events:
                # Handle server_content structure (primary path for Live API)
                if hasattr(event, 'server_content') and event.server_content:
                    server_content = event.server_content
                    
                    # Handle output transcription (text)
                    if hasattr(server_content, 'output_transcription') and server_content.output_transcription:
                        text_content = server_content.output_transcription
                        message = {
                            "mime_type": "text/plain",
                            "data": str(text_content).strip()
                        }
                        await websocket.send_text(json.dumps(message))
                        logger.info(f"Sent transcription text: {str(text_content)[:50]}...")
                    
                    # Handle model_turn with parts (audio/text)
                    if hasattr(server_content, 'model_turn') and server_content.model_turn:
                        model_turn = server_content.model_turn
                        
                        if hasattr(model_turn, 'parts') and model_turn.parts:
                            for part in model_turn.parts:
                                # Handle audio parts with inline_data
                                if hasattr(part, "inline_data") and part.inline_data:
                                    mime_type = getattr(part.inline_data, "mime_type", "")
                                    if mime_type.startswith("audio"):
                                        audio_data = getattr(part.inline_data, "data", b"")
                                        if audio_data:
                                            base64_audio = base64.b64encode(audio_data).decode('utf-8')
                                            message = {
                                                "mime_type": "audio/pcm",
                                                "data": base64_audio
                                            }
                                            await websocket.send_text(json.dumps(message))
                                            logger.info(f"Sent audio from model_turn: {len(audio_data)} bytes")
                
                # Handle content.parts structure (fallback)
                elif hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        # Handle text parts
                        if hasattr(part, "text") and part.text:
                            message = {
                                "mime_type": "text/plain",
                                "data": part.text.strip()
                            }
                            await websocket.send_text(json.dumps(message))
                            logger.info(f"Sent text: {part.text[:50]}...")
                        
                        # Handle audio parts  
                        elif hasattr(part, "inline_data") and part.inline_data:
                            mime_type = getattr(part.inline_data, "mime_type", "")
                            if mime_type.startswith("audio"):
                                audio_data = getattr(part.inline_data, "data", b"")
                                if audio_data:
                                    base64_audio = base64.b64encode(audio_data).decode('utf-8')
                                    message = {
                                        "mime_type": "audio/pcm",
                                        "data": base64_audio
                                    }
                                    await websocket.send_text(json.dumps(message))
                                    logger.info(f"Sent audio: {len(audio_data)} bytes")
                
                # Send turn completion signal
                if hasattr(event, 'turn_complete') and event.turn_complete:
                    message = {
                        "turn_complete": True
                    }
                    await websocket.send_text(json.dumps(message))
                    logger.info("Sent turn_complete signal")

        except Exception as e:
            logger.error(f"Error in agent-to-client messaging: {e}")
        finally:
            if websocket.client_state.name == 'CONNECTED':
                await websocket.close()
            await adk_service._cleanup_queue(session_id)

    client_to_agent_task = asyncio.create_task(client_to_agent_messaging())
    agent_to_client_task = asyncio.create_task(agent_to_client_messaging())

    done, pending = await asyncio.wait(
        [client_to_agent_task, agent_to_client_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()