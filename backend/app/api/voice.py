import asyncio
import base64
import json
import logging
import re
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai.types import (
    AudioTranscriptionConfig,
    RealtimeInputConfig,
    AutomaticActivityDetection,
    StartSensitivity,
    EndSensitivity,
    Blob,
    GenerateContentResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Import word segmentation library
try:
    from wordsegment import load, segment
    # Load the word segmentation data (this only needs to be done once)
    load()
    WORDSEGMENT_AVAILABLE = True
    logger.info("WordSegment library loaded successfully")
except ImportError:
    WORDSEGMENT_AVAILABLE = False
    logger.warning("WordSegment library not available, using fallback segmentation")


def segment_text_without_spaces(text: str) -> str:
    """
    Segment text without spaces into properly spaced words using advanced word segmentation.
    
    Args:
        text: Input text without proper spacing (e.g., "thisisatest")
        
    Returns:
        Properly spaced text (e.g., "this is a test")
    """
    if not text or not text.strip():
        return text
    
    original_text = text.strip()
    
    # Check if text contains only ASCII English characters
    if not original_text.isascii():
        logger.warning(f"Non-ASCII text detected, skipping segmentation: '{original_text}'")
        return original_text
    
    
    # Check if text already has reasonable spacing (more than 50% words separated)
    words_with_spaces = len(original_text.split())
    if words_with_spaces > 1 and len(original_text) / words_with_spaces < 8:
        logger.debug(f"Text already has reasonable spacing: '{original_text}'")
        return original_text
    
    # Remove extra whitespace and convert to lowercase for processing
    clean_text = re.sub(r'\s+', '', original_text.lower())
    
    # Skip very short text
    if len(clean_text) < 3:
        return original_text
    
    # Remove punctuation for segmentation, but preserve it
    punctuation_pattern = r'([.!?,:;])'
    punctuation_parts = re.split(punctuation_pattern, clean_text)
    
    segmented_parts = []
    
    for part in punctuation_parts:
        if not part:
            continue
            
        # If it's punctuation, keep it as is
        if re.match(punctuation_pattern, part):
            segmented_parts.append(part)
            continue
            
        # Apply word segmentation only to English text
        if WORDSEGMENT_AVAILABLE and len(part) > 1 and part.isalpha():
            try:
                # Use wordsegment library for intelligent word segmentation
                segmented_words = segment(part)
                segmented_parts.append(' '.join(segmented_words))
                logger.debug(f"WordSegment: '{part}' -> '{' '.join(segmented_words)}'")
            except Exception as e:
                logger.warning(f"WordSegment failed for '{part}': {e}, using fallback")
                segmented_parts.append(fallback_word_segmentation(part))
        else:
            # Fallback segmentation using regex patterns
            segmented_parts.append(fallback_word_segmentation(part))
    
    # Join the parts and clean up spacing
    result = ''.join(segmented_parts)
    
    # Clean up spacing around punctuation
    result = re.sub(r'\s+([.!?,:;])', r'\1', result)  # Remove space before punctuation
    result = re.sub(r'([.!?])\s*', r'\1 ', result)    # Ensure space after sentence endings
    result = re.sub(r'\s+', ' ', result)              # Clean up multiple spaces
    
    return result.strip()


def fallback_word_segmentation(text: str) -> str:
    """
    Fallback word segmentation using regex patterns when wordsegment is not available.
    
    Args:
        text: Input text without spaces
        
    Returns:
        Text with basic word boundaries added
    """
    if not text:
        return text
    
    # Basic word boundary patterns
    result = text
    
    # Add space before capital letters (camelCase -> camel Case)
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', result)
    
    # Add space between letters and numbers
    result = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', result)
    result = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', result)
    
    # Add space after common word endings
    result = re.sub(r'(ing|tion|ness|ment|able|ible)([a-z])', r'\1 \2', result)
    
    # Add space before common word beginnings
    result = re.sub(r'([a-z])(the|and|or|in|on|at|to|for|of|with|by|from|is|are|was|were|be|been|have|has|had|do|does|did|will|would|could|should|may|might|can|cannot)', r'\1 \2', result)
    
    # Clean up multiple spaces
    result = re.sub(r'\s+', ' ', result)
    
    return result.strip()

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
        response_modalities=["AUDIO"],  # Audio only - text comes via transcription configs
        input_audio_transcription=AudioTranscriptionConfig(),
        output_audio_transcription=AudioTranscriptionConfig(),  # This enables text transcription
        realtime_input_config=RealtimeInputConfig(
            # Configure Voice Activity Detection to reduce AI interruptions
            automatic_activity_detection=AutomaticActivityDetection(
                # Lower sensitivity to end of speech - makes AI wait longer before responding
                end_of_speech_sensitivity=EndSensitivity.END_SENSITIVITY_LOW,
                # Require longer silence before considering speech ended (default is ~700ms, increase to 1.5s)
                silence_duration_ms=1500,
                # Higher sensitivity to start of speech - detect user speech quickly
                start_of_speech_sensitivity=StartSensitivity.START_SENSITIVITY_HIGH,
                # Add some padding to capture beginning of speech
                prefix_padding_ms=300
            )
        ),
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
        # Text accumulation for complete sentence word segmentation
        accumulated_user_text = ""
        accumulated_assistant_text = ""
        
        try:
            async for event in live_events:
                # Debug: Only log events with assistant content for now
                author = getattr(event, 'author', None)
                has_assistant_content = (hasattr(event, 'content') and event.content and 
                                       hasattr(event.content, 'parts') and 
                                       str(author).lower() == 'model')
                
                if has_assistant_content:
                    logger.info(f"[ASSISTANT EVENT] Author: {author}, turn_complete: {getattr(event, 'turn_complete', None)}, interrupted: {getattr(event, 'interrupted', None)}")
                
                # Check author field to distinguish user vs assistant
                author = getattr(event, 'author', None)
                is_user_event = (hasattr(event, 'author') and event.author and 
                               ('user' in str(event.author).lower() or 'input' in str(event.author).lower()))
                
                # Handle ADK event content structure  
                if hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        # Handle text parts
                        if hasattr(part, "text") and part.text:
                            # Determine role based on event analysis
                            role = "user" if is_user_event else "assistant"
                            
                            # Accumulate text chunks without sending to frontend immediately
                            text_chunk = part.text.strip()
                            if role == "user":
                                accumulated_user_text += text_chunk
                                logger.info(f"User text accumulated: '{accumulated_user_text}'")
                            else:
                                # Accumulate assistant text but don't send yet - wait for turn completion
                                accumulated_assistant_text += text_chunk
                                logger.info(f"Assistant text accumulated: '{accumulated_assistant_text}'")
                        
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
                
                # Check for additional transcription fields
                user_transcription_fields = ['transcription', 'input_transcription', 'user_transcription', 'input_text']
                for field_name in user_transcription_fields:
                    if hasattr(event, field_name):
                        field_value = getattr(event, field_name)
                        if field_value:
                            accumulated_user_text += str(field_value).strip()
                
                # Send turn completion signal and apply word segmentation to complete text
                if hasattr(event, 'turn_complete') and event.turn_complete:
                    logger.info(f"[TURN COMPLETE] Processing turn completion with user: '{accumulated_user_text}', assistant: '{accumulated_assistant_text}'")
                    # Process complete accumulated text with word segmentation
                    if accumulated_user_text:
                        segmented_user_text = segment_text_without_spaces(accumulated_user_text)
                        
                        # Send segmented complete user text
                        complete_message = {
                            "mime_type": "text/plain",
                            "role": "user",
                            "data": segmented_user_text,
                            "complete": True
                        }
                        await websocket.send_text(json.dumps(complete_message))
                        accumulated_user_text = ""  # Reset for next turn
                    
                    if accumulated_assistant_text:
                        segmented_assistant_text = segment_text_without_spaces(accumulated_assistant_text)
                        
                        # Send segmented complete assistant text
                        complete_message = {
                            "mime_type": "text/plain",
                            "role": "assistant", 
                            "data": segmented_assistant_text,
                            "complete": True
                        }
                        await websocket.send_text(json.dumps(complete_message))
                        accumulated_assistant_text = ""  # Reset for next turn
                    
                    # Send turn completion signal
                    await websocket.send_text(json.dumps({"turn_complete": True}))

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