'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Button } from './ui/button'
import { Mic, Square } from 'lucide-react'

interface VoiceInterfaceProps {
  /**
   * When true, renders a compact inline button suitable for toolbars
   * (e.g. next to the chat send button). Status text and level meter are
   * hidden, but audio playback still functions.
   */
  inline?: boolean
}

export function VoiceInterface({ inline = false }: VoiceInterfaceProps) {
  const [status, setStatus] = useState<'idle' | 'recording' | 'processing'>('idle')
  const [permissionError, setPermissionError] = useState<string | null>(null)
  const socketRef = useRef<WebSocket | null>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const [level, setLevel] = useState(0)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const isPlayingAIAudioRef = useRef(false) // Flag to prevent feedback
  const audioPlaybackQueueRef = useRef<{data: string, timestamp: number}[]>([])
  const isProcessingQueueRef = useRef(false)

  const processAudioQueue = async () => {
    if (isProcessingQueueRef.current || audioPlaybackQueueRef.current.length === 0) {
      return
    }

    isProcessingQueueRef.current = true
    isPlayingAIAudioRef.current = true
    
    console.log(`[AUDIO QUEUE]: Processing ${audioPlaybackQueueRef.current.length} queued audio chunks`)

    while (audioPlaybackQueueRef.current.length > 0 && audioContextRef.current) {
      const audioChunk = audioPlaybackQueueRef.current.shift()
      if (!audioChunk) break

      try {
        const audioData = atob(audioChunk.data)
        const bytes = new Uint8Array(audioData.length)
        for (let i = 0; i < audioData.length; i++) {
          bytes[i] = audioData.charCodeAt(i)
        }
        
        // Use 24kHz as that's what the ADK is sending (audio/pcm;rate=24000)
        const sampleRate = 24000
        
        // Interpret as 16-bit little-endian PCM samples
        const samples = new Int16Array(bytes.buffer)
        const floatSamples = new Float32Array(samples.length)
        
        // Convert 16-bit signed integers to float32 in range [-1, 1]
        for (let i = 0; i < samples.length; i++) {
          floatSamples[i] = samples[i] / 32768.0
        }
        
        // Create and configure audio buffer
        const audioBuffer = audioContextRef.current.createBuffer(1, floatSamples.length, sampleRate)
        audioBuffer.getChannelData(0).set(floatSamples)
        
        // Create source node and play
        const source = audioContextRef.current.createBufferSource()
        source.buffer = audioBuffer
        source.connect(audioContextRef.current.destination)
        
        // Calculate duration
        const audioDuration = floatSamples.length / sampleRate * 1000
        
        console.log(`[AUDIO QUEUE]: Playing chunk ${samples.length} samples, ${audioDuration.toFixed(0)}ms`)
        
        // Wait for this chunk to finish before playing the next one
        await new Promise<void>((resolve) => {
          source.onended = () => {
            console.log(`[AUDIO QUEUE]: Chunk finished playing`)
            resolve()
          }
          source.start(0)
          
          // Fallback timeout in case onended doesn't fire
          setTimeout(resolve, audioDuration + 100)
        })
        
      } catch (err) {
        console.error('Error playing queued audio chunk:', err)
      }
    }
    
    // Clear flags when all chunks are done
    isProcessingQueueRef.current = false
    isPlayingAIAudioRef.current = false
    console.log(`[AUDIO QUEUE]: All chunks processed, cleared feedback flag`)
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
      audioContextRef.current = new AudioCtx()
      const source = audioContextRef.current.createMediaStreamSource(stream)
      analyserRef.current = audioContextRef.current.createAnalyser()
      source.connect(analyserRef.current)

      const wsUrl = process.env.NEXT_PUBLIC_VOICE_WS_URL || 'ws://localhost:8000/api/voice'
      const socket = new WebSocket(wsUrl)
      socket.binaryType = 'arraybuffer'
      socketRef.current = socket

      socket.onopen = async () => {
        setStatus('recording')
        setPermissionError(null)
        
        // Use ScriptProcessorNode for PCM audio capture
        // Note: ScriptProcessorNode is deprecated but widely supported
        // In production, consider using AudioWorklet for better performance
        const processor = audioContextRef.current!.createScriptProcessor(4096, 1, 1)
        source.connect(processor)
        processor.connect(audioContextRef.current!.destination)
        
        processor.onaudioprocess = (event) => {
          // Skip processing if AI is currently speaking to prevent feedback
          if (socket.readyState === WebSocket.OPEN) {
            if (isPlayingAIAudioRef.current) {
              return // Skip sending when AI is speaking
            }
            const inputBuffer = event.inputBuffer
            const inputData = inputBuffer.getChannelData(0) // Get mono audio data
            const sampleRate = audioContextRef.current!.sampleRate
            
            // Always send audio to match the working version (remove voice activity detection for now)
            // Resample to 16kHz if needed (Gemini Live API requirement)
            let resampledData: Float32Array
            if (sampleRate !== 16000) {
              const resampleRatio = 16000 / sampleRate
              const outputLength = Math.floor(inputData.length * resampleRatio)
              resampledData = new Float32Array(outputLength)
              
              for (let i = 0; i < outputLength; i++) {
                const srcIndex = i / resampleRatio
                const srcIndexFloor = Math.floor(srcIndex)
                const srcIndexCeil = Math.min(srcIndexFloor + 1, inputData.length - 1)
                const fraction = srcIndex - srcIndexFloor
                
                // Linear interpolation for resampling
                resampledData[i] = inputData[srcIndexFloor] * (1 - fraction) + inputData[srcIndexCeil] * fraction
              }
            } else {
              resampledData = inputData
            }
            
            // Convert Float32Array to Int16Array (16-bit PCM, little-endian)
            const pcmData = new Int16Array(resampledData.length)
            for (let i = 0; i < resampledData.length; i++) {
              // Clamp to [-1, 1] and convert to 16-bit PCM
              const sample = Math.max(-1, Math.min(1, resampledData[i]))
              pcmData[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
            }
            
            // Convert PCM data to Base64 and send as JSON message (as per Gemini Live API requirements)
            const base64Data = btoa(String.fromCharCode(...new Uint8Array(pcmData.buffer)))
            const message = {
              mime_type: "audio/pcm;rate=16000", // Specify sample rate as required by Gemini Live API
              data: base64Data
            }
            socket.send(JSON.stringify(message))
          }
        }
        
        // Store processor reference for cleanup
        ;(socket as any).processor = processor
      }

      // Handle cleanup when connection closes
      socket.onclose = () => {
        setStatus('idle')
        // Cleanup audio processing
        if ((socket as any).processor) {
          (socket as any).processor.disconnect()
        }
        if (audioContextRef.current) {
          audioContextRef.current.close()
          audioContextRef.current = null
        }
      }

      socket.onmessage = (event: MessageEvent<string>) => {
        const message_from_server = JSON.parse(event.data)
        console.log("[AGENT TO CLIENT] ", message_from_server)

        // Check if the turn is complete
        if (message_from_server.turn_complete && message_from_server.turn_complete == true) {
          console.log("Turn complete")
          return
        }

        // If it's audio, add to queue for sequential playback
        if (message_from_server.mime_type == "audio/pcm" && audioContextRef.current) {
          // Add to queue instead of playing immediately
          audioPlaybackQueueRef.current.push({
            data: message_from_server.data,
            timestamp: Date.now()
          })
          
          // Audio chunk queued for sequential playback
          
          // Start processing the queue if not already processing
          processAudioQueue()
        }

        // Handle text responses without blocking audio input
        if (message_from_server.mime_type == "text/plain") {
          // Text transcription received (logging available if needed)
        }
      }

      socket.onclose = () => {
        setStatus('idle')
      }

      socket.onerror = (err) => {
        console.error('WebSocket error:', err)
        setPermissionError('Connection to voice service failed.')
        setStatus('idle')
      }
    } catch (err) {
      setPermissionError('Microphone access denied')
    }
  }

  const stopRecording = () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      // Cleanup processor
      if ((socketRef.current as any).processor) {
        (socketRef.current as any).processor.disconnect()
      }
      socketRef.current.close()
    }
    // Reset audio feedback prevention flag and clear queue
    isPlayingAIAudioRef.current = false
    isProcessingQueueRef.current = false
    audioPlaybackQueueRef.current = []
    setStatus('processing')
  }

  const handleRecord = () => {
    if (status === 'idle') {
      startRecording()
    } else if (status === 'recording') {
      stopRecording()
    }
  }

  useEffect(() => {
    let raf: number
    const updateLevel = () => {
      if (analyserRef.current) {
        const array = new Uint8Array(analyserRef.current.fftSize)
        analyserRef.current.getByteTimeDomainData(array)
        let max = 0
        for (let i = 0; i < array.length; i++) {
          const val = Math.abs(array[i] - 128) / 128
          if (val > max) max = val
        }
        setLevel(max)
      }
      raf = requestAnimationFrame(updateLevel)
    }
    if (status === 'recording') {
      raf = requestAnimationFrame(updateLevel)
    } else {
      cancelAnimationFrame(raf)
      setLevel(0)
    }
    return () => cancelAnimationFrame(raf)
  }, [status])

  return (
    <div className={inline ? 'flex items-center' : 'flex flex-col items-center gap-2'}>
      <Button
        data-testid="record-button"
        onClick={handleRecord}
        size={inline ? 'icon' : undefined}
        aria-label={status === 'recording' ? 'Stop recording' : 'Start recording'}
      >
        {status === 'recording'
          ? inline
            ? <Square className="h-4 w-4" />
            : 'Stop'
          : inline
            ? <Mic className="h-4 w-4" />
            : 'Record'}
      </Button>
      {!inline && status === 'recording' && <div>Recording...</div>}
      {!inline && status === 'processing' && <div>Processing...</div>}
      {!inline && permissionError && <div className="text-red-500">{permissionError}</div>}
      {!inline && (
        <div className="h-2 w-32 bg-gray-200" aria-label="voice-level">
          <div
            className="h-2 bg-green-500"
            style={{ width: `${Math.min(level * 100, 100)}%` }}
            data-testid="vad-bar"
          />
        </div>
      )}
      <audio ref={audioRef} data-testid="playback" />
    </div>
  )
}

export default VoiceInterface
